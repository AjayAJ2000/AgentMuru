from fastapi.testclient import TestClient

from agentmuru import Agent, Application, FakeModel
from agentmuru.server import create_asgi_app


def test_websocket_replays_events_from_requested_sequence() -> None:
    app = create_asgi_app(
        Application(agent=Agent(name="assistant", instructions="", model=FakeModel.responses("ok")))
    )
    with TestClient(app) as client:
        session_id = client.post("/api/v1/sessions", json={}).json()["id"]
        with client.websocket_connect(f"/api/v1/sessions/{session_id}/stream?after=0") as socket:
            envelope = socket.receive_json()

    assert envelope["protocol_version"] == 1
    assert envelope["kind"] == "event"
    assert envelope["data"]["type"] == "session.started"


def test_websocket_accepts_typed_submit_action() -> None:
    app = create_asgi_app(
        Application(agent=Agent(name="assistant", instructions="", model=FakeModel.responses("ok")))
    )
    with TestClient(app) as client:
        session_id = client.post("/api/v1/sessions", json={}).json()["id"]
        with client.websocket_connect(f"/api/v1/sessions/{session_id}/stream") as socket:
            socket.receive_json()
            socket.send_json(
                {
                    "protocol_version": 1,
                    "kind": "submit_message",
                    "data": {"content": "hello", "idempotency_key": "ws-1"},
                }
            )
            event_types = []
            for _ in range(12):
                event_types.append(socket.receive_json()["data"]["type"])
                if "run.completed" in event_types:
                    break

    assert "user.message.received" in event_types
    assert "run.completed" in event_types
