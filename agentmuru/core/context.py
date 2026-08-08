from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RunContext:
    session_id: str
    run_id: str
    trace_id: str
    agent_name: str


_current_run: ContextVar[RunContext | None] = ContextVar("agentmuru_current_run", default=None)


def current_run_context() -> RunContext:
    context = _current_run.get()
    if context is None:
        raise RuntimeError("No AgentMuru run is active in this context")
    return context
