from datetime import timezone

from agentmuru.core.events import EventType, RuntimeEvent


def test_runtime_event_round_trips_through_public_dict() -> None:
    event = RuntimeEvent.new(
        EventType.USER_MESSAGE_RECEIVED,
        session_id="session-1",
        run_id="run-1",
        trace_id="trace-1",
        payload={"content": "hello", "nested": {"visible": True}},
    ).with_sequence(7)

    restored = RuntimeEvent.from_dict(event.to_dict())

    assert restored == event
    assert restored.timestamp.tzinfo is timezone.utc
    assert restored.to_dict()["type"] == "user.message.received"


def test_runtime_event_rejects_non_json_payloads() -> None:
    try:
        RuntimeEvent.new(
            EventType.SESSION_STARTED,
            session_id="session-1",
            payload={"bad": object()},
        )
    except TypeError as exc:
        assert "JSON-serializable" in str(exc)
    else:
        raise AssertionError("non-JSON event payload was accepted")
