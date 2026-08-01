"""
BrickflowUI Auth Portal Demo.

Run locally:
    python app.py

This example demonstrates:
- hybrid auth mode (user or shared app identity)
- page-level access control
- role-based access checks
- cookie-backed local sign-in for browser testing
"""

from __future__ import annotations

from pathlib import Path

from fastapi import Request, WebSocket
from fastapi.responses import JSONResponse

import brickflowui as db

APP_DIR = Path(__file__).parent


class DemoCookieAuthProvider:
    """Simple local demo auth provider backed by browser cookies."""

    USER_COOKIE = "bf_demo_user"
    ROLES_COOKIE = "bf_demo_roles"

    def _principal_from_mapping(self, values) -> db.Principal | None:
        subject = values.get(self.USER_COOKIE)
        if not subject:
            return None

        roles_raw = values.get(self.ROLES_COOKIE, "")
        roles = tuple(role.strip() for role in roles_raw.split(",") if role.strip())
        title_map = {
            "viewer": "Viewer",
            "analyst": "Analyst",
            "admin": "Administrator",
        }

        return db.Principal(
            subject=subject,
            principal_type="user",
            display_name=title_map.get(subject, subject.title()),
            email=f"{subject}@example.local",
            roles=roles,
            authenticated=True,
            attributes={"source": "demo-cookie"},
        )

    def authenticate_request(self, request: Request) -> db.Principal | None:
        return self._principal_from_mapping(request.cookies)

    def authenticate_websocket(self, websocket: WebSocket) -> db.Principal | None:
        return self._principal_from_mapping(websocket.cookies)


app = db.App(
    theme=APP_DIR / "theme.yaml",
    auth_mode="hybrid",
    auth_provider=DemoCookieAuthProvider(),
    allow_anonymous=True,
)


def _metric_card(label: str, value: str, delta: str, delta_type: str, icon: str) -> db.VNode:
    return db.Card(
        [db.Stat(label=label, value=value, delta=delta, delta_type=delta_type, icon=icon)],
        bordered=True,
    )


def _current_identity_banner() -> db.VNode:
    principal = db.current_principal()
    if principal.principal_type == "user":
        role_text = ", ".join(principal.roles) if principal.roles else "no roles"
        message = f"Signed in as {principal.display_name or principal.subject} ({role_text})"
        tone = "success"
        badge = db.Badge("User Identity", color="green")
    else:
        message = "Running as the shared application identity. Protected user pages will ask you to sign in."
        tone = "info"
        badge = db.Badge("App Identity", color="orange")

    return db.Card(
        [
            db.Row(
                [
                    db.Column(
                        [
                            db.Text("Current Execution Context", variant="h3"),
                            db.Text(message, muted=True),
                        ]
                    ),
                    badge,
                ],
                justify="between",
            ),
            db.Spacer(2),
            db.Alert(
                "Hybrid mode lets the same BrickflowUI portal support user-level access and shared service-principal behavior."
                if principal.principal_type == "user"
                else "This is the fallback mode teams can use for shared operational dashboards or controlled service workflows.",
                type=tone,
            ),
        ],
        bordered=True,
    )


def _login_forms() -> db.VNode:
    return db.Grid(
        [
            db.Card(
                [
                    db.Text("Viewer", variant="h3"),
                    db.Text("Can access signed-in workspace pages and personal dashboards.", muted=True),
                    db.Spacer(2),
                    db.Form(
                        action="/api/demo-login/viewer",
                        method="POST",
                        success_redirect="/workspace",
                        reload_on_success=True,
                        children=[db.Button("Sign in as Viewer", html_type="submit")],
                    ),
                ],
                bordered=True,
            ),
            db.Card(
                [
                    db.Text("Analyst", variant="h3"),
                    db.Text("Can access analyst workspaces and operational reporting tools.", muted=True),
                    db.Spacer(2),
                    db.Form(
                        action="/api/demo-login/analyst",
                        method="POST",
                        success_redirect="/workspace",
                        reload_on_success=True,
                        children=[db.Button("Sign in as Analyst", html_type="submit")],
                    ),
                ],
                bordered=True,
            ),
            db.Card(
                [
                    db.Text("Admin", variant="h3"),
                    db.Text("Gets admin-only routes plus the regular user workspace.", muted=True),
                    db.Spacer(2),
                    db.Form(
                        action="/api/demo-login/admin",
                        method="POST",
                        success_redirect="/admin",
                        reload_on_success=True,
                        children=[db.Button("Sign in as Admin", html_type="submit")],
                    ),
                ],
                bordered=True,
            ),
        ],
        cols=3,
        gap=4,
    )


def _logout_form() -> db.VNode:
    return db.Form(
        action="/api/demo-logout",
        method="POST",
        success_redirect="/",
        reload_on_success=True,
        children=[db.Button("Sign out", html_type="submit", variant="secondary")],
    )


@app.page("/", title="Home", icon="Home")
def home_page():
    principal = db.current_principal()
    signed_in = principal.principal_type == "user"

    return db.Column(
        [
            db.Text("BrickflowUI Access Portal", variant="h1"),
            db.Text(
                "A branded test portal for hybrid auth, role checks, and multi-page access control.",
                muted=True,
            ),
            db.Divider(),
            _current_identity_banner(),
            db.Grid(
                [
                    _metric_card("Auth Mode", app.auth_mode.title(), "+ secure", "increase", "Lock"),
                    _metric_card("Pages", "4", "portal-ready", "increase", "LayoutDashboard"),
                    _metric_card("Protected APIs", "3", "guarded", "increase", "Activity"),
                ],
                cols=3,
                gap=4,
            ),
            db.Card(
                [
                    db.Text("Security UI Theme Check", variant="h3"),
                    db.Text("1. Confirm the configured accent appears consistently across security actions and status highlights.", muted=True),
                    db.Text("2. Verify the app title in the browser tab is 'BrickflowUI Access Portal'.", muted=True),
                    db.Text("3. Check the lighter neutral background and white card surfaces feel clean and clinical.", muted=True),
                    db.Spacer(2),
                    db.Text("Access Flow", variant="h3"),
                    db.Text("1. Open the app signed out and explore the public pages.", muted=True),
                    db.Text("2. Sign in as Viewer or Analyst and open the workspace page.", muted=True),
                    db.Text("3. Sign in as Admin and verify the admin page unlocks.", muted=True),
                    db.Text("4. Sign out and confirm the app-only page still works while user pages are blocked.", muted=True),
                ],
                bordered=True,
            ),
            *([_logout_form()] if signed_in else [_login_forms()]),
        ],
        padding=6,
        gap=6,
    )


@app.page("/workspace", title="Workspace", icon="Database", access="user")
def workspace_page():
    user = db.require_auth()

    return db.Column(
        [
            db.Text("User Workspace", variant="h1"),
            db.Text(
                f"Welcome {user.display_name or user.subject}. This page requires a signed-in user identity.",
                muted=True,
            ),
            db.Divider(),
            db.Grid(
                [
                    _metric_card("Principal", user.subject, "active", "increase", "User"),
                    _metric_card("Roles", str(len(user.roles) or 1), "mapped", "increase", "Hash"),
                    _metric_card("Mode", "User", "isolated", "increase", "Lock"),
                ],
                cols=3,
                gap=4,
            ),
            db.Card(
                [
                    db.Text("Role Summary", variant="h3"),
                    db.Badge(", ".join(user.roles) if user.roles else "viewer", color="blue"),
                    db.Spacer(2),
                    db.Text(
                        "In a real Databricks app, this is where user-specific dashboards, analytics views, or profile-scoped data would load.",
                        muted=True,
                    ),
                ],
                bordered=True,
            ),
            _logout_form(),
        ],
        padding=6,
        gap=6,
    )


@app.page("/admin", title="Admin", icon="Settings", access="user", roles=["admin"])
def admin_page():
    admin = db.require_role("admin")

    return db.Column(
        [
            db.Text("Admin Console", variant="h1"),
            db.Text(
                f"Only users with the admin role can reach this page. Current admin: {admin.subject}",
                muted=True,
            ),
            db.Divider(),
            db.Grid(
                [
                    _metric_card("Policy Checks", "12", "+3", "increase", "Shield"),
                    _metric_card("Active Sessions", "48", "steady", "neutral", "Users"),
                    _metric_card("Audit Alerts", "0", "healthy", "decrease", "Activity"),
                ],
                cols=3,
                gap=4,
            ),
            db.Card(
                [
                    db.Text("Admin Notes", variant="h3"),
                    db.Text(
                        "This is the kind of page that should stay role-protected even when the app itself supports shared service-principal operations.",
                        muted=True,
                    ),
                ],
                bordered=True,
            ),
            _logout_form(),
        ],
        padding=6,
        gap=6,
    )


@app.page("/app-ops", title="App Ops", icon="Server", access="app")
def app_ops_page():
    principal = db.current_principal()

    return db.Column(
        [
            db.Text("Shared App Operations", variant="h1"),
            db.Text(
                "This page is intentionally reserved for the shared application identity.",
                muted=True,
            ),
            db.Divider(),
            db.Alert(
                f"Current principal: {principal.subject} ({principal.principal_type})",
                type="info",
            ),
            db.Card(
                [
                    db.Text("Why This Matters", variant="h3"),
                    db.Text(
                        "Some operational tasks should run under a shared service identity instead of a signed-in user, especially for controlled background actions or central dashboards.",
                        muted=True,
                    ),
                ],
                bordered=True,
            ),
        ],
        padding=6,
        gap=6,
    )


@app.route("/api/demo-login/viewer", methods=["POST"])
async def login_viewer():
    response = JSONResponse({"status": "ok", "user": "viewer"})
    response.set_cookie("bf_demo_user", "viewer", httponly=True, samesite="lax")
    response.set_cookie("bf_demo_roles", "viewer", httponly=True, samesite="lax")
    return response


@app.route("/api/demo-login/analyst", methods=["POST"])
async def login_analyst():
    response = JSONResponse({"status": "ok", "user": "analyst"})
    response.set_cookie("bf_demo_user", "analyst", httponly=True, samesite="lax")
    response.set_cookie("bf_demo_roles", "viewer,analyst", httponly=True, samesite="lax")
    return response


@app.route("/api/demo-login/admin", methods=["POST"])
async def login_admin():
    response = JSONResponse({"status": "ok", "user": "admin"})
    response.set_cookie("bf_demo_user", "admin", httponly=True, samesite="lax")
    response.set_cookie("bf_demo_roles", "viewer,analyst,admin", httponly=True, samesite="lax")
    return response


@app.route("/api/demo-logout", methods=["POST"])
async def logout():
    response = JSONResponse({"status": "ok"})
    response.delete_cookie("bf_demo_user")
    response.delete_cookie("bf_demo_roles")
    return response


@app.route("/api/whoami", methods=["GET"], access="authenticated")
async def whoami(request: Request):
    principal = request.state.brickflow_principal
    return {
        "subject": principal.subject,
        "principal_type": principal.principal_type,
        "roles": list(principal.roles),
        "authenticated": principal.authenticated,
    }


if __name__ == "__main__":
    app.run()
