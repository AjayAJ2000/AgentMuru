from __future__ import annotations

import json
from pathlib import Path

from agentmuru.core.events import RuntimeEvent


ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "schemas"
EVENT_FIXTURE = SCHEMAS / "testdata" / "events" / "session-started.json"
HARDWARE_FIXTURE = SCHEMAS / "testdata" / "hardware" / "pentium-8gb.json"


def test_edge_event_fixture_round_trips() -> None:
    value = json.loads(EVENT_FIXTURE.read_text(encoding="utf-8"))

    event = RuntimeEvent.from_dict(value)

    assert event.to_dict() == value


def test_hardware_fixture_has_explicit_support_reasons() -> None:
    value = json.loads(HARDWARE_FIXTURE.read_text(encoding="utf-8"))

    assert value["schema_version"] == "hardware.agentmuru.dev/v1"
    assert value["memory"]["total_bytes"] == 8 * 1024**3
    assert isinstance(value["support"]["reasons"], list)
    assert value["support"]["level"] == "experimental"


def test_contract_schemas_are_strict_at_the_root() -> None:
    paths = (
        SCHEMAS / "hardware" / "v1" / "profile.schema.json",
        SCHEMAS / "events" / "v1" / "event.schema.json",
        SCHEMAS / "agent-pack" / "v1" / "manifest.schema.json",
    )

    for path in paths:
        schema = json.loads(path.read_text(encoding="utf-8"))
        assert schema["additionalProperties"] is False, path
        assert schema["type"] == "object", path
