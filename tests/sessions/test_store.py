import asyncio

import pytest

from agentmuru.core.events import EventType, RuntimeEvent
from agentmuru.sessions.store import InMemorySessionStore


def test_store_assigns_monotonic_sequences_and_isolates_sessions() -> None:
    store = InMemorySessionStore()
    first_session = store.create()
    second_session = store.create()

    first = store.append_event(
        first_session.id,
        RuntimeEvent.new(EventType.SESSION_STARTED, session_id=first_session.id),
    )
    second = store.append_event(
        first_session.id,
        RuntimeEvent.new(EventType.USER_MESSAGE_RECEIVED, session_id=first_session.id),
    )
    other = store.append_event(
        second_session.id,
        RuntimeEvent.new(EventType.SESSION_STARTED, session_id=second_session.id),
    )

    assert [first.sequence, second.sequence, other.sequence] == [1, 2, 1]
    assert [event.id for event in store.events(first_session.id, after_sequence=1)] == [second.id]
    assert store.get(second_session.id).events == [other]


def test_store_rejects_event_for_another_session() -> None:
    store = InMemorySessionStore()
    session = store.create()

    with pytest.raises(ValueError, match="session_id"):
        store.append_event(
            session.id,
            RuntimeEvent.new(EventType.SESSION_STARTED, session_id="different"),
        )


@pytest.mark.asyncio
async def test_store_subscription_replays_then_follows_live_events() -> None:
    store = InMemorySessionStore()
    session = store.create()
    first = store.append_event(
        session.id,
        RuntimeEvent.new(EventType.SESSION_STARTED, session_id=session.id),
    )
    stream = store.subscribe(session.id)

    assert await anext(stream) == first

    second = store.append_event(
        session.id,
        RuntimeEvent.new(EventType.USER_MESSAGE_RECEIVED, session_id=session.id),
    )
    assert await asyncio.wait_for(anext(stream), timeout=0.2) == second
    await stream.aclose()
