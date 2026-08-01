import dataclasses
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
import brickflowui as db
import brickflowui.server as server
from brickflowui.app import App
from brickflowui.auth import HeaderAuthProvider, current_user
from brickflowui.server import _minimal_html_shell, create_asgi_app
from brickflowui.vdom import VNode


def _find_node_by_type(node: dict, node_type: str) -> dict | None:
    if node.get("type") == node_type:
        return node
    for child in node.get("children", []):
        found = _find_node_by_type(child, node_type)
        if found:
            return found
    for value in node.get("props", {}).values():
        if isinstance(value, dict):
            found = _find_node_by_type(value, node_type)
            if found:
                return found
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    found = _find_node_by_type(item, node_type)
                    if found:
                        return found
    return None


def test_app_page_registration():
    app = App(title="Test App")
    
    @app.page("/", title="Home")
    def home():
        return VNode(type="div")
        
    assert "/" in app._pages
    assert app._pages["/"].title == "Home"
    assert app._root_fn == home

    @app.page("/other")
    def other():
        return VNode(type="span")
    
    assert "/other" in app._pages
    # _root_fn should still be home as it was registered first at "/"
    assert app._root_fn == home
 # First page at "/" or first page generally? 
    # Actually code says: if not self._root_fn and path == "/": self._root_fn = fn
    # So if I didn't register "/", it won't be root_fn yet.

def test_app_render_basic():
    app = App()
    @app.page("/")
    def home():
        return VNode(type="div", props={"id": "root-node"})
    
    # Simulate a session
    from brickflowui.state import RenderContext
    session_id = "sess-1"
    app._sessions[session_id] = RenderContext(session_id=session_id)
    app._session_paths[session_id] = "/"
    
    vnode = app._render(session_id)
    assert vnode.type == "div"
    assert vnode.props["id"] == "root-node"

def test_server_spa_shell():
    app = App()
    app.mount(lambda: VNode(type="div"))
    asgi = create_asgi_app(app)
    client = TestClient(asgi)
    
    response = client.get("/")
    assert response.status_code == 200
    assert "BrickflowUI App" in response.text


def test_shell_escapes_title_favicon_and_bootstrap_html():
    app = App(
        title='</title><img src=x>',
        favicon='" onload="alert(1)',
        loading={"message": "</script><img src=x>"},
    )
    app.mount(lambda: VNode(type="div"))

    response = TestClient(create_asgi_app(app)).get("/")

    assert response.status_code == 200
    assert "</title><img" not in response.text
    assert 'onload="alert(1)' not in response.text
    assert "</script><img" not in response.text


def test_missing_frontend_bundle_returns_diagnostic(monkeypatch):
    monkeypatch.setattr(server, "_FRONTEND_DIST", Path("missing-frontend-dist"))
    app = App()
    app.mount(lambda: VNode(type="div"))

    response = TestClient(create_asgi_app(app)).get("/")

    assert response.status_code == 503
    assert "frontend bundle is missing" in response.text.lower()
    assert "new WebSocket" not in response.text


def test_shell_bootstrap_and_local_asset_route():
    asset = Path("docs/assets/brickflowui-mark.svg").resolve()

    app = App(
        title="Asset App",
        favicon=str(asset),
        loading={
            "asset": str(asset),
            "message": "Booting secure workspace",
            "animation": "pulse",
        },
    )
    app.mount(lambda: VNode(type="div"))
    client = TestClient(create_asgi_app(app))

    response = client.get("/")
    assert response.status_code == 200
    assert 'id="brickflow-bootstrap" type="application/json"' in response.text
    assert "Booting secure workspace" in response.text
    assert "/__brickflow_asset__/" in response.text

    asset_url = app.asset_url(str(asset))
    asset_response = client.get(asset_url)
    assert asset_response.status_code == 200
    assert b"<svg" in asset_response.content


def test_local_asset_registry_enforces_roots_limit_and_revalidation():
    safe_root = Path("docs/assets").resolve()
    first = safe_root / "auth-guard-flow.png"
    second = safe_root / "auth-guard-flow.svg"
    third = safe_root / "bfui-darkbg.svg"
    outside = Path("README.md").resolve()

    app = App(asset_roots=[safe_root], asset_registry_limit=2)

    first_url = app.asset_url(first)
    second_url = app.asset_url(second)
    third_url = app.asset_url(third)
    first_id = str(first_url).split("/")[2]
    second_id = str(second_url).split("/")[2]
    third_id = str(third_url).split("/")[2]

    assert str(first_url).startswith("/__brickflow_asset__/")
    assert app.asset_url(outside) == outside
    assert app.get_registered_asset(first_id) is None
    assert app.get_registered_asset(second_id) == second.resolve()
    assert app.get_registered_asset(third_id) == third.resolve()

    app.asset_roots = (outside.parent / "examples",)
    assert app.get_registered_asset(third_id) is None


def test_asset_registry_rejects_non_positive_limits():
    with pytest.raises(ValueError, match="greater than 0"):
        App(asset_registry_limit=0)


def test_shell_bootstrap_includes_theme_mode_and_subtitle():
    app = App(
        title="Acme Analytics",
        theme={"branding": {"tagline": "React components. Python syntax."}},
        loading={"subtitle": "Querying warehouse metadata"},
    )
    app.mount(lambda: VNode(type="div"))
    client = TestClient(create_asgi_app(app))

    response = client.get("/")

    assert response.status_code == 200
    assert "Querying warehouse metadata" in response.text
    assert "\"themeMode\": \"light\"" in response.text


def test_shell_bootstrap_includes_style_preset_and_loading_modes():
    asset = Path("docs/assets/brickflowui-mark.svg").resolve()
    app = App(
        theme={"style_preset": "bento"},
        loading={
            "light": {"asset": str(asset), "message": "Loading light workspace"},
            "dark": {"message": "Loading dark workspace", "animation": "pulse"},
        },
    )
    app.mount(lambda: VNode(type="div"))
    client = TestClient(create_asgi_app(app))

    response = client.get("/")

    assert response.status_code == 200
    assert "\"stylePreset\": \"bento\"" in response.text
    assert "Loading light workspace" in response.text
    assert "Loading dark workspace" in response.text
    assert "/__brickflow_asset__/" in response.text


def test_minimal_shell_uses_builtin_loading_mark_when_no_custom_media_is_configured():
    html = _minimal_html_shell(
        title="Fallback App",
        loading={
            "title": "Fallback App",
            "message": "Connecting to runtime...",
            "subtitle": "Built-in brand mark should render.",
        },
    )

    assert 'class="loading-mark"' in html
    assert "Built-in brand mark should render." in html
    assert 'class="spinner"' not in html


def test_custom_api_route():
    app = App()
    
    @app.route("/api/health")
    async def health():
        return {"status": "ok"}
        
    asgi = create_asgi_app(app)
    client = TestClient(asgi)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_custom_route_registered_after_server_access_is_available():
    app = App()
    _ = app.server

    @app.route("/api/late")
    async def late():
        return {"status": "late"}

    client = TestClient(app.server)
    response = client.get("/api/late")
    assert response.status_code == 200
    assert response.json() == {"status": "late"}

def test_unknown_api_path_returns_404():
    app = App()
    app.mount(lambda: VNode(type="div"))
    client = TestClient(create_asgi_app(app))

    response = client.get("/api/missing")
    assert response.status_code == 404

def test_security_headers_present_on_shell():
    app = App()
    app.mount(lambda: VNode(type="div"))
    client = TestClient(create_asgi_app(app))

    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "SAMEORIGIN"


def test_safe_requests_receive_csrf_cookie_by_default():
    app = App()
    app.mount(lambda: VNode(type="div"))
    client = TestClient(create_asgi_app(app))

    response = client.get("/")

    assert response.status_code == 200
    assert "brickflowui_csrf" in response.cookies


def test_unsafe_browser_requests_require_valid_csrf_token():
    app = App()

    @app.route("/api/submit", methods=["POST"])
    async def submit():
        return {"status": "ok"}

    client = TestClient(create_asgi_app(app))
    seed = client.get("/")
    csrf = seed.cookies.get("brickflowui_csrf")
    assert csrf

    denied = client.post("/api/submit", json={"name": "blocked"}, headers={"origin": "http://testserver"})
    assert denied.status_code == 403

    allowed = client.post(
        "/api/submit",
        json={"name": "allowed"},
        headers={"origin": "http://testserver", "x-brickflow-csrf": csrf},
    )
    assert allowed.status_code == 200
    assert allowed.json() == {"status": "ok"}

def test_protected_route_requires_authenticated_user():
    app = App(auth_mode="user", auth_provider=HeaderAuthProvider())

    @app.route("/api/secure", methods=["GET"], access="user")
    async def secure():
        return {"status": "ok"}

    client = TestClient(create_asgi_app(app))

    denied = client.get("/api/secure")
    assert denied.status_code == 401

    allowed = client.get("/api/secure", headers={"x-brickflow-user-id": "alice"})
    assert allowed.status_code == 200
    assert allowed.json() == {"status": "ok"}

def test_websocket_page_uses_authenticated_user_context():
    app = App(auth_mode="user", auth_provider=HeaderAuthProvider())

    @app.page("/", access="user")
    def home():
        user = current_user()
        return VNode(type="Text", props={"value": user.subject if user else "missing", "variant": "body"})

    client = TestClient(create_asgi_app(app))

    with client.websocket_connect("/events", headers={"x-brickflow-user-id": "alice"}) as websocket:
        payload = websocket.receive_json()

    assert payload["type"] == "full"
    assert payload["tree"]["props"]["value"] == "alice"


def test_forwarded_access_token_is_private_and_available_in_user_context():
    provider = HeaderAuthProvider()
    principal = provider._from_mapping(
        {
            "x-brickflow-user-id": "alice",
            "x-forwarded-access-token": "secret-user-token",
        }
    )

    assert principal is not None
    assert principal.access_token == "secret-user-token"
    assert "secret-user-token" not in repr(principal)
    assert principal == dataclasses.replace(principal, access_token="different-token")

    app = App(auth_mode="user", auth_provider=provider)

    @app.page("/", access="user")
    def home():
        user = current_user()
        return VNode(
            type="Text",
            props={"value": "token-present" if user and user.access_token else "token-missing"},
        )

    client = TestClient(create_asgi_app(app))
    with client.websocket_connect(
        "/events",
        headers={
            "x-brickflow-user-id": "alice",
            "x-forwarded-access-token": "secret-user-token",
        },
    ) as websocket:
        payload = websocket.receive_json()

    serialized = json.dumps(payload)
    assert payload["tree"]["props"]["value"] == "token-present"
    assert "secret-user-token" not in serialized


def test_header_provider_accepts_native_databricks_forwarded_identity():
    principal = HeaderAuthProvider()._from_mapping(
        {
            "x-forwarded-user": "user-123",
            "x-forwarded-preferred-username": "Alice Analyst",
            "x-forwarded-email": "alice@example.com",
            "x-forwarded-access-token": "secret-user-token",
        }
    )

    assert principal is not None
    assert principal.subject == "user-123"
    assert principal.display_name == "Alice Analyst"
    assert principal.email == "alice@example.com"
    assert principal.access_token == "secret-user-token"

def test_websocket_page_renders_access_denied_without_user():
    app = App(auth_mode="user", auth_provider=HeaderAuthProvider())

    @app.page("/", access="user")
    def home():
        return VNode(type="div")

    client = TestClient(create_asgi_app(app))

    with client.websocket_connect("/events") as websocket:
        payload = websocket.receive_json()

    assert payload["type"] == "full"
    assert payload["tree"]["type"] == "Column"


def test_websocket_render_error_is_correlated_and_redacted(caplog):
    app = App()

    @app.page("/")
    def home():
        raise RuntimeError("database-password must never reach the browser")

    client = TestClient(create_asgi_app(app))
    with caplog.at_level("ERROR", logger="brickflowui.server"):
        with client.websocket_connect("/events") as websocket:
            payload = websocket.receive_json()

    assert payload["type"] == "error"
    assert payload["error_id"]
    assert "database-password" not in payload["message"]
    assert "database-password" not in json.dumps(payload)
    assert "database-password" in caplog.text
    assert payload["error_id"] in caplog.text


def test_shell_sidebar_hides_pages_user_cannot_access():
    app = App(auth_mode="user", auth_provider=HeaderAuthProvider())

    @app.page("/", title="Overview")
    def overview():
        return db.Text("Overview")

    @app.page("/admin", title="Admin", access="user", roles=["admin"])
    def admin():
        return db.Text("Admin")

    client = TestClient(create_asgi_app(app))

    with client.websocket_connect("/events", headers={"x-brickflow-user-id": "alice", "x-brickflow-user-roles": "viewer"}) as websocket:
        payload = websocket.receive_json()

    sidebar = _find_node_by_type(payload["tree"], "Sidebar")
    assert sidebar is not None
    labels = [child["props"]["label"] for child in sidebar["children"]]
    assert "Overview" in labels
    assert "Admin" not in labels

def test_extract_event_payload_unwraps_single_value():
    from brickflowui.server import _extract_event_payload

    assert _extract_event_payload({"value": "abc"}) == "abc"
    assert _extract_event_payload({"row": {"id": 1}}) == {"id": 1}
    assert _extract_event_payload({"value": ["bronze", "silver"]}) == ["bronze", "silver"]
    assert _extract_event_payload({"value": {"start": "2026-04-01", "end": "2026-04-07"}}) == {"start": "2026-04-01", "end": "2026-04-07"}
    assert _extract_event_payload({"a": 1, "b": 2}) == {"a": 1, "b": 2}


def test_multiselect_event_payload_updates_state_and_rerenders():
    app = App()

    @app.page("/")
    def home():
        values, set_values = db.use_state([])
        return db.Column(
            [
                db.Text(",".join(values) if values else "none"),
                db.MultiSelect(
                    name="layers",
                    label="Layers",
                    options=[
                        {"label": "Bronze", "value": "bronze"},
                        {"label": "Silver", "value": "silver"},
                    ],
                    values=values,
                    on_change=set_values,
                ),
            ]
        )

    client = TestClient(create_asgi_app(app))

    with client.websocket_connect("/events") as websocket:
        full = websocket.receive_json()
        control = _find_node_by_type(full["tree"], "MultiSelect")
        assert control is not None

        websocket.send_json(
            {
                "type": "event",
                "event_id": control["props"]["change"],
                "data": {"value": ["bronze", "silver"]},
            }
        )
        patch = websocket.receive_json()

    assert patch["type"] == "patch"
    text_patch = next(item for item in patch["patches"] if item["path"] == [0])
    assert text_patch["props"]["value"] == "bronze,silver"


def test_date_range_event_payload_updates_state_and_rerenders():
    app = App()

    @app.page("/")
    def home():
        selected, set_selected = db.use_state({"start": "", "end": ""})
        return db.Column(
            [
                db.Text(f"{selected['start']}->{selected['end']}"),
                db.DateRangePicker(
                    name="window",
                    label="Window",
                    start=selected["start"],
                    end=selected["end"],
                    on_change=set_selected,
                ),
            ]
        )

    client = TestClient(create_asgi_app(app))

    with client.websocket_connect("/events") as websocket:
        full = websocket.receive_json()
        control = _find_node_by_type(full["tree"], "DateRangePicker")
        assert control is not None

        websocket.send_json(
            {
                "type": "event",
                "event_id": control["props"]["change"],
                "data": {"value": {"start": "2026-04-01", "end": "2026-04-07"}},
            }
        )
        patch = websocket.receive_json()

    assert patch["type"] == "patch"
    text_patch = next(item for item in patch["patches"] if item["path"] == [0])
    assert text_patch["props"]["value"] == "2026-04-01->2026-04-07"


def test_chat_input_submit_payload_updates_state_and_rerenders():
    app = App()

    @app.page("/")
    def home():
        message, set_message = db.use_state("empty")
        return db.Column(
            [
                db.Text(message),
                db.ChatInput(on_submit=set_message),
            ]
        )

    client = TestClient(create_asgi_app(app))

    with client.websocket_connect("/events") as websocket:
        full = websocket.receive_json()
        control = _find_node_by_type(full["tree"], "ChatInput")
        assert control is not None

        websocket.send_json(
            {
                "type": "event",
                "event_id": control["props"]["submit"],
                "data": {"value": "show failed pipelines"},
            }
        )
        patch = websocket.receive_json()

    assert patch["type"] == "patch"
    text_patch = next(item for item in patch["patches"] if item["path"] == [0])
    assert text_patch["props"]["value"] == "show failed pipelines"


def test_checkbox_false_payload_updates_state_and_rerenders():
    app = App()

    @app.page("/")
    def home():
        enabled, set_enabled = db.use_state(True)
        return db.Column(
            [
                db.Text("enabled" if enabled else "disabled"),
                db.Checkbox(name="enabled", label="Enabled", checked=enabled, on_change=set_enabled),
            ]
        )

    client = TestClient(create_asgi_app(app))

    with client.websocket_connect("/events") as websocket:
        full = websocket.receive_json()
        control = _find_node_by_type(full["tree"], "Checkbox")
        assert control is not None

        websocket.send_json(
            {
                "type": "event",
                "event_id": control["props"]["change"],
                "data": {"value": False},
            }
        )
        patch = websocket.receive_json()

    assert patch["type"] == "patch"
    text_patch = next(item for item in patch["patches"] if item["path"] == [0])
    checkbox_patch = next(item for item in patch["patches"] if item["path"] == [1])
    assert text_patch["props"]["value"] == "disabled"
    assert checkbox_patch["props"]["checked"] is False


def test_input_empty_string_payload_updates_state_and_rerenders():
    app = App()

    @app.page("/")
    def home():
        query, set_query = db.use_state("seed")
        return db.Column(
            [
                db.Text(query or "empty"),
                db.Input(name="query", label="Query", value=query, on_change=set_query),
            ]
        )

    client = TestClient(create_asgi_app(app))

    with client.websocket_connect("/events") as websocket:
        full = websocket.receive_json()
        control = _find_node_by_type(full["tree"], "Input")
        assert control is not None

        websocket.send_json(
            {
                "type": "event",
                "event_id": control["props"]["change"],
                "data": {"value": ""},
            }
        )
        patch = websocket.receive_json()

    assert patch["type"] == "patch"
    text_patch = next(item for item in patch["patches"] if item["path"] == [0])
    input_patch = next(item for item in patch["patches"] if item["path"] == [1])
    assert text_patch["props"]["value"] == "empty"
    assert input_patch["props"]["value"] == ""


def test_websocket_serializes_local_media_paths_as_asset_urls():
    image_asset = Path("docs/assets/brickflowui-mark.svg").resolve()
    video_asset = Path("README.md").resolve()

    app = App()

    @app.page("/")
    def home():
        return db.Column(
            [
                db.Image(str(image_asset), alt="Preview"),
                db.Video(str(video_asset), caption="Demo"),
            ]
        )

    client = TestClient(create_asgi_app(app))

    with client.websocket_connect("/events") as websocket:
        payload = websocket.receive_json()

    assert payload["type"] == "full"
    image_node = _find_node_by_type(payload["tree"], "Image")
    video_node = _find_node_by_type(payload["tree"], "Video")
    assert image_node is not None
    assert video_node is not None
    assert str(image_node["props"]["src"]).startswith("/__brickflow_asset__/")
    assert str(video_node["props"]["src"]).startswith("/__brickflow_asset__/")


def test_embed_allowlist_rejects_unapproved_origins():
    app = App(allowed_embed_origins=["https://allowed.example.com"])

    with pytest.raises(ValueError, match="allowed_embed_origins"):
        app.transform_serialized_tree(
            {
                "type": "Embed",
                "props": {"src": "https://blocked.example.com/dashboard", "title": "Blocked"},
            }
        )


def test_pipeline_node_click_payload_updates_state_and_rerenders():
    app = App()

    @app.page("/")
    def home():
        selected, set_selected = db.use_state("none")

        def select_node(payload):
            set_selected(payload["id"])

        return db.Column(
            [
                db.Text(selected),
                db.PipelineGraph(
                    nodes=[{"id": "bronze", "label": "Bronze", "status": "running"}],
                    edges=[],
                    on_node_click=select_node,
                ),
            ]
        )

    client = TestClient(create_asgi_app(app))

    with client.websocket_connect("/events") as websocket:
        full = websocket.receive_json()
        control = _find_node_by_type(full["tree"], "PipelineGraph")
        assert control is not None

        websocket.send_json(
            {
                "type": "event",
                "event_id": control["props"]["nodeClick"],
                "data": {"value": {"id": "bronze", "status": "running"}},
            }
        )
        patch = websocket.receive_json()

    assert patch["type"] == "patch"
    text_patch = next(item for item in patch["patches"] if item["path"] == [0])
    assert text_patch["props"]["value"] == "bronze"


def test_websocket_sends_event_complete_for_non_dirty_handlers():
    app = App()
    touched = {"count": 0}

    @app.page("/")
    def home():
        return db.Button("Ping", on_click=lambda: touched.__setitem__("count", touched["count"] + 1))

    client = TestClient(create_asgi_app(app))

    with client.websocket_connect("/events") as websocket:
        full = websocket.receive_json()
        event_id = full["tree"]["props"]["click"]

        websocket.send_json(
            {
                "type": "event",
                "event_id": event_id,
                "data": {},
            }
        )
        completion = websocket.receive_json()

    assert touched["count"] == 1
    assert completion == {"type": "event_complete", "event_id": event_id}


def test_previous_render_event_handler_remains_valid_for_one_generation():
    app = App()

    @app.page("/")
    def home():
        count, set_count = db.use_state(0)
        status, set_status = db.use_state("idle")
        return db.Column(
            [
                db.Text(f"{status}:{count}"),
                db.Button("Advance", on_click=lambda: set_count(count + 1)),
                db.Button("Use queued event", on_click=lambda: set_status("accepted")),
            ]
        )

    client = TestClient(create_asgi_app(app))

    with client.websocket_connect("/events") as websocket:
        full = websocket.receive_json()
        old_advance_id = full["tree"]["children"][1]["props"]["click"]
        old_queued_id = full["tree"]["children"][2]["props"]["click"]

        websocket.send_json({"type": "event", "event_id": old_advance_id, "data": {}})
        first_patch = websocket.receive_json()
        websocket.receive_json()  # event_complete
        current_advance_id = next(
            patch["props"]["click"]
            for patch in first_patch["patches"]
            if patch["path"] == [1]
        )

        websocket.send_json({"type": "event", "event_id": old_queued_id, "data": {}})
        websocket.send_json({"type": "event", "event_id": current_advance_id, "data": {}})
        second_patch = websocket.receive_json()

    text_patch = next(patch for patch in second_patch["patches"] if patch["path"] == [0])
    assert text_patch["props"]["value"] == "accepted:1"


def test_websocket_disconnect_cleans_session_and_effects():
    app = App()
    cleaned = {"count": 0}

    @app.page("/")
    def home():
        db.use_effect(
            lambda: lambda: cleaned.__setitem__("count", cleaned["count"] + 1),
            [],
        )
        return db.Text("ready")

    client = TestClient(create_asgi_app(app))
    with client.websocket_connect("/events") as websocket:
        assert websocket.receive_json()["type"] == "full"
        assert len(app._sessions) == 1

    assert app._sessions == {}
    assert app._session_paths == {}
    assert cleaned["count"] == 1


def test_repeated_websocket_disconnects_do_not_grow_session_registries():
    app = App()
    app.mount(lambda: db.Text("ready"))
    client = TestClient(create_asgi_app(app))

    for _ in range(20):
        with client.websocket_connect("/events") as websocket:
            assert websocket.receive_json()["type"] == "full"

        assert app._sessions == {}
        assert app._session_paths == {}


def test_websocket_sessions_keep_state_independent():
    app = App()

    @app.page("/")
    def home():
        count, set_count = db.use_state(0)
        return db.Column(
            [
                db.Text(f"count:{count}"),
                db.Button("Increment", on_click=lambda: set_count(count + 1)),
            ]
        )

    client = TestClient(create_asgi_app(app))
    with client.websocket_connect("/events") as first:
        first_full = first.receive_json()
        first_button = _find_node_by_type(first_full["tree"], "Button")
        assert first_button is not None

        with client.websocket_connect("/events") as second:
            second_full = second.receive_json()
            second_button = _find_node_by_type(second_full["tree"], "Button")
            assert second_button is not None

            first.send_json(
                {"type": "event", "event_id": first_button["props"]["click"], "data": {}}
            )
            first_messages = [first.receive_json(), first.receive_json()]
            first_patch = next(message for message in first_messages if message["type"] == "patch")

            second.send_json(
                {"type": "event", "event_id": second_button["props"]["click"], "data": {}}
            )
            second_messages = [second.receive_json(), second.receive_json()]
            second_patch = next(message for message in second_messages if message["type"] == "patch")

    first_text = next(patch for patch in first_patch["patches"] if patch["path"] == [0])
    second_text = next(patch for patch in second_patch["patches"] if patch["path"] == [0])
    assert first_text["props"]["value"] == "count:1"
    assert second_text["props"]["value"] == "count:1"
    assert app._sessions == {}
    assert app._session_paths == {}


def test_concurrent_websocket_sessions_keep_principals_isolated():
    app = App(auth_mode="user", auth_provider=HeaderAuthProvider())

    @app.page("/", access="user")
    def home():
        principal = current_user()
        return db.Text(principal.subject if principal else "missing")

    asgi = create_asgi_app(app)

    def connect(subject: str) -> str:
        with TestClient(asgi) as client:
            with client.websocket_connect(
                "/events",
                headers={"x-brickflow-user-id": subject},
            ) as websocket:
                payload = websocket.receive_json()
                return payload["tree"]["props"]["value"]

    subjects = [f"user-{index}" for index in range(8)]
    with ThreadPoolExecutor(max_workers=8) as executor:
        rendered = list(executor.map(connect, subjects))

    assert sorted(rendered) == sorted(subjects)
    assert app._sessions == {}
    assert app._session_paths == {}
