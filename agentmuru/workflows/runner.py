from __future__ import annotations

import asyncio
import inspect
from typing import Any

from agentmuru.core.events import EventType, RuntimeEvent
from agentmuru.sessions import SessionStore

from .models import Checkpoint, Step, StepResult, Workflow, WorkflowResult, WorkflowStatus


class WorkflowRunner:
    def __init__(self, session_store: SessionStore | None = None) -> None:
        self._sessions = session_store

    async def run(
        self,
        workflow: Workflow,
        *,
        initial_state: dict[str, Any],
        session_id: str | None = None,
        run_id: str | None = None,
    ) -> WorkflowResult:
        state = dict(initial_state)
        checkpoints: list[Checkpoint] = []
        index_by_name = {step.name: index for index, step in enumerate(workflow.steps)}
        self._emit(
            EventType.WORKFLOW_STARTED,
            session_id=session_id,
            run_id=run_id,
            payload={"workflow": workflow.name},
        )
        index = 0
        while index < len(workflow.steps):
            step = workflow.steps[index]
            self._emit(
                EventType.WORKFLOW_STEP_STARTED,
                session_id=session_id,
                run_id=run_id,
                payload={"workflow": workflow.name, "step": step.name},
            )
            try:
                result = await self._run_step(step, state)
            except Exception:
                return WorkflowResult(
                    status=WorkflowStatus.FAILED,
                    state=state,
                    checkpoints=tuple(checkpoints),
                    error_code="workflow_step_failed",
                )
            state = dict(result.state)
            checkpoint = Checkpoint(step_name=step.name, state=dict(state))
            checkpoints.append(checkpoint)
            self._emit(
                EventType.WORKFLOW_STEP_COMPLETED,
                session_id=session_id,
                run_id=run_id,
                payload={"workflow": workflow.name, "step": step.name},
            )
            if result.next_step is None:
                index += 1
            else:
                try:
                    index = index_by_name[result.next_step]
                except KeyError as exc:
                    raise ValueError(f"Unknown next workflow step '{result.next_step}'") from exc
        self._emit(
            EventType.WORKFLOW_COMPLETED,
            session_id=session_id,
            run_id=run_id,
            payload={"workflow": workflow.name, "status": WorkflowStatus.COMPLETED.value},
        )
        return WorkflowResult(
            status=WorkflowStatus.COMPLETED,
            state=state,
            checkpoints=tuple(checkpoints),
        )

    async def _run_step(self, step: Step, state: dict[str, Any]) -> StepResult:
        last_error: Exception | None = None
        for _ in range(step.retries + 1):
            try:
                if inspect.iscoroutinefunction(step.handler):
                    value = await step.handler(dict(state))
                else:
                    value = await asyncio.to_thread(step.handler, dict(state))
                if not isinstance(value, StepResult):
                    raise TypeError(f"Workflow step '{step.name}' must return StepResult")
                return value
            except Exception as exc:
                last_error = exc
        assert last_error is not None
        raise last_error

    def _emit(
        self,
        event_type: EventType,
        *,
        session_id: str | None,
        run_id: str | None,
        payload: dict[str, Any],
    ) -> None:
        if self._sessions is None or session_id is None:
            return
        self._sessions.append_event(
            session_id,
            RuntimeEvent.new(
                event_type,
                session_id=session_id,
                run_id=run_id,
                payload=payload,
            ),
        )
