"""
BrickflowUI App class — the main entry point for building apps.

Usage:
    import brickflowui as db

    app = db.App()

    @app.page("/", title="Home", icon="Home")
    def home():
        count, set_count = db.use_state(0)
        return db.Column([
            db.Text("Counter", variant="h2"),
            db.Text(f"Count: {count}"),
            db.Button("Increment", on_click=lambda: set_count(count + 1)),
        ])

    if __name__ == "__main__":
        app.run()
"""

import hashlib
import logging
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union, Tuple
from urllib.parse import quote, urlparse

from .auth import (
    AccessLevel,
    AuthProvider,
    AuthMode,
    AuthenticationRequired,
    AuthorizationError,
    Principal,
    authorize_principal,
    current_principal,
)
from .state import RenderContext
from .vdom import VNode
from .theme import Theme
from .version import __version__

logger = logging.getLogger("brickflowui.app")

_ASSET_PROP_KEYS = {
    "src",
    "poster",
    "logo",
    "favicon",
    "avatar",
    "image",
}


# ---------------------------------------------------------------------------
# Page descriptor
# ---------------------------------------------------------------------------


@dataclass
class Page:
    path: str
    title: str
    icon: Optional[str]
    render_fn: Callable[[], VNode]
    access: AccessLevel = "public"
    roles: Tuple[str, ...] = ()


@dataclass
class RouteSpec:
    path: str
    methods: List[str]
    handler: Callable
    access: AccessLevel = "public"
    roles: Tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# App class
# ---------------------------------------------------------------------------


class App:
    """
    The main BrickflowUI application.

    - Register pages via the @app.page() decorator or app.mount()
    - Add custom API routes via @app.route()
    - Start the dev/prod server via app.run()
    """

    def __init__(
        self,
        title: str = "BrickflowUI App",
        theme: Union[str, Path, Dict[str, Any], None] = None,
        theme_color: Optional[str] = None,
        logo: Optional[str] = None,
        favicon: Optional[str] = None,
        loading: Optional[Dict[str, Any]] = None,
        cors_origins: Optional[List[str]] = None,
        trusted_hosts: Optional[List[str]] = None,
        websocket_origins: Optional[List[str]] = None,
        enable_dev_docs: bool = False,
        auth_mode: AuthMode = "app",
        auth_provider: Optional[AuthProvider] = None,
        app_principal: Optional[Principal] = None,
        allow_anonymous: bool = True,
        csrf_protection: bool = True,
        audit_events: bool = False,
        allowed_embed_origins: Optional[List[str]] = None,
        asset_roots: Optional[List[Union[str, Path]]] = None,
        asset_registry_limit: int = 256,
    ):
        """Create a BrickflowUI app and normalize theme, auth, and loading state."""
        self.title = title
        self.theme = Theme(theme)
        if theme_color:
            self.theme.load({"colors": {"primary": theme_color}})
        if title == "BrickflowUI App":
            self.title = self.theme.branding_value("title", title)
        if asset_registry_limit <= 0:
            raise ValueError("asset_registry_limit must be greater than 0.")
        configured_roots = asset_roots if asset_roots is not None else [Path.cwd()]
        self.asset_roots = tuple(Path(root).expanduser().resolve() for root in configured_roots)
        self.asset_registry_limit = asset_registry_limit
        self._asset_registry: OrderedDict[str, Path] = OrderedDict()
        self.logo = self.resolve_asset_url(logo or self.theme.branding_value("logo"))
        self.favicon = self.resolve_asset_url(favicon or self.theme.branding_value("favicon"))
        self.brand_tagline = self.theme.branding_value("tagline")
        self.show_theme_toggle = bool(self.theme.branding_value("show_theme_toggle", True))
        self.default_theme_mode = self.theme.default_mode()
        self.style_preset = self.theme.style_preset()
        self.loading = self._normalize_loading_config(loading)
        self.cors_origins = list(cors_origins or [])
        self.trusted_hosts = list(trusted_hosts or [])
        self.websocket_origins = list(websocket_origins or [])
        self.enable_dev_docs = enable_dev_docs
        self.auth_mode = auth_mode
        self.auth_provider = auth_provider
        self.app_principal = app_principal
        self.allow_anonymous = allow_anonymous
        self.csrf_protection = csrf_protection
        self.audit_events = audit_events
        self.allowed_embed_origins = list(allowed_embed_origins or [])

        # Runtime registries:
        # - pages hold routed page metadata
        # - sessions hold hook state per connected client
        # - session_paths remember the active route for each session
        # - custom_routes keeps non-UI HTTP handlers alongside the websocket app

        # page path → Page
        self._pages: Dict[str, Page] = {}
        # session_id → RenderContext
        self._sessions: Dict[str, RenderContext] = {}
        # session_id → current page path
        self._session_paths: Dict[str, str] = {}
        # path → (methods, handler)
        self._custom_routes: Dict[str, RouteSpec] = {}

        # Simple root-mount shortcut (single-page apps)
        self._root_fn: Optional[Callable[[], VNode]] = None

    def _normalize_loading_config(self, loading: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge theme-level and app-level loading settings into one runtime payload."""
        theme_loading = self.theme.config.get("loading", {}) if isinstance(self.theme.config, dict) else {}
        merged = {
            "title": self.title,
            "message": "Connecting to runtime...",
            "subtitle": self.brand_tagline or "Preparing the workspace runtime.",
            "reconnecting_message": "Reconnecting...",
            "error_message": "Connection error - retrying...",
            "animation": "spinner",
            "text_only": False,
            **(theme_loading if isinstance(theme_loading, dict) else {}),
            **(loading or {}),
        }

        merged["modes"] = self._normalize_loading_modes(merged.get("light"), merged.get("dark"))
        merged.pop("light", None)
        merged.pop("dark", None)
        self._normalize_loading_media(merged)
        return merged

    def _normalize_loading_modes(self, light: Any, dark: Any) -> Dict[str, Dict[str, Any]]:
        """Normalize light and dark loading overrides after alias resolution."""
        modes: Dict[str, Dict[str, Any]] = {}
        if isinstance(light, dict):
            payload = dict(light)
            self._normalize_loading_media(payload)
            modes["light"] = payload
        if isinstance(dark, dict):
            payload = dict(dark)
            self._normalize_loading_media(payload)
            modes["dark"] = payload
        return modes

    def _normalize_loading_media(self, payload: Dict[str, Any]) -> None:
        """Resolve loading media into stable app-served URLs when local files are used."""
        asset = payload.get("asset") or payload.get("logo") or payload.get("image")
        video = payload.get("video")
        if video:
            payload["video"] = self.resolve_asset_url(video)
            payload["asset"] = None
            payload["asset_kind"] = "video"
        elif asset:
            payload["asset"] = self.resolve_asset_url(asset)
            payload["asset_kind"] = self._asset_kind(asset)
        else:
            payload["asset"] = None
            payload["asset_kind"] = None

    def _asset_kind(self, value: Any) -> str:
        """Infer whether an asset should render as an image or video."""
        suffix = Path(str(value)).suffix.lower()
        if suffix in {".mp4", ".webm", ".ogg", ".mov"}:
            return "video"
        return "image"

    def _coerce_asset_path(self, value: Any) -> Optional[Path]:
        """Return an on-disk file path only when the value points to a real local asset."""
        if value is None or isinstance(value, bool):
            return None

        raw = str(value).strip()
        if not raw:
            return None

        lowered = raw.lower()
        if lowered.startswith(("http://", "https://", "data:", "blob:", "/assets/", "/__brickflow_asset__/")):
            return None

        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        path = path.resolve()
        if not path.exists() or not path.is_file() or not self._is_allowed_asset_path(path):
            return None
        return path

    def _is_allowed_asset_path(self, path: Path) -> bool:
        """Return whether a resolved local file stays beneath an approved root."""
        return any(path == root or root in path.parents for root in self.asset_roots)

    def resolve_asset_url(self, value: Any) -> Any:
        """Convert local assets into stable app URLs and leave remote values untouched."""
        asset_path = self._coerce_asset_path(value)
        if asset_path is None:
            return value

        digest = hashlib.sha1(str(asset_path).encode("utf-8")).hexdigest()[:12]
        self._asset_registry[digest] = asset_path
        self._asset_registry.move_to_end(digest)
        while len(self._asset_registry) > self.asset_registry_limit:
            self._asset_registry.popitem(last=False)
        return f"/__brickflow_asset__/{digest}/{quote(asset_path.name)}"

    def asset_url(self, value: Any) -> Any:
        """Return a browser-safe URL for a local asset path, or the original value for remote URLs."""
        return self.resolve_asset_url(value)

    def get_registered_asset(self, asset_id: str) -> Optional[Path]:
        """Return the local asset path previously registered for a public asset URL."""
        path = self._asset_registry.get(asset_id)
        if path is None:
            return None
        resolved = path.resolve()
        if not resolved.exists() or not resolved.is_file() or not self._is_allowed_asset_path(resolved):
            self._asset_registry.pop(asset_id, None)
            return None
        self._asset_registry.move_to_end(asset_id)
        return resolved

    def transform_serialized_tree(self, payload: Any) -> Any:
        """Rewrite local media paths inside serialized VDOM payloads before shipping them."""
        if isinstance(payload, dict):
            if payload.get("type") == "Embed":
                self._validate_embed_payload(payload)
            transformed = {}
            for key, value in payload.items():
                if key in _ASSET_PROP_KEYS:
                    transformed[key] = self.resolve_asset_url(value)
                else:
                    transformed[key] = self.transform_serialized_tree(value)
            return transformed

        if isinstance(payload, list):
            return [self.transform_serialized_tree(item) for item in payload]

        return payload

    def _validate_embed_payload(self, payload: Dict[str, Any]) -> None:
        """Enforce external embed allowlists when the app opts into them."""
        if not self.allowed_embed_origins:
            return

        props = payload.get("props", {})
        src = props.get("src")
        if not isinstance(src, str):
            return

        parsed = urlparse(src)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Embed sources must be absolute HTTP(S) URLs when allowlists are enabled.")

        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin.rstrip("/") not in {item.rstrip("/") for item in self.allowed_embed_origins}:
            raise ValueError(f"Embed origin '{origin}' is not in the allowed_embed_origins list.")

    def loading_bootstrap(self) -> Dict[str, Any]:
        """Serialize the loading contract consumed by the frontend bootstrap."""
        return {
            "title": self.loading.get("title") or self.title,
            "message": self.loading.get("message") or "Connecting to runtime...",
            "subtitle": self.loading.get("subtitle") or self.brand_tagline,
            "reconnectingMessage": self.loading.get("reconnecting_message") or "Reconnecting...",
            "errorMessage": self.loading.get("error_message") or "Connection error - retrying...",
            "animation": self.loading.get("animation") or "spinner",
            "textOnly": bool(self.loading.get("text_only")),
            "asset": self.loading.get("asset"),
            "assetKind": self.loading.get("asset_kind"),
            "video": self.loading.get("video"),
            "themeMode": self.default_theme_mode,
            "modes": self.loading.get("modes") or {},
            "stylePreset": self.style_preset,
        }

    def _invalidate_server(self) -> None:
        """Drop the cached ASGI app when runtime routes or pages change."""
        if hasattr(self, "_fastapi_app"):
            delattr(self, "_fastapi_app")

    # ── Page registration ────────────────────────────────────────────────

    def page(
        self,
        path: str,
        title: str = "",
        icon: Optional[str] = None,
        access: AccessLevel = "public",
        roles: Optional[List[str]] = None,
    ) -> Callable:
        """Register a page-rendering function under a path and optional access policy."""
        def decorator(fn: Callable[[], VNode]) -> Callable[[], VNode]:
            self._pages[path] = Page(
                path=path,
                title=title or fn.__name__.replace("_", " ").title(),
                icon=icon,
                render_fn=fn,
                access=access,
                roles=tuple(roles or ()),
            )
            # The first "/" page doubles as the root renderer for simple apps.
            if not self._root_fn and path == "/":
                self._root_fn = fn
            self._invalidate_server()
            return fn
        return decorator

    def mount(self, component: Callable[[], VNode]) -> None:
        """Mount a single root component for apps that do not need explicit routes."""
        self._root_fn = component
        self._pages["/"] = Page(path="/", title=self.title, icon=None, render_fn=component)
        self._invalidate_server()

    # ── Custom routes ────────────────────────────────────────────────────

    def route(
        self,
        path: str,
        methods: Optional[List[str]] = None,
        access: AccessLevel = "public",
        roles: Optional[List[str]] = None,
    ) -> Callable:
        """Register a custom HTTP route alongside the BrickflowUI websocket runtime."""
        if methods is None:
            methods = ["GET"]

        def decorator(fn: Callable) -> Callable:
            self._custom_routes[path] = RouteSpec(
                path=path,
                methods=methods,
                handler=fn,
                access=access,
                roles=tuple(roles or ()),
            )
            self._invalidate_server()
            return fn
        return decorator

    # ── Rendering ────────────────────────────────────────────────────────

    def _render(self, session_id: str) -> VNode:
        """Render the current page for a session."""
        ctx = self._sessions.get(session_id)
        if ctx is None:
            raise RuntimeError(f"No session context for {session_id}")

        path = self._session_paths.get(session_id, "/")
        page = self._pages.get(path)

        if page is None and self._root_fn is not None:
            # Fallback: use root fn
            return self._root_fn()

        if page is None:
            from .components import Column, Text, Alert
            return Column([
                Text("404 – Page Not Found", variant="h2"),
                Alert(f"No page registered for path: {path}", type="error"),
            ])

        try:
            authorize_principal(current_principal(), access=page.access, roles=page.roles)
        except (AuthenticationRequired, AuthorizationError) as exc:
            return self._render_access_denied(exc)

        # Wrap with app shell if multiple pages
        if len(self._pages) > 1:
            return self._render_with_shell(session_id, page)

        return page.render_fn()

    def _render_access_denied(self, exc: Exception) -> VNode:
        """Render a consistent auth/access failure state inside the current app shell."""
        from .components import Alert, Column, Text

        title = "Sign In Required" if isinstance(exc, AuthenticationRequired) else "Access Denied"
        return Column(
            [
                Text(title, variant="h2"),
                Alert(str(exc), type="error"),
            ],
            padding=6,
            gap=4,
        )

    def _render_with_shell(self, session_id: str, current_page: Page) -> VNode:
        """Wrap routed pages in the shared navigation shell."""
        from .components import Column, Row, Sidebar, NavItem

        principal = current_principal()

        nav_items = [
            NavItem(label=p.title, path=p.path, icon=p.icon)
            for p in self._pages.values()
            if self._page_is_visible(principal, p)
        ]

        return Row(
            children=[
                Sidebar(
                    items=nav_items,
                    brand_name=self.title,
                    tagline=self.brand_tagline,
                    logo=self.logo,
                    show_theme_toggle=self.show_theme_toggle,
                ),
                Column(
                    children=[current_page.render_fn()],
                    padding=6,
                    style={"flex": "1", "minHeight": "100vh", "overflowY": "auto"},
                ),
            ],
            gap=0,
            align="stretch",
            style={"minHeight": "100vh", "width": "100%"},
        )

    def _page_is_visible(self, principal: Principal, page: Page) -> bool:
        """Return True when the current principal can see a page in the navigation shell."""
        try:
            authorize_principal(principal, access=page.access, roles=page.roles)
            return True
        except (AuthenticationRequired, AuthorizationError):
            return False

    def _navigate(self, session_id: str, path: str) -> None:
        """Handle page navigation for a session."""
        self._session_paths[session_id] = path
        ctx = self._sessions.get(session_id)
        if ctx:
            # Routed navigation swaps component trees, so session-scoped hook state resets here.
            ctx.cleanup_effects()
            ctx.state_slots = []
            ctx.memo_slots = []
            ctx.mark_dirty()

    # ── Server ────────────────────────────────────────────────────────────

    @property
    def server(self):
        """
        Access the lazily-created FastAPI app that powers the BrickflowUI runtime.
        """
        if not hasattr(self, "_fastapi_app"):
            from .server import create_asgi_app
            self._fastapi_app = create_asgi_app(self)
        return self._fastapi_app

    def run(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        reload: bool = False,
    ) -> None:
        """Resolve the runtime host/port and start the ASGI server."""
        from .databricks.env import resolve_host_port
        from .server import run_server

        host, port = resolve_host_port(host, port)
        logger.info(f"BrickflowUI v{__version__} — starting on http://{host}:{port}")
        logger.info(f"Pages: {list(self._pages.keys())}")

        if not self._pages and self._root_fn is None:
            raise RuntimeError("No pages or root component registered. Use @app.page() or app.mount().")

        run_server(self, host=host, port=port, reload=reload)
