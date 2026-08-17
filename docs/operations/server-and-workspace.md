# Server and Workspace

`muru run module:application` starts the AgentMuru FastAPI server and serves the bundled React
Workspace. The browser is a projection of runtime state. Models, tools, approvals, artifacts,
policy, and persistence remain in Python.

## Start the server

```powershell
muru run app:application --host 127.0.0.1 --port 8000
```

Use `muru dev` during local development when source reload is useful. Do not use reload mode for
a deployed process because it can interrupt active runs.

## Health and metadata

`GET /health` is unauthenticated and returns status, product, and protocol version. Use it for
process and load-balancer health checks.

`GET /api/v1/app` returns application title, agents, models, tools, protocol version, and current
principal details. It follows the configured authentication policy.

## HTTP routes

| Method | Route | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/sessions` | Create a session |
| `GET` | `/api/v1/sessions` | List sessions owned by the principal |
| `GET` | `/api/v1/sessions/{session_id}` | Hydrate messages, runs, artifacts, and approvals |
| `POST` | `/api/v1/sessions/{session_id}/messages` | Submit a message with optional idempotency key |
| `GET` | `/api/v1/sessions/{session_id}/events` | Replay events after a sequence |
| `GET` | `/api/v1/runs/{run_id}` | Read run state |
| `POST` | `/api/v1/runs/{run_id}/cancel` | Cancel an active run |
| `PATCH` | `/api/v1/approvals/{approval_id}` | Approve or reject a pending tool call |
| `GET` | `/api/v1/artifacts/{artifact_id}` | Read artifact metadata and content |
| `GET` | `/api/v1/runs/{run_id}/traces` | Read traces and usage |

## WebSocket replay

Connect to `/api/v1/sessions/{session_id}/stream?after=N`. The server first sends committed
events with a sequence greater than `N`, then follows new events.

Workspace actions submit messages, cancel runs, decide approvals, and ping the connection.
Unknown protocol versions or actions return typed control errors instead of silently dropping a
request.

## Limits

`ServerSettings.max_message_chars` defaults to 100,000. Proxy payload and connection limits must
not be higher than the application is prepared to parse and store. The browser is not a trusted
security boundary.

## Shutdown

Stop accepting traffic, then allow work to finish or cancel it deliberately. Any queued,
running, or approval-waiting SQLite run left by process loss becomes a `process_interrupted`
failure on the next runtime construction.
