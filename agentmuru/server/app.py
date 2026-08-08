from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.trustedhost import TrustedHostMiddleware

from agentmuru.approvals import ApprovalDecision
from agentmuru.artifacts import Artifact
from agentmuru.core.application import Application
from agentmuru.core.errors import RunNotFoundError, SessionNotFoundError
from agentmuru.core.runtime import Runtime
from agentmuru.observability import Trace
from agentmuru.sessions import Message, RunRecord, Session
from agentmuru.version import __version__

from .auth import ANONYMOUS, AuthProvider, Principal, _principal
from .protocol import PROTOCOL_VERSION, control_envelope, event_envelope


@dataclass(frozen=True, slots=True)
class ServerSettings:
    allow_anonymous: bool = True
    auth_provider: AuthProvider | None = None
    trusted_hosts: tuple[str, ...] = ("testserver", "localhost", "127.0.0.1")
    cors_origins: tuple[str, ...] = ()
    websocket_origins: tuple[str, ...] = ()
    max_message_chars: int = 100_000
    frontend_dir: Path | None = None


class CreateSessionBody(BaseModel):
    title: str | None = None


class SubmitMessageBody(BaseModel):
    content: str
    idempotency_key: str | None = None


class ApprovalBody(BaseModel):
    decision: ApprovalDecision
    reason: str | None = None


def _resolve_principal(headers: Any, settings: ServerSettings) -> Principal:
    principal = settings.auth_provider.authenticate(headers) if settings.auth_provider else None
    if principal is not None and principal.authenticated:
        return principal
    if settings.allow_anonymous:
        return ANONYMOUS
    raise HTTPException(status_code=401, detail="Authentication required")


def _authorize_session(session: Session, principal: Principal) -> None:
    if session.user_id is not None and session.user_id != principal.subject:
        raise HTTPException(status_code=403, detail="Session access denied")


def _message_dict(message: Message) -> dict[str, Any]:
    return {
        "id": message.id,
        "role": message.role.value,
        "content": message.content,
        "name": message.name,
        "tool_call_id": message.tool_call_id,
        "created_at": message.created_at.isoformat(),
    }


def _run_dict(run: RunRecord) -> dict[str, Any]:
    return {
        "id": run.id,
        "session_id": run.session_id,
        "agent_name": run.agent_name,
        "status": run.status.value,
        "created_at": run.created_at.isoformat(),
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "error_code": run.error_code,
    }


def _session_dict(session: Session, *, detail: bool = True) -> dict[str, Any]:
    value: dict[str, Any] = {
        "id": session.id,
        "title": session.title,
        "user_id": session.user_id,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "metadata": session.metadata,
        "event_sequence": session.events[-1].sequence if session.events else 0,
    }
    if detail:
        value["messages"] = [_message_dict(message) for message in session.messages]
        value["runs"] = [_run_dict(run) for run in session.runs]
    return value


def _artifact_dict(artifact: Artifact, *, include_content: bool = False) -> dict[str, Any]:
    value = {
        "id": artifact.id,
        "session_id": artifact.session_id,
        "run_id": artifact.run_id,
        "kind": artifact.kind.value,
        "name": artifact.name,
        "mime_type": artifact.mime_type,
        "creator": artifact.creator,
        "metadata": dict(artifact.metadata),
        "created_at": artifact.created_at.isoformat(),
        "updated_at": artifact.updated_at.isoformat(),
    }
    if include_content:
        value["content"] = artifact.content
    return value


def _trace_dict(trace: Trace) -> dict[str, Any]:
    return {
        "id": trace.id,
        "session_id": trace.session_id,
        "run_id": trace.run_id,
        "name": trace.name,
        "status": trace.status,
        "started_at": trace.started_at.isoformat(),
        "ended_at": trace.ended_at.isoformat() if trace.ended_at else None,
        "usage": asdict(trace.usage),
        "spans": [
            {
                "id": span.id,
                "parent_id": span.parent_id,
                "name": span.name,
                "kind": span.kind,
                "status": span.status,
                "started_at": span.started_at.isoformat(),
                "ended_at": span.ended_at.isoformat() if span.ended_at else None,
                "duration_ms": span.duration_ms,
                "attributes": dict(span.attributes),
            }
            for span in trace.spans
        ],
    }


def create_asgi_app(
    application: Application,
    *,
    runtime: Runtime | None = None,
    settings: ServerSettings | None = None,
) -> FastAPI:
    settings = settings or ServerSettings()
    runtime = runtime or Runtime(application)
    app = FastAPI(title="AgentMuru Runtime", version=__version__, docs_url=None, redoc_url=None)
    app.state.runtime = runtime
    app.state.application = application
    app.state.settings = settings
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(settings.trusted_hosts))
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_origins),
            allow_methods=["GET", "POST", "PATCH"],
            allow_headers=["Authorization", "Content-Type"],
            allow_credentials=False,
        )

    @app.middleware("http")
    async def security_headers(request: Request, call_next: Any) -> Any:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; connect-src 'self' ws: wss:; img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline'; script-src 'self'; frame-ancestors 'none'"
        )
        return response

    async def principal_for(request: Request) -> Principal:
        principal = _resolve_principal(request.headers, settings)
        request.state.principal = principal
        return principal

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {"status": "ok", "product": "AgentMuru", "protocol_version": PROTOCOL_VERSION}

    @app.get("/api/v1/app")
    async def app_metadata(principal: Principal = Depends(principal_for)) -> dict[str, Any]:
        agents = (application.agent, *application.agents)
        return {
            "product": "AgentMuru",
            "workspace": "Muru Workspace",
            "version": __version__,
            "protocol_version": PROTOCOL_VERSION,
            "title": application.title,
            "description": application.description,
            "primary_agent": application.agent.name,
            "agents": [
                {
                    "name": agent.name,
                    "description": agent.description,
                    "model": agent.model.name,
                    "tools": [tool.name for tool in agent.tools],
                }
                for agent in agents
            ],
            "principal": {
                "subject": principal.subject,
                "authenticated": principal.authenticated,
                "roles": principal.roles,
            },
        }

    @app.post("/api/v1/sessions", status_code=201)
    async def create_session(
        body: CreateSessionBody,
        principal: Principal = Depends(principal_for),
    ) -> dict[str, Any]:
        session = runtime.create_session(
            user_id=principal.subject if principal.authenticated else None,
            title=body.title,
        )
        return _session_dict(session)

    @app.get("/api/v1/sessions")
    async def list_sessions(principal: Principal = Depends(principal_for)) -> dict[str, Any]:
        sessions = runtime.sessions.list()
        sessions = [
            session
            for session in sessions
            if session.user_id == (principal.subject if principal.authenticated else None)
        ]
        return {"sessions": [_session_dict(session, detail=False) for session in sessions]}

    @app.get("/api/v1/sessions/{session_id}")
    async def get_session(
        session_id: str,
        principal: Principal = Depends(principal_for),
    ) -> dict[str, Any]:
        try:
            session = runtime.sessions.get(session_id)
        except SessionNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Session not found") from exc
        _authorize_session(session, principal)
        value = _session_dict(session)
        value["artifacts"] = [
            _artifact_dict(item) for item in runtime.artifacts.list(session_id=session.id)
        ]
        value["approvals"] = [
            {
                "id": item.id,
                "run_id": item.run_id,
                "tool_name": item.tool_name,
                "arguments": dict(item.arguments),
                "permission": item.permission,
                "risk": item.risk,
                "status": item.status.value,
                "reason": item.reason,
                "expires_at": item.expires_at.isoformat() if item.expires_at else None,
            }
            for item in runtime.approvals.list(session_id=session.id)
        ]
        return value

    @app.post("/api/v1/sessions/{session_id}/messages", status_code=202)
    async def submit_message(
        session_id: str,
        body: SubmitMessageBody,
        principal: Principal = Depends(principal_for),
    ) -> dict[str, Any]:
        try:
            session = runtime.sessions.get(session_id)
        except SessionNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Session not found") from exc
        _authorize_session(session, principal)
        if len(body.content) > settings.max_message_chars:
            raise HTTPException(status_code=422, detail="Message exceeds configured size limit")
        run = await runtime.submit(
            session_id, body.content, idempotency_key=body.idempotency_key
        )
        return _run_dict(run)

    @app.get("/api/v1/sessions/{session_id}/events")
    async def list_events(
        session_id: str,
        after: int = 0,
        principal: Principal = Depends(principal_for),
    ) -> dict[str, Any]:
        try:
            session = runtime.sessions.get(session_id)
        except SessionNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Session not found") from exc
        _authorize_session(session, principal)
        return {
            "protocol_version": PROTOCOL_VERSION,
            "events": [event.to_dict() for event in runtime.sessions.events(session_id, after_sequence=after)],
        }

    @app.get("/api/v1/runs/{run_id}")
    async def get_run(
        run_id: str,
        principal: Principal = Depends(principal_for),
    ) -> dict[str, Any]:
        try:
            run = runtime.get_run(run_id)
        except RunNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Run not found") from exc
        _authorize_session(runtime.sessions.get(run.session_id), principal)
        return _run_dict(run)

    @app.post("/api/v1/runs/{run_id}/cancel")
    async def cancel_run(
        run_id: str,
        principal: Principal = Depends(principal_for),
    ) -> dict[str, Any]:
        run = runtime.get_run(run_id)
        _authorize_session(runtime.sessions.get(run.session_id), principal)
        return _run_dict(await runtime.cancel(run_id))

    @app.patch("/api/v1/approvals/{approval_id}")
    async def decide_approval(
        approval_id: str,
        body: ApprovalBody,
        principal: Principal = Depends(principal_for),
    ) -> dict[str, Any]:
        approval = runtime.approvals.get(approval_id)
        _authorize_session(runtime.sessions.get(approval.session_id), principal)
        decided = await runtime.decide_approval(
            approval_id,
            body.decision,
            actor=principal.subject,
            reason=body.reason,
        )
        return {
            "id": decided.id,
            "status": decided.status.value,
            "actor": decided.actor,
            "reason": decided.reason,
        }

    @app.get("/api/v1/artifacts/{artifact_id}")
    async def get_artifact(
        artifact_id: str,
        principal: Principal = Depends(principal_for),
    ) -> dict[str, Any]:
        try:
            artifact = runtime.artifacts.get(artifact_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Artifact not found") from exc
        _authorize_session(runtime.sessions.get(artifact.session_id), principal)
        return _artifact_dict(artifact, include_content=True)

    @app.get("/api/v1/runs/{run_id}/traces")
    async def get_traces(
        run_id: str,
        principal: Principal = Depends(principal_for),
    ) -> dict[str, Any]:
        run = runtime.get_run(run_id)
        _authorize_session(runtime.sessions.get(run.session_id), principal)
        return {"traces": [_trace_dict(trace) for trace in runtime.tracer.traces_for_run(run_id)]}

    @app.websocket("/api/v1/sessions/{session_id}/stream")
    async def session_stream(websocket: WebSocket, session_id: str, after: int = 0) -> None:
        try:
            principal = _resolve_principal(websocket.headers, settings)
            session = runtime.sessions.get(session_id)
            _authorize_session(session, principal)
        except HTTPException as exc:
            await websocket.close(code=4401 if exc.status_code == 401 else 4403)
            return
        except SessionNotFoundError:
            await websocket.close(code=4404)
            return
        origin = websocket.headers.get("origin")
        if settings.websocket_origins and origin not in settings.websocket_origins:
            await websocket.close(code=4403)
            return
        await websocket.accept()
        send_lock = asyncio.Lock()

        async def send(value: dict[str, Any]) -> None:
            async with send_lock:
                await websocket.send_json(value)

        async def publish_events() -> None:
            async for event in runtime.events(session_id, after_sequence=after):
                await send(event_envelope(event))

        sender = asyncio.create_task(publish_events())
        principal_token = _principal.set(principal)
        try:
            while True:
                action = await websocket.receive_json()
                if action.get("protocol_version") != PROTOCOL_VERSION:
                    await send(control_envelope("error", {"code": "unsupported_protocol"}))
                    continue
                kind = action.get("kind")
                data = action.get("data") or {}
                if kind == "ping":
                    await send(control_envelope("pong"))
                elif kind == "submit_message":
                    content = str(data.get("content", ""))
                    if not content or len(content) > settings.max_message_chars:
                        await send(control_envelope("error", {"code": "invalid_message"}))
                        continue
                    await runtime.submit(
                        session_id,
                        content,
                        idempotency_key=data.get("idempotency_key"),
                    )
                elif kind == "cancel_run":
                    run = runtime.get_run(str(data.get("run_id", "")))
                    if run.session_id != session_id:
                        await send(control_envelope("error", {"code": "session_mismatch"}))
                        continue
                    await runtime.cancel(run.id)
                elif kind == "decide_approval":
                    approval = runtime.approvals.get(str(data.get("approval_id", "")))
                    if approval.session_id != session_id:
                        await send(control_envelope("error", {"code": "session_mismatch"}))
                        continue
                    await runtime.decide_approval(
                        approval.id,
                        ApprovalDecision(str(data.get("decision"))),
                        actor=principal.subject,
                        reason=data.get("reason"),
                    )
                else:
                    await send(control_envelope("error", {"code": "unknown_action"}))
        except WebSocketDisconnect:
            pass
        finally:
            _principal.reset(principal_token)
            sender.cancel()
            await asyncio.gather(sender, return_exceptions=True)

    frontend_dir = settings.frontend_dir
    if frontend_dir is None:
        packaged = Path(__file__).resolve().parents[1] / "frontend" / "dist"
        frontend_dir = packaged if packaged.exists() else None
    if frontend_dir and (frontend_dir / "index.html").exists():
        assets = frontend_dir / "assets"
        if assets.exists():
            app.mount("/assets", StaticFiles(directory=assets), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        async def workspace(path: str) -> FileResponse:
            return FileResponse(frontend_dir / "index.html")

    return app


def run_server(application: Application, *, host: str, port: int) -> None:
    import uvicorn

    uvicorn.run(create_asgi_app(application), host=host, port=port)
