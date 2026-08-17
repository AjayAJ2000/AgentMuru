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
from agentmuru.sessions import (
    AssistantToolCall,
    Message,
    MessageRole,
    RunRecord,
    RunStatus,
    Session,
)
from agentmuru.tools import PermissionDecision, PermissionPolicy

from .application import Application
from .events import EventType, RuntimeEvent


class PermissionDeniedError(AgentMuruError):
    code = "permission_denied"


class ModelExecutionError(AgentMuruError):
    code = "model_failed"

    def __init__(self, code: str = "model_failed") -> None:
        self.code = code
        super().__init__("Model execution failed")


class ToolRuntimeError(AgentMuruError):
    code = "tool_failed"


class ApprovalExpiredError(AgentMuruError):
    code = "approval_expired"


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
        approval_timeout: float | None = 300.0,
    ) -> None:
        if approval_timeout is not None and approval_timeout <= 0:
            raise ValueError("approval_timeout must be positive or None")
        self.application = application
        self.sessions = application.session_store
        self.artifacts = application.artifact_store
        self.policy = policy or PermissionPolicy()
        self.approvals = approvals or ApprovalService()
        self.tracer = tracer or Tracer()
        self.max_model_turns = max_model_turns
        self.approval_timeout = approval_timeout
        self._tasks: dict[str, asyncio.Task[RunRecord]] = {}
        for recovered in self.sessions.recover_interrupted_runs():
            self._emit(
                EventType.RUN_FAILED,
                session_id=recovered.session_id,
                run_id=recovered.id,
                payload={
                    "code": "process_interrupted",
                    "status": recovered.status.value,
                },
            )

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
            existing = self.sessions.get_idempotent_run(session_id, idempotency_key)
            if existing is not None:
                return existing
        self.sessions.get(session_id)
        message = Message(role=MessageRole.USER, content=content)
        self.sessions.append_message(session_id, message)
        self._emit(
            EventType.USER_MESSAGE_RECEIVED,
            session_id=session_id,
            payload={"message_id": message.id, "content": content},
        )
        run = RunRecord(session_id=session_id, agent_name=self.application.agent.name)
        self.sessions.create_run(run)
        if idempotency_key is not None:
            self.sessions.bind_idempotency_key(session_id, idempotency_key, run.id)
        self._tasks[run.id] = asyncio.create_task(self._execute(run))
        return run

    async def wait(self, run_id: str) -> RunRecord:
        task = self._tasks.get(run_id)
        if task is None:
            run = self.sessions.get_run(run_id)
            if run.status in {RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED}:
                return run
            raise RunNotFoundError(f"Run '{run_id}' has no active process")
        return await asyncio.shield(task)

    def get_run(self, run_id: str) -> RunRecord:
        return self.sessions.get_run(run_id)

    async def cancel(self, run_id: str) -> RunRecord:
        task = self._tasks.get(run_id)
        if task is None:
            run = self.sessions.get_run(run_id)
            if run.status in {RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED}:
                return run
            raise RunNotFoundError(f"Run '{run_id}' has no active process")
        if not task.done():
            task.cancel()
        return await task

    async def handoff(
        self,
        from_run_id: str,
        *,
        to_agent: str,
        reason: str,
    ) -> RunRecord:
        source = self.sessions.get_run(from_run_id)
        target = self.application.get_agent(to_agent)
        session = self.sessions.get(source.session_id)
        target_run = RunRecord(session_id=session.id, agent_name=target.name)
        self.sessions.create_run(target_run)
        self._emit(
            EventType.AGENT_HANDOFF,
            session_id=session.id,
            run_id=source.id,
            payload={
                "from_agent": source.agent_name,
                "to_agent": target.name,
                "reason": reason,
                "target_run_id": target_run.id,
            },
        )
        self._tasks[target_run.id] = asyncio.create_task(self._execute(target_run))
        return target_run

    async def wait_for_approval(self, run_id: str) -> ApprovalRequest:
        self.sessions.get_run(run_id)
        approval_waiter = asyncio.create_task(self.approvals.wait_for_run(run_id))
        try:
            run_task = self._tasks[run_id]
        except KeyError as exc:
            approval_waiter.cancel()
            raise RunNotFoundError(f"Run '{run_id}' has no active process") from exc
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
        agent = self.application.get_agent(run.agent_name)
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
        self.sessions.update_run(run)
        self._emit(
            EventType.AGENT_STARTED,
            session_id=session.id,
            run_id=run.id,
            trace_id=trace.id,
            payload={"agent": agent.name},
        )
        try:
            for turn in range(self.max_model_turns):
                assistant_text: list[str] = []
                collected_calls: list[ToolCall] = []
                model_span = self.tracer.start_span(
                    trace.id, name="model", kind="model", attributes={"turn": turn + 1}
                )
                self._emit(
                    EventType.TRACE_SPAN_STARTED,
                    session_id=session.id,
                    run_id=run.id,
                    trace_id=trace.id,
                    parent_id=model_span.parent_id,
                    payload={
                        "span_id": model_span.id,
                        "name": model_span.name,
                        "kind": model_span.kind,
                    },
                )
                self._emit(
                    EventType.MODEL_REQUEST_STARTED,
                    session_id=session.id,
                    run_id=run.id,
                    trace_id=trace.id,
                    parent_id=model_span.id,
                    payload={
                        "provider": agent.model.name,
                        "model_id": getattr(agent.model, "model_id", agent.model.name),
                        "turn": turn + 1,
                    },
                )
                request = ModelRequest(
                    messages=tuple(self.sessions.get(session.id).messages),
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
                        collected_calls.append(event)
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
                        raise ModelExecutionError(event.code)
                completed_model_span = self.tracer.finish_span(model_span.id)
                self._emit(
                    EventType.TRACE_SPAN_COMPLETED,
                    session_id=session.id,
                    run_id=run.id,
                    trace_id=trace.id,
                    parent_id=completed_model_span.parent_id,
                    payload={
                        "span_id": completed_model_span.id,
                        "status": completed_model_span.status,
                        "duration_ms": completed_model_span.duration_ms,
                    },
                )
                self._emit(
                    EventType.MODEL_REQUEST_COMPLETED,
                    session_id=session.id,
                    run_id=run.id,
                    trace_id=trace.id,
                    parent_id=model_span.id,
                    payload={
                        "provider": agent.model.name,
                        "model_id": getattr(agent.model, "model_id", agent.model.name),
                        "turn": turn + 1,
                    },
                )
                normalized_calls: list[AssistantToolCall] = []
                for call in collected_calls:
                    try:
                        resolved_tool = agent.tool(call.name)
                    except KeyError as exc:
                        self._tool_failure(run, trace.id, call, "tool_not_found", str(exc))
                        raise AgentMuruError(str(exc)) from exc
                    normalized_calls.append(
                        AssistantToolCall(
                            id=call.id,
                            name=resolved_tool.name,
                            arguments=resolved_tool.redact_arguments(call.arguments),
                        )
                    )
                if assistant_text or normalized_calls:
                    message = Message(
                        role=MessageRole.ASSISTANT,
                        content="".join(assistant_text),
                        tool_calls=tuple(normalized_calls),
                    )
                    self.sessions.append_message(session.id, message)
                    if assistant_text:
                        self._emit(
                            EventType.ASSISTANT_MESSAGE_COMPLETED,
                            session_id=session.id,
                            run_id=run.id,
                            trace_id=trace.id,
                            payload={"message_id": message.id, "content": message.content},
                        )
                for call in collected_calls:
                    await self._handle_tool_call(
                        run=run,
                        trace_id=trace.id,
                        parent_span_id=model_span.id,
                        call=call,
                    )
                if not collected_calls:
                    break
            else:
                raise ModelExecutionError("Agent exceeded the maximum number of model turns")

            run.status = RunStatus.COMPLETED
            run.completed_at = datetime.now(timezone.utc)
            self.sessions.update_run(run)
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
            self.sessions.update_run(run)
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
            self.sessions.update_run(run)
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
        self.sessions.get(run.session_id)
        agent = self.application.get_agent(run.agent_name)
        try:
            tool = agent.tool(call.name)
        except KeyError as exc:
            self._tool_failure(run, trace_id, call, "tool_not_found", str(exc))
            raise AgentMuruError(str(exc)) from exc

        redacted = tool.redact_arguments(call.arguments)
        self._emit(
            EventType.TOOL_CALL_REQUESTED,
            session_id=run.session_id,
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
                session_id=run.session_id,
                run_id=run.id,
                tool_call_id=call.id,
                tool_name=tool.name,
                arguments=redacted,
                permission=tool.permission,
                risk=tool.risk.value,
                timeout=self.approval_timeout,
            )
            run.status = RunStatus.WAITING_APPROVAL
            self.sessions.update_run(run)
            self._emit(
                EventType.APPROVAL_REQUESTED,
                session_id=run.session_id,
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
                    "expires_at": approval.expires_at.isoformat() if approval.expires_at else None,
                },
            )
            approval = await self.approvals.wait(approval.id)
            run.status = RunStatus.RUNNING
            self.sessions.update_run(run)
            if approval.status is ApprovalStatus.EXPIRED:
                self._emit(
                    EventType.APPROVAL_EXPIRED,
                    session_id=run.session_id,
                    run_id=run.id,
                    trace_id=trace_id,
                    parent_id=parent_span_id,
                    payload={"approval_id": approval.id, "tool_name": tool.name},
                )
                raise ApprovalExpiredError(f"Approval for tool '{tool.name}' expired")
            if approval.status is ApprovalStatus.REJECTED:
                self.sessions.append_message(
                    run.session_id,
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
            EventType.TRACE_SPAN_STARTED,
            session_id=run.session_id,
            run_id=run.id,
            trace_id=trace_id,
            parent_id=tool_span.parent_id,
            payload={"span_id": tool_span.id, "name": tool_span.name, "kind": tool_span.kind},
        )
        self._emit(
            EventType.TOOL_CALL_STARTED,
            session_id=run.session_id,
            run_id=run.id,
            trace_id=trace_id,
            parent_id=tool_span.id,
            payload={"tool_call_id": call.id, "tool_name": tool.name, "arguments": redacted},
        )
        try:
            result = await tool.invoke(call.arguments)
        except Exception as exc:
            failed_span = self.tracer.finish_span(tool_span.id, status="failed")
            self._emit(
                EventType.TRACE_SPAN_COMPLETED,
                session_id=run.session_id,
                run_id=run.id,
                trace_id=trace_id,
                parent_id=failed_span.parent_id,
                payload={
                    "span_id": failed_span.id,
                    "status": failed_span.status,
                    "duration_ms": failed_span.duration_ms,
                },
            )
            self._tool_failure(run, trace_id, call, ToolRuntimeError.code, "Tool execution failed")
            raise ToolRuntimeError("Tool execution failed") from exc
        completed_tool_span = self.tracer.finish_span(tool_span.id)
        self._emit(
            EventType.TRACE_SPAN_COMPLETED,
            session_id=run.session_id,
            run_id=run.id,
            trace_id=trace_id,
            parent_id=completed_tool_span.parent_id,
            payload={
                "span_id": completed_tool_span.id,
                "status": completed_tool_span.status,
                "duration_ms": completed_tool_span.duration_ms,
            },
        )
        public_result = _public_value(result)
        self.sessions.append_message(
            run.session_id,
            Message(
                role=MessageRole.TOOL,
                name=tool.name,
                tool_call_id=call.id,
                content=json.dumps(public_result),
            )
        )
        self._emit(
            EventType.TOOL_CALL_COMPLETED,
            session_id=run.session_id,
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
