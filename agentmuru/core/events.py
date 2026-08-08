from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping
from uuid import uuid4

JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]


class EventType(str, Enum):
    SESSION_STARTED = "session.started"
    SESSION_COMPLETED = "session.completed"
    USER_MESSAGE_RECEIVED = "user.message.received"
    ASSISTANT_MESSAGE_STARTED = "assistant.message.started"
    ASSISTANT_MESSAGE_DELTA = "assistant.message.delta"
    ASSISTANT_MESSAGE_COMPLETED = "assistant.message.completed"
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"
    AGENT_HANDOFF = "agent.handoff"
    MODEL_REQUEST_STARTED = "model.request.started"
    MODEL_TOKEN_DELTA = "model.token.delta"
    MODEL_REQUEST_COMPLETED = "model.request.completed"
    TOOL_CALL_REQUESTED = "tool.call.requested"
    TOOL_CALL_STARTED = "tool.call.started"
    TOOL_CALL_COMPLETED = "tool.call.completed"
    TOOL_CALL_FAILED = "tool.call.failed"
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_GRANTED = "approval.granted"
    APPROVAL_REJECTED = "approval.rejected"
    APPROVAL_EXPIRED = "approval.expired"
    ARTIFACT_CREATED = "artifact.created"
    ARTIFACT_UPDATED = "artifact.updated"
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_STEP_STARTED = "workflow.step.started"
    WORKFLOW_STEP_COMPLETED = "workflow.step.completed"
    WORKFLOW_COMPLETED = "workflow.completed"
    RUN_CANCELLED = "run.cancelled"
    RUN_COMPLETED = "run.completed"
    RUN_FAILED = "run.failed"
    TRACE_SPAN_STARTED = "trace.span.started"
    TRACE_SPAN_COMPLETED = "trace.span.completed"
    USAGE_RECORDED = "usage.recorded"


def _validate_payload(payload: Mapping[str, Any]) -> dict[str, JsonValue]:
    plain = dict(payload)
    try:
        encoded = json.dumps(plain, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise TypeError("Runtime event payloads must be JSON-serializable") from exc
    return json.loads(encoded)


@dataclass(frozen=True, slots=True)
class RuntimeEvent:
    id: str
    type: EventType
    timestamp: datetime
    session_id: str
    sequence: int = 0
    run_id: str | None = None
    trace_id: str | None = None
    parent_id: str | None = None
    payload: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None:
            raise ValueError("Runtime event timestamps must be timezone-aware")
        object.__setattr__(self, "timestamp", self.timestamp.astimezone(timezone.utc))
        object.__setattr__(self, "payload", MappingProxyType(_validate_payload(self.payload)))

    @classmethod
    def new(
        cls,
        event_type: EventType,
        *,
        session_id: str,
        run_id: str | None = None,
        trace_id: str | None = None,
        parent_id: str | None = None,
        payload: Mapping[str, Any] | None = None,
    ) -> "RuntimeEvent":
        return cls(
            id=str(uuid4()),
            type=event_type,
            timestamp=datetime.now(timezone.utc),
            session_id=session_id,
            run_id=run_id,
            trace_id=trace_id,
            parent_id=parent_id,
            payload=payload or {},
        )

    def with_sequence(self, sequence: int) -> "RuntimeEvent":
        if sequence < 1:
            raise ValueError("Event sequence must be positive")
        return replace(self, sequence=sequence)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat().replace("+00:00", "Z"),
            "session_id": self.session_id,
            "sequence": self.sequence,
            "run_id": self.run_id,
            "trace_id": self.trace_id,
            "parent_id": self.parent_id,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RuntimeEvent":
        timestamp = datetime.fromisoformat(str(value["timestamp"]).replace("Z", "+00:00"))
        return cls(
            id=str(value["id"]),
            type=EventType(str(value["type"])),
            timestamp=timestamp,
            session_id=str(value["session_id"]),
            sequence=int(value.get("sequence", 0)),
            run_id=str(value["run_id"]) if value.get("run_id") is not None else None,
            trace_id=str(value["trace_id"]) if value.get("trace_id") is not None else None,
            parent_id=str(value["parent_id"]) if value.get("parent_id") is not None else None,
            payload=value.get("payload") or {},
        )
