from __future__ import annotations

from datetime import datetime, timezone
from threading import RLock
from typing import Any, Mapping

from agentmuru.models import Usage

from .models import Span, Trace


class Tracer:
    def __init__(self) -> None:
        self._traces: dict[str, Trace] = {}
        self._spans: dict[str, Span] = {}
        self._lock = RLock()

    def start_trace(self, *, session_id: str, run_id: str, name: str) -> Trace:
        trace = Trace(session_id=session_id, run_id=run_id, name=name)
        with self._lock:
            self._traces[trace.id] = trace
        return trace

    def start_span(
        self,
        trace_id: str,
        *,
        name: str,
        kind: str,
        parent_id: str | None = None,
        attributes: Mapping[str, Any] | None = None,
    ) -> Span:
        with self._lock:
            trace = self._traces[trace_id]
            span = Span(
                trace_id=trace_id,
                name=name,
                kind=kind,
                parent_id=parent_id,
                attributes=attributes or {},
            )
            trace.spans.append(span)
            self._spans[span.id] = span
        return span

    def finish_span(self, span_id: str, *, status: str = "completed") -> Span:
        with self._lock:
            span = self._spans[span_id]
            span.ended_at = datetime.now(timezone.utc)
            span.status = status
            return span

    def record_usage(self, trace_id: str, usage: Usage) -> None:
        with self._lock:
            trace = self._traces[trace_id]
            current = trace.usage
            trace.usage = Usage(
                input_tokens=current.input_tokens + usage.input_tokens,
                output_tokens=current.output_tokens + usage.output_tokens,
                cost=(current.cost or 0.0) + (usage.cost or 0.0)
                if current.cost is not None or usage.cost is not None
                else None,
            )

    def finish_trace(self, trace_id: str, *, status: str = "completed") -> Trace:
        with self._lock:
            trace = self._traces[trace_id]
            trace.ended_at = datetime.now(timezone.utc)
            trace.status = status
            return trace

    def traces_for_run(self, run_id: str) -> list[Trace]:
        with self._lock:
            return [trace for trace in self._traces.values() if trace.run_id == run_id]

    def get(self, trace_id: str) -> Trace:
        with self._lock:
            return self._traces[trace_id]
