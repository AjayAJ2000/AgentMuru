# Auth And Security

BrickflowUI now treats authentication, authorization, and browser-facing security as first-class framework concerns rather than ad hoc example code.

![Auth and route guard flow](assets/auth-guard-flow.png)

## Core Model

The framework separates three concerns:

1. `AuthProvider`: resolves identity from HTTP requests and WebSocket sessions.
2. Access levels: `public`, `authenticated`, `user`, or `app`.
3. Role checks: explicit role lists on pages and routes.

This keeps the browser as a renderer while the server remains authoritative for identity and access decisions.

## Supported Patterns

Use `auth_mode="app"` when the portal should always run as the application identity.

Use `auth_mode="user"` when pages or routes depend on signed-in user identity.

Use `auth_mode="hybrid"` when the app should fall back to an application identity but still honor user identity when it is present.

`HeaderAuthProvider` accepts both BrickflowUI's local-development headers and the native Databricks Apps headers: `X-Forwarded-User`, `X-Forwarded-Preferred-Username`, `X-Forwarded-Email`, and `X-Forwarded-Access-Token`. Access tokens are private principal credentials: they are excluded from representations and comparisons, never sent to the browser, and never stored in the shared app-identity connection.

Databricks SQL and SDK helpers follow the current identity automatically:

- user identity opens an operation-scoped connection/client using the forwarded token and closes the SQL connection after the operation;
- app identity uses Databricks unified authentication and a guarded reusable SQL connection;
- hybrid identity uses the user path when Databricks forwards a user identity, otherwise the app path.

## Route And Page Guards

```python
import brickflowui as db
from brickflowui.auth import HeaderAuthProvider

app = db.App(
    auth_mode="user",
    auth_provider=HeaderAuthProvider(),
)

@app.page("/ops", title="Operations", access="user", roles=["ops"])
def operations():
    return db.Text("Ops-only view")

@app.route("/api/audit", methods=["POST"], access="user", roles=["ops"])
async def write_audit():
    return {"status": "ok"}
```

## Browser Safety Defaults

The server applies:

- CSP headers
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: SAMEORIGIN`
- WebSocket origin checks
- optional trusted-host middleware
- browser-oriented CSRF checks for unsafe HTTP methods

## CSRF Protection

When `csrf_protection=True` on `App`, BrickflowUI issues a CSRF cookie for browser sessions and expects the matching `X-Brickflow-Csrf` header on unsafe HTTP form/API requests.

This is wired automatically for `db.Form(...)`.

Machine-to-machine clients are not forced into a browser-style CSRF flow unless they present browser-like session context.

## Role-Aware Navigation

Multi-page shells now filter navigation items using the current principal. A user only sees pages they are allowed to enter.

This avoids the awkward enterprise experience where a user sees links they cannot actually access.

## Audit Logging

Set `audit_events=True` on `App` when you want the runtime to log event execution metadata such as session id, principal, page path, and event id.

This is useful for regulated internal tools and debugging sensitive workflows.

## Embed Safety

Use `allowed_embed_origins=[...]` on `App` when you need to strictly control which remote iframe sources can appear in the portal.

```python
app = db.App(
    allowed_embed_origins=[
        "https://app.datadoghq.com",
        "https://lookerstudio.google.com",
    ]
)
```

## Recommended Enterprise Path

For a serious internal deployment:

1. choose `auth_mode="user"` or `auth_mode="hybrid"`
2. implement an `AuthProvider` that maps your platform identity to `Principal`
3. protect routes and pages with access levels and roles
4. keep `csrf_protection=True`
5. enable `audit_events=True` for sensitive workflows
6. allowlist external embeds explicitly when used
7. configure the minimum Databricks user-authorization scopes required by the app
