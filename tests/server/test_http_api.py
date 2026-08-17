import time

from fastapi.testclient import TestClient

from agentmuru import Agent, Application, FakeModel
from agentmuru.server import create_asgi_app


def make_client() -> TestClient:
    application = Application(
        agent=Agent(name="assistant", instructions="help", model=FakeModel.responses("hello")),
        title="Support Muru",
    )
    return TestClient(create_asgi_app(application))


def test_http_api_creates_session_submits_message_and_exposes_replay() -> None:
    with make_client() as client:
        assert client.get("/health").json() == {
            "status": "ok",
            "product": "AgentMuru",
            "protocol_version": 1,
        }
        created = client.post("/api/v1/sessions", json={"title": "Demo"})
        assert created.status_code == 201
        session_id = created.json()["id"]

        submitted = client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={"content": "Hi", "idempotency_key": "message-1"},
        )
        assert submitted.status_code == 202
        run_id = submitted.json()["id"]

        for _ in range(20):
            run = client.get(f"/api/v1/runs/{run_id}").json()
            if run["status"] == "completed":
                break
            time.sleep(0.01)
        assert run["status"] == "completed"

        events = client.get(f"/api/v1/sessions/{session_id}/events?after=1").json()
        assert all(event["sequence"] > 1 for event in events["events"])
        assert events["protocol_version"] == 1
        session = client.get(f"/api/v1/sessions/{session_id}").json()
        assert session["messages"][-1]["content"] == "hello"
        assert session["messages"][-1]["tool_calls"] == []


def test_application_metadata_describes_agents_and_tools() -> None:
    with make_client() as client:
        metadata = client.get("/api/v1/app").json()

    assert metadata["title"] == "Support Muru"
    assert metadata["primary_agent"] == "assistant"
    assert metadata["agents"][0]["model"] == "fake"
