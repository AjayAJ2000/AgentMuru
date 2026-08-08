from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

from agentmuru.models import Usage


@dataclass(slots=True)
class Span:
    trace_id: str
    name: str
    kind: str
    id: str = field(default_factory=lambda: str(uuid4()))
    parent_id: str | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: datetime | None = None
    status: str = "running"
    attributes: Mapping[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float | None:
        if self.ended_at is None:
            return None
        return (self.ended_at - self.started_at).total_seconds() * 1000


@dataclass(slots=True)
class Trace:
    session_id: str
    run_id: str
    name: str
    id: str = field(default_factory=lambda: str(uuid4()))
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: datetime | None = None
    status: str = "running"
    spans: list[Span] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)
