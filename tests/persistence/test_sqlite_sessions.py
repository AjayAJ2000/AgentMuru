from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from agentmuru.core.events import EventType, RuntimeEvent
from agentmuru.persistence.database import SQLiteDatabase
from agentmuru.persistence.session_store import SQLiteSessionStore
from agentmuru.sessions import AssistantToolCall, Message, MessageRole, RunRecord, RunStatus
from tests.sessions.test_store_contract import (
    assert_assistant_tool_call_contract,
    assert_session_store_contract,
)


def test_sqlite_store_satisfies_contract_and_survives_reopen(tmp_path: Path) -> None:
    path = tmp_path / "agentmuru.db"
    first = SQLiteSessionStore(SQLiteDatabase(path))

    assert_session_store_contract(first)

    second = SQLiteSessionStore(SQLiteDatabase(path))
    sessions = second.list(user_id="user-1")
    assert len(sessions) == 1
    assert sessions[0].title == "Durable"
    assert sessions[0].messages[0].content == "hello"
    assert sessions[0].runs[0].status is RunStatus.RUNNING


def test_sqlite_store_round_trips_session_metadata_and_message_fields(tmp_path: Path) -> None:
    store = SQLiteSessionStore(SQLiteDatabase(tmp_path / "agentmuru.db"))
    session = store.create(user_id="user-1", title="Before")
    session.title = "After"
    session.metadata = {"team": "முரு", "rank": 2}
    store.save(session)
    message = store.append_message(
        session.id,
        Message(
            role=MessageRole.TOOL,
            content='{"ok": true}',
            name="lookup",
            tool_call_id="call-1",
        ),
    )

    loaded = store.get(session.id)
    assert loaded.title == "After"
    assert loaded.metadata == {"rank": 2, "team": "முரு"}
    assert loaded.messages == [message]


def test_sqlite_store_preserves_normalized_assistant_tool_calls(tmp_path: Path) -> None:
    path = tmp_path / "agentmuru.db"
    first = SQLiteSessionStore(SQLiteDatabase(path))

    assert_assistant_tool_call_contract(first)

    reopened = SQLiteSessionStore(SQLiteDatabase(path))
    [loaded] = reopened.list()
    assert loaded.messages[0].tool_calls == (
        AssistantToolCall(
            id="call-1",
            name="lookup",
            arguments={"limit": 3, "query": "muru"},
        ),
    )


def test_two_store_instances_allocate_unique_monotonic_sequences(tmp_path: Path) -> None:
    path = tmp_path / "agentmuru.db"
    first = SQLiteSessionStore(SQLiteDatabase(path, busy_timeout_ms=1000, max_retries=8))
    second = SQLiteSessionStore(SQLiteDatabase(path, busy_timeout_ms=1000, max_retries=8))
    session = first.create()

    def append(index: int) -> RuntimeEvent:
        store = first if index % 2 else second
        return store.append_event(
            session.id,
            RuntimeEvent.new(
                EventType.USER_MESSAGE_RECEIVED,
                session_id=session.id,
                payload={"index": index},
            ),
        )

    with ThreadPoolExecutor(max_workers=8) as pool:
        persisted = list(pool.map(append, range(40)))

    assert sorted(event.sequence for event in persisted) == list(range(1, 41))
    assert [event.sequence for event in first.events(session.id)] == list(range(1, 41))
    assert sorted(int(event.payload["index"]) for event in first.events(session.id)) == list(
        range(40)
    )


@pytest.mark.asyncio
async def test_subscription_observes_event_from_another_store_instance(tmp_path: Path) -> None:
    path = tmp_path / "agentmuru.db"
    subscriber = SQLiteSessionStore(SQLiteDatabase(path), poll_interval=0.01)
    writer = SQLiteSessionStore(SQLiteDatabase(path))
    session = subscriber.create()
    stream = subscriber.subscribe(session.id)

    writer.append_event(
        session.id,
        RuntimeEvent.new(EventType.SESSION_STARTED, session_id=session.id),
    )

    observed = await asyncio.wait_for(anext(stream), timeout=0.5)
    assert observed.sequence == 1
    assert observed.type is EventType.SESSION_STARTED
    await stream.aclose()


def test_recovery_fails_only_nonterminal_runs_and_preserves_history(tmp_path: Path) -> None:
    path = tmp_path / "agentmuru.db"
    first = SQLiteSessionStore(SQLiteDatabase(path))
    session = first.create()
    first.append_message(session.id, Message(role=MessageRole.USER, content="keep me"))
    running = first.create_run(
        RunRecord(session_id=session.id, agent_name="running", status=RunStatus.RUNNING)
    )
    completed = first.create_run(
        RunRecord(session_id=session.id, agent_name="completed", status=RunStatus.COMPLETED)
    )

    second = SQLiteSessionStore(SQLiteDatabase(path))
    recovered = second.recover_interrupted_runs()

    assert [item.id for item in recovered] == [running.id]
    assert second.get_run(running.id).status is RunStatus.FAILED
    assert second.get_run(running.id).error_code == "process_interrupted"
    assert second.get_run(completed.id).status is RunStatus.COMPLETED
    assert second.get(session.id).messages[0].content == "keep me"


def test_idempotency_binding_survives_reopen_and_remains_session_scoped(
    tmp_path: Path,
) -> None:
    path = tmp_path / "agentmuru.db"
    first = SQLiteSessionStore(SQLiteDatabase(path))
    first_session = first.create()
    second_session = first.create()
    first_run = first.create_run(RunRecord(session_id=first_session.id, agent_name="agent"))
    second_run = first.create_run(RunRecord(session_id=second_session.id, agent_name="agent"))
    first.bind_idempotency_key(first_session.id, "request", first_run.id)
    first.bind_idempotency_key(second_session.id, "request", second_run.id)

    reopened = SQLiteSessionStore(SQLiteDatabase(path))
    assert reopened.get_idempotent_run(first_session.id, "request") == first_run
    assert reopened.get_idempotent_run(second_session.id, "request") == second_run
