from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Mapping
from datetime import datetime, timezone
from typing import Any

from agentmuru.approvals import (
    ApprovalDecision,
    ApprovalRequest,
    ApprovalService,
    ApprovalStatus,
)
from agentmuru.artifacts import Artifact, ArtifactKind
from agentmuru.core.context import RunContext, _current_run
from agentmuru.core.errors import AgentMuruError, RunNotFoundError
from agentmuru.models import ModelCompleted, ModelFailed, ModelRequest, TextDelta, ToolCall
from agentmuru.observability import Tracer
from agentmuru.sessions import Message, MessageRole, RunRecord, RunStatus, Session
from agentmuru.tools import PermissionDecision, PermissionPolicy

from .application import Application
from .events import EventType, RuntimeEvent


class PermissionDeniedError(AgentMuruError):
    code = "permission_denied"


class ModelExecutionError(AgentMuruError):
    code = "model_failed"


class ToolRuntimeError(AgentMuruError):
    code = "tool_failed"


def _public_value(value: Any) -> Any:
    try:
        return json.loads(json.dumps(value, allow_nan=False))
    except (TypeError, ValueError):
        return str(value)


class Runtime:
    def __init__(
        self,
        application: Application,
        *,
        policy: PermissionPolicy | None = None,
        approvals: ApprovalService | None = None,
        tracer: Tracer | None = None,
        max_model_turns: int = 24,
    ) -> None:
        self.application = application
        self.sessions = application.session_store
        self.artifacts = application.artifact_store
        self.policy = policy or PermissionPolicy()
        self.approvals = approvals or ApprovalService()
        self.tracer = tracer or Tracer()
        self.max_model_turns = max_model_turns
        self._runs: dict[str, RunRecord] = {}
        self._tasks: dict[str, asyncio.Task[RunRecord]] = {}
        self._idempotency: dict[tuple[str, str], str] = {}

    def create_session(self, *, user_id: str | None = None, title: str | None = None) -> Session:
        session = self.sessions.create(user_id=user_id, title=title)
        self._emit(EventType.SESSION_STARTED, session_id=session.id, payload={"title": title})
        return session

    async def submit(
        self,
        session_id: str,
        content: str,
        *,
        idempotency_key: str | None = None,
    ) -> RunRecord:
        if not content.strip():
            raise ValueError("Message content cannot be empty")
        if idempotency_key is not None:
            existing = self._idempotency.get((session_id, idempotency_key))
            if existing is not None:
                return self._runs[existing]
        session = self.sessions.get(session_id)
        message = Message(role=MessageRole.USER, content=content)
        session.messages.append(message)
        self._emit(
            EventType.USER_MESSAGE_RECEIVED,
            session_id=session_id,
            payload={"message_id": message.id, "content": content},
        )
        run = RunRecord(session_id=session_id, agent_name=self.application.agent.name)
        session.runs.append(run)
        self._runs[run.id] = run
        if idempotency_key is not None:
            self._idempotency[(session_id, idempotency_key)] = run.id
        self._tasks[run.id] = asyncio.create_task(self._execute(run))
        return run

    async def wait(self, run_id: str) -> RunRecord:
        try:
            task = self._tasks[run_id]
        except KeyError as exc:
            raise RunNotFoundError(f"Run '{run_id}' was not found") from exc
        return await asyncio.shield(task)

    async def cancel(self, run_id: str) -> RunRecord:
        try:
            task = self._tasks[run_id]
        except KeyError as exc:
            raise RunNotFoundError(f"Run '{run_id}' was not found") from exc
        if not task.done():
            task.cancel()
        return await task

    async def wait_for_approval(self, run_id: str) -> ApprovalRequest:
        if run_id not in self._runs:
            raise RunNotFoundError(f"Run '{run_id}' was not found")
        approval_waiter = asyncio.create_task(self.approvals.wait_for_run(run_id))
        run_task = self._tasks[run_id]
        done, _ = await asyncio.wait(
            {approval_waiter, run_task}, return_when=asyncio.FIRST_COMPLETED
        )
        if approval_waiter in done:
            return approval_waiter.result()
        approval_waiter.cancel()
        raise RuntimeError("Run completed without requesting approval")

    async def decide_approval(
        self,
        approval_id: str,
        decision: ApprovalDecision,
        *,
        actor: str,
        reason: str | None = None,
    ) -> ApprovalRequest:
        decided = await self.approvals.decide(
            approval_id, decision, actor=actor, reason=reason
        )
        event_type = (
            EventType.APPROVAL_GRANTED
            if decided.status is ApprovalStatus.APPROVED
            else EventType.APPROVAL_REJECTED
        )
        self._emit(
            event_type,
            session_id=decided.session_id,
            run_id=decided.run_id,
            payload={
                "approval_id": decided.id,
                "actor": actor,
                "reason": reason,
                "tool_name": decided.tool_name,
            },
        )
        return decided

    def create_artifact(
        self,
        *,
        session_id: str,
        run_id: str | None,
        kind: ArtifactKind,
        name: str,
        content: Any,
        mime_type: str,
        creator: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> Artifact:
        self.sessions.get(session_id)
        artifact = self.artifacts.create(
            session_id=session_id,
            run_id=run_id,
            kind=kind,
            name=name,
            content=content,
            mime_type=mime_type,
            creator=creator,
            metadata=metadata,
        )
        self._emit(
            EventType.ARTIFACT_CREATED,
            session_id=session_id,
            run_id=run_id,
            payload={
                "artifact_id": artifact.id,
                "kind": artifact.kind.value,
                "name": artifact.name,
                "mime_type": artifact.mime_type,
                "creator": artifact.creator,
            },
        )
        return artifact

    def events(
        self, session_id: str, *, after_sequence: int = 0
    ) -> AsyncIterator[RuntimeEvent]:
        subscribe = getattr(self.sessions, "subscribe", None)
        if subscribe is None:
            raise RuntimeError("Configured session store does not support event subscriptions")
        return subscribe(session_id, after_sequence=after_sequence)

    def _emit(
        self,
        event_type: EventType,
        *,
        session_id: str,
        run_id: str | None = None,
        trace_id: str | None = None,
        parent_id: str | None = None,
        payload: Mapping[str, Any] | None = None,
    ) -> RuntimeEvent:
        return self.sessions.append_event(
            session_id,
            RuntimeEvent.new(
                event_type,
                session_id=session_id,
                run_id=run_id,
                trace_id=trace_id,
                parent_id=parent_id,
                payload={key: _public_value(value) for key, value in (payload or {}).items()},
            ),
        )

    async def _execute(self, run: RunRecord) -> RunRecord:
        session = self.sessions.get(run.session_id)
        agent = self.application.agent
        trace = self.tracer.start_trace(
            session_id=session.id, run_id=run.id, name=f"agent:{agent.name}"
        )
        token = _current_run.set(
            RunContext(
                session_id=session.id,
                run_id=run.id,
                trace_id=trace.id,
                agent_name=agent.name,
            )
        )
        run.status = RunStatus.RUNNING
        self._emit(
            EventType.AGENT_STARTED,
            session_id=session.id,
            run_id=run.id,
            trace_id=trace.id,
            payload={"agent": agent.name},
        )
        try:
            for turn in range(self.max_model_turns):
                used_tool = False
                assistant_text: list[str] = []
                model_span = self.tracer.start_span(
                    trace.id, name="model", kind="model", attributes={"turn": turn + 1}
                )
                self._emit(
                    EventType.MODEL_REQUEST_STARTED,
                    session_id=session.id,
                    run_id=run.id,
                    trace_id=trace.id,
                    parent_id=model_span.id,
                    payload={"provider": agent.model.name, "turn": turn + 1},
                )
                request = ModelRequest(
                    messages=tuple(session.messages),
                    instructions=agent.instructions,
                    tools=tuple(item.provider_schema() for item in agent.tools),
                    settings=agent.model_settings,
                )
                async for event in agent.model.stream(request):
                    if isinstance(event, TextDelta):
                        assistant_text.append(event.text)
                        self._emit(
                            EventType.MODEL_TOKEN_DELTA,
                            session_id=session.id,
                            run_id=run.id,
                            trace_id=trace.id,
                            parent_id=model_span.id,
                            payload={"delta": event.text},
                        )
                    elif isinstance(event, ToolCall):
                        used_tool = True
                        await self._handle_tool_call(
                            run=run,
                            trace_id=trace.id,
                            parent_span_id=model_span.id,
                            call=event,
                        )
                    elif isinstance(event, ModelCompleted):
                        self.tracer.record_usage(trace.id, event.usage)
                        self._emit(
                            EventType.USAGE_RECORDED,
                            session_id=session.id,
                            run_id=run.id,
                            trace_id=trace.id,
                            payload={
                                "input_tokens": event.usage.input_tokens,
                                "output_tokens": event.usage.output_tokens,
                                "total_tokens": event.usage.total_tokens,
                                "cost": event.usage.cost,
                            },
                        )
                    elif isinstance(event, ModelFailed):
                        raise ModelExecutionError("Model execution failed")
                self.tracer.finish_span(model_span.id)
                self._emit(
                    EventType.MODEL_REQUEST_COMPLETED,
                    session_id=session.id,
                    run_id=run.id,
                    trace_id=trace.id,
                    parent_id=model_span.id,
                    payload={"provider": agent.model.name, "turn": turn + 1},
                )
                if assistant_text:
                    message = Message(role=MessageRole.ASSISTANT, content="".join(assistant_text))
                    session.messages.append(message)
                    self._emit(
                        EventType.ASSISTANT_MESSAGE_COMPLETED,
                        session_id=session.id,
                        run_id=run.id,
                        trace_id=trace.id,
                        payload={"message_id": message.id, "content": message.content},
                    )
                if not used_tool:
                    break
            else:
                raise ModelExecutionError("Agent exceeded the maximum number of model turns")

            run.status = RunStatus.COMPLETED
            run.completed_at = datetime.now(timezone.utc)
            self.tracer.finish_trace(trace.id)
            self._emit(
                EventType.AGENT_COMPLETED,
                session_id=session.id,
                run_id=run.id,
                trace_id=trace.id,
                payload={"agent": agent.name},
            )
            self._emit(
                EventType.RUN_COMPLETED,
                session_id=session.id,
                run_id=run.id,
                trace_id=trace.id,
                payload={"status": run.status.value},
            )
        except asyncio.CancelledError:
            run.status = RunStatus.CANCELLED
            run.completed_at = datetime.now(timezone.utc)
            self.tracer.finish_trace(trace.id, status="cancelled")
            self._emit(
                EventType.RUN_CANCELLED,
                session_id=session.id,
                run_id=run.id,
                trace_id=trace.id,
                payload={"status": run.status.value},
            )
        except Exception as exc:
            run.status = RunStatus.FAILED
            run.completed_at = datetime.now(timezone.utc)
            run.error_code = exc.code if isinstance(exc, AgentMuruError) else "runtime_error"
            self.tracer.finish_trace(trace.id, status="failed")
            self._emit(
                EventType.AGENT_FAILED,
                session_id=session.id,
                run_id=run.id,
                trace_id=trace.id,
                payload={"code": run.error_code, "message": str(exc)},
            )
            self._emit(
                EventType.RUN_FAILED,
                session_id=session.id,
                run_id=run.id,
                trace_id=trace.id,
                payload={"code": run.error_code, "status": run.status.value},
            )
        finally:
            _current_run.reset(token)
        return run

    async def _handle_tool_call(
        self,
        *,
        run: RunRecord,
        trace_id: str,
        parent_span_id: str,
        call: ToolCall,
    ) -> None:
        session = self.sessions.get(run.session_id)
        agent = self.application.agent
        try:
            tool = agent.tool(call.name)
        except KeyError as exc:
            self._tool_failure(run, trace_id, call, "tool_not_found", str(exc))
            raise AgentMuruError(str(exc)) from exc

        redacted = tool.redact_arguments(call.arguments)
        self._emit(
            EventType.TOOL_CALL_REQUESTED,
            session_id=session.id,
            run_id=run.id,
            trace_id=trace_id,
            parent_id=parent_span_id,
            payload={"tool_call_id": call.id, "tool_name": tool.name, "arguments": redacted},
        )
        decision = self.policy.evaluate(tool, granted_permissions=agent.permissions)
        if decision is PermissionDecision.DENY:
            message = f"Permission '{tool.permission}' is not granted"
            self._tool_failure(run, trace_id, call, PermissionDeniedError.code, message)
            raise PermissionDeniedError(message)
        if decision is PermissionDecision.REQUIRE_APPROVAL:
            approval = await self.approvals.create(
                session_id=session.id,
                run_id=run.id,
                tool_call_id=call.id,
                tool_name=tool.name,
                arguments=redacted,
                permission=tool.permission,
                risk=tool.risk.value,
            )
            run.status = RunStatus.WAITING_APPROVAL
            self._emit(
                EventType.APPROVAL_REQUESTED,
                session_id=session.id,
                run_id=run.id,
                trace_id=trace_id,
                parent_id=parent_span_id,
                payload={
                    "approval_id": approval.id,
                    "tool_call_id": call.id,
                    "tool_name": tool.name,
                    "arguments": redacted,
                    "permission": tool.permission,
                    "risk": tool.risk.value,
                },
            )
            approval = await self.approvals.wait(approval.id)
            run.status = RunStatus.RUNNING
            if approval.status is ApprovalStatus.REJECTED:
                session.messages.append(
                    Message(
                        role=MessageRole.TOOL,
                        name=tool.name,
                        tool_call_id=call.id,
                        content=json.dumps({"status": "rejected", "reason": approval.reason}),
                    )
                )
                return

        tool_span = self.tracer.start_span(
            trace_id,
            name=f"tool:{tool.name}",
            kind="tool",
            parent_id=parent_span_id,
            attributes={"tool": tool.name},
        )
        self._emit(
            EventType.TOOL_CALL_STARTED,
            session_id=session.id,
            run_id=run.id,
            trace_id=trace_id,
            parent_id=tool_span.id,
            payload={"tool_call_id": call.id, "tool_name": tool.name, "arguments": redacted},
        )
        try:
            result = await tool.invoke(call.arguments)
        except Exception as exc:
            self.tracer.finish_span(tool_span.id, status="failed")
            self._tool_failure(run, trace_id, call, ToolRuntimeError.code, "Tool execution failed")
            raise ToolRuntimeError("Tool execution failed") from exc
        self.tracer.finish_span(tool_span.id)
        public_result = _public_value(result)
        session.messages.append(
            Message(
                role=MessageRole.TOOL,
                name=tool.name,
                tool_call_id=call.id,
                content=json.dumps(public_result),
            )
        )
        self._emit(
            EventType.TOOL_CALL_COMPLETED,
            session_id=session.id,
            run_id=run.id,
            trace_id=trace_id,
            parent_id=tool_span.id,
            payload={"tool_call_id": call.id, "tool_name": tool.name, "result": public_result},
        )

    def _tool_failure(
        self,
        run: RunRecord,
        trace_id: str,
        call: ToolCall,
        code: str,
        message: str,
    ) -> None:
        self._emit(
            EventType.TOOL_CALL_FAILED,
            session_id=run.session_id,
            run_id=run.id,
            trace_id=trace_id,
            payload={
                "tool_call_id": call.id,
                "tool_name": call.name,
                "code": code,
                "message": message,
            },
        )
