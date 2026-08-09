from __future__ import annotations

from pathlib import Path

import pytest

from agentmuru import Agent, Application, FakeModel, Runtime, SQLitePersistence
from agentmuru.core.events import EventType
from agentmuru.sessions import MessageRole, RunRecord, RunStatus


def _runtime(path: Path, *, model: FakeModel | None = None) -> Runtime:
    persistence = SQLitePersistence(path)
    return Runtime(
        Application(
            agent=Agent(
                name="assistant",
                instructions="Be useful",
                model=model or FakeModel.responses("Hello from durable Muru"),
            ),
            session_store=persistence.sessions,
            artifact_store=persistence.artifacts,
        ),
        approvals=persistence.approval_service(),
    )


@pytest.mark.asyncio
async def test_runtime_history_and_idempotency_survive_reopen(tmp_path: Path) -> None:
    path = tmp_path / "agentmuru.db"
    first = _runtime(path)
    session = first.create_session(title="durable")
    run = await first.submit(session.id, "hello", idempotency_key="request-1")
    completed = await first.wait(run.id)
    assert completed.status is RunStatus.COMPLETED

    second = _runtime(path)
    restored = second.sessions.get(session.id)
    replayed = await second.submit(session.id, "ignored", idempotency_key="request-1")

    assert replayed.id == run.id
    assert await second.wait(replayed.id) == replayed
    assert second.get_run(run.id).status is RunStatus.COMPLETED
    assert [(message.role, message.content) for message in restored.messages] == [
        (MessageRole.USER, "hello"),
        (MessageRole.ASSISTANT, "Hello from durable Muru"),
    ]
    assert restored.events[-1].type is EventType.RUN_COMPLETED


def test_runtime_marks_interrupted_runs_failed_and_emits_recovery_event(tmp_path: Path) -> None:
    path = tmp_path / "agentmuru.db"
    persistence = SQLitePersistence(path)
    session = persistence.sessions.create(title="interrupted")
    run = persistence.sessions.create_run(
        RunRecord(
            session_id=session.id,
            agent_name="assistant",
            status=RunStatus.RUNNING,
        )
    )

    runtime = Runtime(
        Application(
            agent=Agent(
                name="assistant",
                instructions="",
                model=FakeModel.responses("new work"),
            ),
            session_store=persistence.sessions,
            artifact_store=persistence.artifacts,
        ),
        approvals=persistence.approval_service(),
    )

    recovered = runtime.get_run(run.id)
    events = runtime.sessions.events(session.id)
    assert recovered.status is RunStatus.FAILED
    assert recovered.error_code == "process_interrupted"
    assert events[-1].type is EventType.RUN_FAILED
    assert events[-1].payload["code"] == "process_interrupted"

