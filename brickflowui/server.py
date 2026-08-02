"""
ASGI server for BrickflowUI.

Creates a FastAPI app that:
- Serves the pre-built React frontend at GET /
- Manages WebSocket sessions at WS /events
- Dispatches events to Python handlers and sends re-renders back
"""

from __future__ import annotations

import asyncio
import html
import inspect
import json
import logging
import re
import secrets
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional
from urllib.parse import urlparse

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .auth import (
    AuthenticationRequired,
    AuthorizationError,
    authorize_principal,
    reset_current_principal,
    resolve_principal,
    set_current_principal,
)
from .state import RenderContext, reset_render_context, set_render_context
from .vdom import EventHandler, VNode, diff

if TYPE_CHECKING:
    from .app import App

logger = logging.getLogger("brickflowui.server")
CSRF_COOKIE_NAME = "brickflowui_csrf"
CSRF_HEADER_NAME = "x-brickflow-csrf"

# Path to bundled frontend
_FRONTEND_DIST = Path(__file__).parent / "frontend" / "dist"


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------


def _full_tree_msg(vnode: VNode, handler_registry: dict, dbrx_app: "App") -> str:
    """Build full-tree WebSocket message."""
    tree = dbrx_app.transform_serialized_tree(vnode.serialize(handler_registry))
    return json.dumps({
        "type": "full",
        "tree": tree,
    })


def _patch_msg(patches: list, dbrx_app: "App") -> str:
    """Build patch WebSocket message."""
    return json.dumps({"type": "patch", "patches": dbrx_app.transform_serialized_tree(patches)})


def _serialize_patch_values(value: Any, handler_registry: dict) -> Any:
    """Convert VNodes nested in incremental prop patches to wire-safe values."""
    if isinstance(value, VNode):
        return value.serialize(handler_registry)
    if isinstance(value, (list, tuple)):
        return [_serialize_patch_values(item, handler_registry) for item in value]
    if isinstance(value, dict):
        return {
            key: _serialize_patch_values(item, handler_registry)
            for key, item in value.items()
        }
    return value


def _error_msg(message: str, error_id: Optional[str] = None) -> str:
    payload = {"type": "error", "message": message}
    if error_id:
        payload["error_id"] = error_id
    return json.dumps(payload)


def _log_correlated_exception(context: str) -> str:
    """Log the active exception privately and return a safe correlation ID."""
    error_id = uuid.uuid4().hex
    logger.exception("%s error_id=%s", context, error_id)
    return error_id


def _runtime_error_msg(session_id: str, context: str) -> str:
    """Log a private exception trace and return a safe correlated browser message."""
    error_id = _log_correlated_exception(f"[{session_id}] {context}")
    return _error_msg(
        f"Something went wrong. Reference error ID {error_id} when contacting support.",
        error_id,
    )


def _event_complete_msg(event_id: str) -> str:
    return json.dumps({"type": "event_complete", "event_id": event_id})


def _safe_json_data(value: object) -> str:
    """Encode JSON so it cannot terminate its containing HTML data element."""
    return (
        json.dumps(value)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def _safe_style_text(value: str) -> str:
    """Prevent developer-supplied theme CSS from closing the style element."""
    return re.sub(r"</(?=style)", r"<\\/", value, flags=re.IGNORECASE)


def _consume_task_exception(task: asyncio.Task) -> None:
    """Prevent noisy unretrieved-task warnings during websocket disconnect races."""
    try:
        task.exception()
    except (asyncio.CancelledError, RuntimeError):
        pass


def _origin_allowed(origin: Optional[str], host: Optional[str], allowed_origins: list[str]) -> bool:
    """Allow same-origin browser sessions by default, plus any explicitly configured origins."""
    if not origin:
        return True

    if "*" in allowed_origins:
        return True

    parsed_origin = urlparse(origin)
    if not parsed_origin.scheme or not parsed_origin.netloc:
        return False

    if host and parsed_origin.netloc == host:
        return True

    normalized_allowed = {value.rstrip("/") for value in allowed_origins}
    return origin.rstrip("/") in normalized_allowed


def _extract_event_payload(event_data: object) -> object:
    """Unwrap common frontend payload shapes into the value Python handlers expect."""
    if not isinstance(event_data, dict):
        return event_data

    if len(event_data) == 1:
        return next(iter(event_data.values()))

    return event_data


def _resolve_event_handler(
    event_id: object,
    current: Dict[str, EventHandler],
    previous: Dict[str, EventHandler],
) -> Optional[EventHandler]:
    """Accept events from the active or immediately previous render generation."""
    if not isinstance(event_id, str):
        return None
    return current.get(event_id) or previous.get(event_id)


def _event_handler_parameter_count(
    handler: Callable[..., object],
    cache: Dict[int, int],
) -> int:
    """Return cached handler arity for the latency-sensitive event path."""
    cache_key = id(handler)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    parameter_count = len(inspect.signature(handler).parameters)
    cache[cache_key] = parameter_count
    return parameter_count


def _call_event_handler(
    handler: Callable[..., object],
    payload: object,
    call_shape_cache: Dict[int, int],
) -> object:
    """Invoke a handler without repeating signature introspection per event."""
    parameter_count = _event_handler_parameter_count(handler, call_shape_cache)
    if parameter_count == 0:
        return handler()
    if isinstance(payload, dict) and parameter_count > 1:
        return handler(**payload)
    return handler(payload)


def _is_safe_http_method(method: str) -> bool:
    return method.upper() in {"GET", "HEAD", "OPTIONS", "TRACE"}


def _request_looks_browser_originated(request: Request) -> bool:
    return bool(
        request.cookies.get(CSRF_COOKIE_NAME)
        or request.headers.get("origin")
        or request.headers.get("referer")
    )


def _validate_csrf(request: Request) -> bool:
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    header_token = request.headers.get(CSRF_HEADER_NAME)
    return bool(cookie_token and header_token and secrets.compare_digest(cookie_token, header_token))


def _head_injections(dbrx_app: "App") -> str:
    """Build static shell head injections once for this ASGI app instance."""
    theme_css = _safe_style_text(dbrx_app.theme.to_css_variables())
    style_block = f"<style id=\"bf-theme-vars\">{theme_css}</style>"
    favicon_block = (
        f'<link rel="icon" href="{html.escape(str(dbrx_app.favicon), quote=True)}" />'
        if dbrx_app.favicon
        else ""
    )
    bootstrap = _safe_json_data(dbrx_app.loading_bootstrap())
    bootstrap_block = f'<script id="__BRICKFLOW_BOOTSTRAP__" type="application/json">{bootstrap}</script>'
    injections = [style_block, favicon_block, bootstrap_block]
    return "\n".join(block for block in injections if block)


def _prepare_spa_shell(dbrx_app: "App") -> tuple[str, int]:
    """Prepare the SPA shell once instead of reading and patching it per request."""
    head_injections = _head_injections(dbrx_app)
    index_path = _FRONTEND_DIST / "index.html"
    if not index_path.exists():
        return _missing_frontend_shell(head_injections, dbrx_app.title), 503

    shell_html = index_path.read_text(encoding="utf-8")
    escaped_title = html.escape(str(dbrx_app.title))
    shell_html = shell_html.replace("<title>BrickflowUI App</title>", f"<title>{escaped_title}</title>")
    if "</head>" in shell_html:
        shell_html = shell_html.replace("</head>", f"{head_injections}\n</head>")
    else:
        shell_html = f"{head_injections}\n{shell_html}"
    return shell_html, 200


# ---------------------------------------------------------------------------
# ASGI app factory
# ---------------------------------------------------------------------------


def create_asgi_app(dbrx_app: "App") -> FastAPI:
    """Create and return the FastAPI ASGI application."""
    spa_shell_html, spa_shell_status = _prepare_spa_shell(dbrx_app)
    docs_url = "/docs" if dbrx_app.enable_dev_docs else None
    openapi_url = "/openapi.json" if dbrx_app.enable_dev_docs else None
    fastapi_app = FastAPI(
        title="BrickflowUI App",
        docs_url=docs_url,
        redoc_url=None,
        openapi_url=openapi_url,
    )

    if dbrx_app.cors_origins:
        fastapi_app.add_middleware(
            CORSMiddleware,
            allow_origins=dbrx_app.cors_origins,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    if dbrx_app.trusted_hosts:
        fastapi_app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=dbrx_app.trusted_hosts,
        )

    @fastapi_app.middleware("http")
    async def add_security_headers(request, call_next):
        if (
            dbrx_app.csrf_protection
            and not _is_safe_http_method(request.method)
            and _request_looks_browser_originated(request)
            and not _validate_csrf(request)
        ):
            return JSONResponse({"detail": "Invalid or missing CSRF token."}, status_code=403)

        try:
            principal = resolve_principal(
                auth_mode=dbrx_app.auth_mode,
                auth_provider=dbrx_app.auth_provider,
                app_principal=dbrx_app.app_principal,
                allow_anonymous=dbrx_app.allow_anonymous,
                source=request,
            )
        except AuthenticationRequired:
            return JSONResponse({"detail": "Authentication required."}, status_code=401)
        except Exception:
            error_id = _log_correlated_exception("HTTP authentication failure")
            return JSONResponse(
                {"detail": "Authentication failed.", "error_id": error_id},
                status_code=500,
            )
        request.state.brickflow_principal = principal
        token = set_current_principal(principal)
        try:
            response = await call_next(request)
        finally:
            reset_current_principal(token)
        if dbrx_app.csrf_protection and _is_safe_http_method(request.method):
            if not request.cookies.get(CSRF_COOKIE_NAME):
                response.set_cookie(
                    CSRF_COOKIE_NAME,
                    secrets.token_urlsafe(24),
                    secure=request.url.scheme == "https",
                    httponly=False,
                    samesite="lax",
                )
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; connect-src 'self' ws: wss:; img-src 'self' data: https:; "
            "media-src 'self' data: https: blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; font-src 'self' data: https:; "
            "frame-ancestors 'self';",
        )
        return response

    # ── Static frontend assets ──────────────────────────────────────────────
    _assets_dir = _FRONTEND_DIST / "assets"
    if _assets_dir.exists():
        fastapi_app.mount(
            "/assets",
            StaticFiles(directory=str(_assets_dir)),
            name="assets",
        )

    @fastapi_app.get("/__brickflow_asset__/{asset_id}/{filename:path}", include_in_schema=False)
    async def brickflow_asset(asset_id: str, filename: str):
        asset_path = dbrx_app.get_registered_asset(asset_id)
        if asset_path is None or not asset_path.exists():
            raise HTTPException(status_code=404, detail="Asset not found")
        return FileResponse(asset_path)

    # ── Custom API Routes ──────────────────────────────────────────────────
    _mount_custom_routes(fastapi_app, dbrx_app)

    # ── WebSocket session handler (MUST come before catch-all GET) ──────────
    @fastapi_app.websocket("/events")
    async def events(ws: WebSocket):
        if not _origin_allowed(
            ws.headers.get("origin"),
            ws.headers.get("host"),
            dbrx_app.websocket_origins,
        ):
            await ws.close(code=1008)
            return

        try:
            principal = resolve_principal(
                auth_mode=dbrx_app.auth_mode,
                auth_provider=dbrx_app.auth_provider,
                app_principal=dbrx_app.app_principal,
                allow_anonymous=dbrx_app.allow_anonymous,
                source=ws,
            )
        except AuthenticationRequired:
            await ws.close(code=1008)
            return
        except Exception:
            error_id = _log_correlated_exception("WebSocket authentication failure")
            await ws.close(
                code=1011,
                reason=f"Authentication failed. Reference error ID {error_id}.",
            )
            return

        await ws.accept()

        session_id = str(uuid.uuid4())
        logger.info(f"[{session_id}] WebSocket connected")

        # Create a fresh render context for this session
        rerender_event = asyncio.Event()
        ctx = RenderContext(
            session_id=session_id,
            rerender_event=rerender_event,
        )
        dbrx_app._sessions[session_id] = ctx
        dbrx_app._session_paths[session_id] = ws.query_params.get("path") or "/"
        ctx.context["principal"] = principal

        # Per-session event handler registry (event_id → callable)
        handler_registry: Dict[str, EventHandler] = {}
        previous_handler_registry: Dict[str, EventHandler] = {}
        handler_call_shape_cache: Dict[int, int] = {}

        # ── Helper: render + send full tree ───────────────────────────────
        async def send_full_tree():
            nonlocal handler_registry, previous_handler_registry
            handler_registry = {}  # refresh on each full render
            previous_handler_registry = {}
            render_token = set_render_context(ctx)
            principal_token = set_current_principal(principal)
            try:
                ctx.reset_indices()
                vnode: VNode = dbrx_app._render(session_id)
                ctx.run_effects()
                ctx.dirty = False
                msg = _full_tree_msg(vnode, handler_registry, dbrx_app)
                await ws.send_text(msg)
                return vnode
            except Exception:
                await ws.send_text(_runtime_error_msg(session_id, "Render error"))
                return None
            finally:
                reset_render_context(render_token)
                reset_current_principal(principal_token)

        # ── Helper: re-render + send patch ────────────────────────────────
        async def send_patch(old_tree: Optional[VNode]):
            nonlocal handler_registry, previous_handler_registry
            new_handler_registry: Dict[str, EventHandler] = {}
            render_token = set_render_context(ctx)
            principal_token = set_current_principal(principal)
            try:
                ctx.reset_indices()
                new_tree: VNode = dbrx_app._render(session_id)
                ctx.run_effects()
                ctx.dirty = False
                patches = diff(old_tree, new_tree, new_handler_registry)
                patches = _serialize_patch_values(patches, new_handler_registry)
                previous_handler_registry = handler_registry
                handler_registry = new_handler_registry
                if patches:
                    await ws.send_text(_patch_msg(patches, dbrx_app))
                return new_tree
            except Exception:
                await ws.send_text(_runtime_error_msg(session_id, "Re-render error"))
                return old_tree
            finally:
                reset_render_context(render_token)
                reset_current_principal(principal_token)

        current_tree = await send_full_tree()

        # ── Event/rerender loop ────────────────────────────────────────────
        try:
            while True:
                completed_event_id: Optional[str] = None
                # Wait for either an incoming WS message or a dirty flag
                receive_task = asyncio.ensure_future(ws.receive_text())
                rerender_task = asyncio.ensure_future(rerender_event.wait())
                receive_task.add_done_callback(_consume_task_exception)
                rerender_task.add_done_callback(_consume_task_exception)

                done, pending = await asyncio.wait(
                    [receive_task, rerender_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )

                for task in pending:
                    task.cancel()
                if pending:
                    await asyncio.gather(*pending, return_exceptions=True)

                if receive_task in done:
                    # Handle incoming event from frontend
                    try:
                        raw = receive_task.result()
                        msg_data = json.loads(raw)
                    except RuntimeError as exc:
                        if "disconnect message" in str(exc).lower():
                            raise WebSocketDisconnect(code=1000) from exc
                        raise
                    except Exception:
                        continue

                    if msg_data.get("type") == "event":
                        event_id = msg_data.get("event_id")
                        event_data = msg_data.get("data", {})
                        handler = _resolve_event_handler(
                            event_id,
                            handler_registry,
                            previous_handler_registry,
                        )
                        if handler is not None:
                            try:
                                payload = _extract_event_payload(event_data)
                                if dbrx_app.audit_events:
                                    logger.info(
                                        "[%s] audit event=%s principal=%s path=%s",
                                        session_id,
                                        event_id,
                                        principal.subject,
                                        dbrx_app._session_paths.get(session_id, "/"),
                                    )
                                principal_token = set_current_principal(principal)
                                result = _call_event_handler(
                                    handler,
                                    payload,
                                    handler_call_shape_cache,
                                )

                                if inspect.isawaitable(result):
                                    await result
                            except Exception:
                                await ws.send_text(
                                    _runtime_error_msg(
                                        session_id,
                                        f"Handler error for {event_id}",
                                    )
                                )
                            finally:
                                reset_current_principal(principal_token)
                                completed_event_id = str(event_id)

                    elif msg_data.get("type") == "navigate":
                        path = msg_data.get("path", "/")
                        dbrx_app._navigate(session_id, path)

                if rerender_task in done:
                    rerender_event.clear()

                # If any state change occurred, re-render
                if ctx.dirty:
                    current_tree = await send_patch(current_tree)

                if completed_event_id is not None:
                    await ws.send_text(_event_complete_msg(completed_event_id))

        except WebSocketDisconnect:
            logger.info(f"[{session_id}] WebSocket disconnected")
        except asyncio.CancelledError:
            pass
        finally:
            ctx.cleanup_effects()
            dbrx_app._sessions.pop(session_id, None)
            dbrx_app._session_paths.pop(session_id, None)

    # ── HTML shell (MUST come last as a catch-all) ─────────────────────────
    @fastapi_app.get("/{full_path:path}", include_in_schema=False)
    async def spa_shell(full_path: str):
        """Serve the SPA shell for all non-API, non-WS routes."""
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")

        return HTMLResponse(spa_shell_html, status_code=spa_shell_status)

    return fastapi_app


# ---------------------------------------------------------------------------
# Server runner
# ---------------------------------------------------------------------------


def run_server(dbrx_app: "App", host: str, port: int, reload: bool = False):
    logger.info(f"Starting BrickflowUI server on http://{host}:{port}")
    asgi_app = create_asgi_app(dbrx_app)

    uvicorn.run(
        asgi_app,
        host=host,
        port=port,
        log_level="info",
        reload=reload,
    )


def _mount_custom_routes(fastapi_app: FastAPI, dbrx_app: "App"):
    """Mount any routes registered via @app.route(...)."""
    async def _guard(request: Request):
        spec = dbrx_app._custom_routes.get(request.url.path)
        principal = getattr(request.state, "brickflow_principal", None)
        if spec is None or principal is None:
            return
        try:
            authorize_principal(principal, access=spec.access, roles=spec.roles)
        except AuthenticationRequired as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        except AuthorizationError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

    for path, spec in dbrx_app._custom_routes.items():
        fastapi_app.add_api_route(
            path,
            spec.handler,
            methods=spec.methods,
            dependencies=[] if spec.access == "public" and not spec.roles else [Depends(_guard)],
        )


# ---------------------------------------------------------------------------
# Fallback HTML shell (used when frontend/dist doesn't exist yet)
# ---------------------------------------------------------------------------


def _missing_frontend_diagnostic(title: str) -> str:
    """Return an explicit non-functional diagnostic for an incomplete install."""
    safe_title = html.escape(title, quote=False)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{safe_title} - frontend unavailable</title>
</head>
<body>
  <main>
    <h1>BrickflowUI frontend bundle is missing</h1>
    <p>The packaged React assets required to run this application were not found.</p>
    <p>Install a complete BrickflowUI wheel, or run <code>npm ci &amp;&amp; npm run build</code>
       from the <code>frontend</code> directory before starting the source checkout.</p>
  </main>
</body>
</html>"""


def _minimal_html_shell(
    style_block: str = "",
    title: str = "BrickflowUI App",
    loading: Optional[Dict[str, object]] = None,
) -> str:
    """Render a lightweight fallback shell when the packaged frontend is unavailable."""
    loading = loading or {}
    loading_title = html.escape(str(loading.get("title") or title))
    loading_message = html.escape(str(loading.get("message") or "Connecting to runtime..."))
    loading_subtitle = str(loading.get("subtitle") or "").strip()
    loading_asset = str(loading.get("video") or loading.get("asset") or "").strip()
    loading_kind = str(loading.get("assetKind") or ("video" if loading.get("video") else "image")).strip()
    loading_media = ""
    if loading_asset:
        escaped_asset = html.escape(loading_asset, quote=True)
        if loading_kind == "video":
            loading_media = (
                f'<video class="loading-media" src="{escaped_asset}" autoplay muted loop playsinline></video>'
            )
        else:
            loading_media = f'<img class="loading-media" src="{escaped_asset}" alt="{loading_title} loading" />'
    elif not bool(loading.get("textOnly")):
        loading_media = (
            '<div class="loading-mark" aria-hidden="true">'
            '<div class="loading-mark-tile">'
            '<span class="loading-mark-bar loading-mark-bar-long"></span>'
            '<span class="loading-mark-bar loading-mark-bar-medium"></span>'
            '<span class="loading-mark-bar loading-mark-bar-short"></span>'
            "</div>"
            "</div>"
        )

    subtitle_html = (
        f'<div class="loading-subtitle">{html.escape(loading_subtitle)}</div>'
        if loading_subtitle
        else ""
    )

    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>__APP_TITLE__</title>
  __STYLE_BLOCK__
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: var(--db-bg);
      color: var(--db-text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }}
    #root {{ flex: 1; display: flex; flex-direction: column; width: 100%; }}
    
    /* Layout components fallback styles */
    column, .column {{ display: flex; flex-direction: column; }}
    row, .row {{ display: flex; flex-direction: row; }}
    
    .loading-screen {{
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      flex: 1;
      gap: 16px;
    }}
    .loading-mark {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 14px;
      border-radius: 20px;
      background:
        radial-gradient(circle at top, color-mix(in srgb, var(--db-primary) 12%, transparent), transparent 68%),
        color-mix(in srgb, var(--db-surface) 90%, transparent);
      box-shadow: 0 18px 42px rgba(15, 23, 42, 0.14);
      border: 1px solid color-mix(in srgb, var(--db-primary) 18%, var(--db-border));
    }}
    .loading-mark-tile {{
      width: 84px;
      height: 84px;
      border-radius: 18px;
      background: color-mix(in srgb, var(--db-primary) 10%, var(--db-surface));
      border: 1px solid color-mix(in srgb, var(--db-primary) 24%, var(--db-border));
      display: grid;
      align-content: center;
      gap: 7px;
      padding: 0 16px;
    }}
    .loading-mark-bar {{
      display: block;
      height: 8px;
      border-radius: 999px;
      background: linear-gradient(90deg, var(--db-primary), color-mix(in srgb, var(--db-primary) 64%, white));
      box-shadow: 0 8px 18px color-mix(in srgb, var(--db-primary) 24%, transparent);
    }}
    .loading-mark-bar-long {{ width: 44px; }}
    .loading-mark-bar-medium {{ width: 34px; }}
    .loading-mark-bar-short {{ width: 26px; }}
    .spinner {{
      width: 40px; height: 40px;
      border: 3px solid var(--db-border);
      border-top-color: var(--db-primary);
      border-radius: 50%;
      animation: spin 1s linear infinite;
    }}
    @keyframes spin {{
      to {{ transform: rotate(360deg); }}
    }}
    .loading-brand {{ font-size: 24px; font-weight: 600; color: var(--db-primary); }}
    .loading-subtitle {{ font-size: 16px; font-weight: 500; color: var(--db-text); }}
    .loading-hint {{ font-size: 14px; color: var(--db-text-muted); }}
    .loading-media {{
      max-width: 168px;
      max-height: 168px;
      width: auto;
      height: auto;
      border-radius: 16px;
      object-fit: contain;
      box-shadow: 0 18px 42px rgba(15, 23, 42, 0.14);
      border: 1px solid rgba(148, 163, 184, 0.24);
      background: rgba(255, 255, 255, 0.68);
    }}
  </style>
</head>
<body>
  <div id="root">
    <div class="loading-screen">
      __LOADING_MEDIA__
      <div class="loading-brand">__APP_TITLE__</div>
      __LOADING_SUBTITLE__
      <div class="loading-hint">__LOADING_MESSAGE__</div>
    </div>
  </div>
  <script>
    const WS_URL = (location.protocol === 'https:' ? 'wss' : 'ws') + '://' + location.host + '/events';
    let ws;
    let tree = null;

    function connect() {{
      ws = new WebSocket(WS_URL);
      ws.onopen = () => {{ document.title = "BrickflowUI - Connected"; }};
      ws.onmessage = (e) => {{
        const msg = JSON.parse(e.data);
        if (msg.type === 'full') {{
          tree = msg.tree;
          render(tree);
        }} else if (msg.type === 'patch') {{
          // Simplistic patch application (full re-render for now in fallback)
          tree = applyPatches(tree, msg.patches);
          render(tree);
        }} else if (msg.type === 'error') {{
          console.error(msg.message);
        }}
      }};
      ws.onclose = () => {{
        document.title = "BrickflowUI - Disconnected";
        setTimeout(connect, 2000);
      }};
    }}

    function render(node) {{
      const root = document.getElementById('root');
      root.innerHTML = '';
      if (node) root.appendChild(createEl(node));
    }}

    function createEl(node) {{
      if (!node) return document.createTextNode('');
      if (typeof node === 'string') return document.createTextNode(node);
      
      const type = node.type.toLowerCase().split('.').pop();
      // Map components to standard HTML where obvious
      const tagMap = {{ 'column': 'div', 'row': 'div', 'text': 'div', 'button': 'button', 'input': 'input', 'card': 'div' }};
      const el = document.createElement(tagMap[type] || 'div');
      if (tagMap[type]) el.classList.add(type);
      
      if (node.props) {{
        Object.entries(node.props).forEach(([k, v]) => {{
          if (k === 'style' && typeof v === 'object') {{
             Object.assign(el.style, v);
          }} else if (k === 'className') {{
             el.className += ' ' + v;
          }} else if (k.startsWith('on')) {{
             el.addEventListener(k.toLowerCase().slice(2), () => {{
                ws.send(JSON.stringify({{ type: 'event', event_id: v }}));
             }});
          }} else {{
             if (v !== null && v !== undefined) el.setAttribute(k, v);
          }}
        }});
      }}
      if (node.children) {{
        node.children.forEach(child => el.appendChild(createEl(child)));
      }}
      return el;
    }}

    function applyPatches(oldTree, patches) {{
      // In a real VDOM this is complex. For fallback, we just return the new tree 
      // if the patch contains the whole thing, or do nothing.
      // But our backend sends full patches. For now, let's just hope for the best 
      // or implement a minimal patch applier.
      // Since 'patch' msg in server.py sends a list of diffs, 
      // and our fallback render cleared root, we might need a better way.
      // ACTUALLY, server.py send_patch sends 'type': 'patch', 'patches': diffs
      return oldTree; // Fallback doesn't support complex patching yet
    }

    connect();
  </script>
</body>
</html>
""".replace("__STYLE_BLOCK__", style_block).replace("__APP_TITLE__", loading_title).replace("__LOADING_MEDIA__", loading_media).replace("__LOADING_SUBTITLE__", subtitle_html).replace("__LOADING_MESSAGE__", loading_message)


def _missing_frontend_shell(head_injections: str, title: str) -> str:
    """Return an honest diagnostic when the packaged React frontend is unavailable."""
    escaped_title = html.escape(str(title))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escaped_title} - Frontend unavailable</title>
  {head_injections}
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 0; background: var(--db-bg, #f8fafc); color: var(--db-text, #0f172a); }}
    main {{ max-width: 720px; margin: 12vh auto; padding: 32px; border: 1px solid var(--db-border, #cbd5e1); border-radius: 16px; background: var(--db-surface, #fff); }}
    code {{ padding: 2px 6px; border-radius: 6px; background: var(--db-surface-muted, #f1f5f9); }}
  </style>
</head>
<body>
  <main role="alert">
    <h1>BrickflowUI frontend bundle is missing</h1>
    <p>The server cannot render this application without the packaged React frontend.</p>
    <p>Install a published BrickflowUI wheel, or run <code>npm ci</code> and <code>npm run build</code> in the <code>frontend</code> directory.</p>
  </main>
</body>
</html>"""
