from __future__ import annotations

from typing import Any

from agentmuru.core.events import RuntimeEvent

PROTOCOL_VERSION = 1


def event_envelope(event: RuntimeEvent) -> dict[str, Any]:
    return {
        "protocol_version": PROTOCOL_VERSION,
        "kind": "event",
        "data": event.to_dict(),
    }


def control_envelope(kind: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"protocol_version": PROTOCOL_VERSION, "kind": kind, "data": data or {}}
