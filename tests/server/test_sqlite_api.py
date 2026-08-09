from __future__ import annotations

import time
from pathlib import Path

from fastapi.testclient import TestClient

from agentmuru import Agent, Application, ArtifactKind, FakeModel, Runtime, SQLitePersistence
from agentmuru.server import create_asgi_app


def _client(path: Path) -> TestClient:
    persistence = SQLitePersistence(path)
    application = Application(
        agent=Agent(
            name="assistant",
            instructions="help",
            model=FakeModel.responses("durable response"),
        ),
        session_store=persistence.sessions,
        artifact_store=persistence.artifacts,
    )
    runtime = Runtime(application, approvals=persistence.approval_service())
    return TestClient(create_asgi_app(application, runtime=runtime))


def test_sqlite_backed_api_restores_history_artifacts_and_replay(tmp_path: Path) -> None:
    path = tmp_path / "agentmuru.db"
    with _client(path) as first:
        session = first.post("/api/v1/sessions", json={"title": "durable"}).json()
        session_id = session["id"]
        submitted = first.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={"content": "hello", "idempotency_key": "request-1"},
        ).json()
        run_id = submitted["id"]
        for _ in range(50):
            if first.get(f"/api/v1/runs/{run_id}").json()["status"] == "completed":
                break
            time.sleep(0.01)
        runtime: Runtime = first.app.state.runtime
        artifact = runtime.create_artifact(
            session_id=session_id,
            run_id=run_id,
            kind=ArtifactKind.REPORT,
            name="qualification.md",
            content="# Qualified",
            mime_type="text/markdown",
            creator="assistant",
        )

    with _client(path) as second:
        restored = second.get(f"/api/v1/sessions/{session_id}")
        replay = second.get(f"/api/v1/sessions/{session_id}/events?after=0")
        stored_artifact = second.get(f"/api/v1/artifacts/{artifact.id}")
        idempotent = second.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={"content": "ignored", "idempotency_key": "request-1"},
        )

    assert restored.status_code == 200
    assert [message["content"] for message in restored.json()["messages"]] == [
        "hello",
        "durable response",
    ]
    assert restored.json()["runs"][0]["status"] == "completed"
    assert restored.json()["artifacts"][0]["id"] == artifact.id
    assert replay.json()["events"][-1]["type"] == "artifact.created"
    assert stored_artifact.json()["content"] == "# Qualified"
    assert idempotent.json()["id"] == run_id


def test_sqlite_websocket_replays_durable_sequence_after_reopen(tmp_path: Path) -> None:
    path = tmp_path / "agentmuru.db"
    with _client(path) as first:
        session_id = first.post("/api/v1/sessions", json={}).json()["id"]
        first.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={"content": "hello", "idempotency_key": "request-1"},
        )
        for _ in range(50):
            snapshot = first.get(f"/api/v1/sessions/{session_id}").json()
            if snapshot["runs"][0]["status"] == "completed":
                break
            time.sleep(0.01)
        after = snapshot["event_sequence"] - 1

    with _client(path) as second:
        with second.websocket_connect(
            f"/api/v1/sessions/{session_id}/stream?after={after}"
        ) as socket:
            envelope = socket.receive_json()

    assert envelope["kind"] == "event"
    assert envelope["data"]["sequence"] == after + 1
    assert envelope["data"]["type"] == "run.completed"

