from fastapi.testclient import TestClient

from agentmuru import Agent, Application, FakeModel
from agentmuru.server import BearerTokenAuth, Principal, ServerSettings, create_asgi_app


def secured_client() -> TestClient:
    auth = BearerTokenAuth(
        {
            "alice-token": Principal(subject="alice", authenticated=True, roles=("user",)),
            "bob-token": Principal(subject="bob", authenticated=True, roles=("user",)),
        }
    )
    app = create_asgi_app(
        Application(agent=Agent(name="assistant", instructions="", model=FakeModel.responses("ok"))),
        settings=ServerSettings(allow_anonymous=False, auth_provider=auth, max_message_chars=8),
    )
    return TestClient(app)


def test_server_requires_auth_and_enforces_session_ownership() -> None:
    with secured_client() as client:
        assert client.post("/api/v1/sessions", json={}).status_code == 401
        session_id = client.post(
            "/api/v1/sessions",
            json={},
            headers={"Authorization": "Bearer alice-token"},
        ).json()["id"]

        forbidden = client.get(
            f"/api/v1/sessions/{session_id}",
            headers={"Authorization": "Bearer bob-token"},
        )

    assert forbidden.status_code == 403


def test_server_rejects_oversized_messages_and_adds_security_headers() -> None:
    with secured_client() as client:
        headers = {"Authorization": "Bearer alice-token"}
        session_id = client.post("/api/v1/sessions", json={}, headers=headers).json()["id"]
        response = client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={"content": "this is too long"},
            headers=headers,
        )
        health = client.get("/health", headers=headers)

    assert response.status_code == 422
    assert health.headers["x-content-type-options"] == "nosniff"
    assert "frame-ancestors 'none'" in health.headers["content-security-policy"]
