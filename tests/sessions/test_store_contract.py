from __future__ import annotations

from agentmuru.sessions import (
    InMemorySessionStore,
    Message,
    MessageRole,
    RunRecord,
    RunStatus,
    SessionStore,
)


def assert_session_store_contract(store: SessionStore) -> None:
    session = store.create(user_id="user-1", title="Durable")
    message = store.append_message(
        session.id,
        Message(role=MessageRole.USER, content="hello"),
    )
    run = store.create_run(RunRecord(session_id=session.id, agent_name="assistant"))
    run.status = RunStatus.RUNNING
    store.update_run(run)
    store.bind_idempotency_key(session.id, "request-1", run.id)

    loaded = store.get(session.id)
    assert loaded.messages == [message]
    assert loaded.runs == [run]
    assert store.get_run(run.id).status is RunStatus.RUNNING
    assert store.get_idempotent_run(session.id, "request-1") == run
    assert store.get_idempotent_run(session.id, "missing") is None


def test_in_memory_store_satisfies_explicit_mutation_contract() -> None:
    assert_session_store_contract(InMemorySessionStore())


def test_in_memory_store_recovers_only_nonterminal_runs() -> None:
    store = InMemorySessionStore()
    session = store.create()
    running = store.create_run(
        RunRecord(session_id=session.id, agent_name="running", status=RunStatus.RUNNING)
    )
    completed = store.create_run(
        RunRecord(session_id=session.id, agent_name="completed", status=RunStatus.COMPLETED)
    )

    recovered = store.recover_interrupted_runs()

    assert [item.id for item in recovered] == [running.id]
    assert store.get_run(running.id).status is RunStatus.FAILED
    assert store.get_run(running.id).error_code == "process_interrupted"
    assert store.get_run(running.id).completed_at is not None
    assert store.get_run(completed.id).status is RunStatus.COMPLETED


def test_in_memory_store_keeps_idempotency_keys_scoped_to_session() -> None:
    store = InMemorySessionStore()
    first_session = store.create()
    second_session = store.create()
    first_run = store.create_run(
        RunRecord(session_id=first_session.id, agent_name="assistant")
    )
    second_run = store.create_run(
        RunRecord(session_id=second_session.id, agent_name="assistant")
    )

    store.bind_idempotency_key(first_session.id, "same-key", first_run.id)
    store.bind_idempotency_key(second_session.id, "same-key", second_run.id)

    assert store.get_idempotent_run(first_session.id, "same-key") == first_run
    assert store.get_idempotent_run(second_session.id, "same-key") == second_run
