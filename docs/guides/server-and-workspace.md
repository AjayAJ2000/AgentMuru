# Run the server and Muru Workspace

`muru run module:application` starts FastAPI and serves the bundled React Workspace. The
browser remains a projection: models, tools, approvals, artifacts, and persistence stay in
Runtime.

## Start and inspect

```powershell
muru run app:application --host 127.0.0.1 --port 8000
```

`GET /health` returns product and protocol health. `GET /api/v1/app` returns application
metadata. Session endpoints create/list/read; run endpoints read/cancel; approval and
artifact endpoints record decisions and retrieve addressable outputs.

## Replay and reconnect

The WebSocket route is `/api/v1/sessions/{session_id}/stream?after=N`. It replays committed
events after `N`, then follows new events. Typed actions submit messages, cancel, decide
approvals, and ping. Unknown versions/actions return typed control errors.

Muru Workspace hydrates from a snapshot before connecting. It renders empty, streaming,
tool, approval, rejection, expiry, artifact, trace, cancellation, failure, reconnect, and
interrupted-process states. `process_interrupted` keeps history visible and prompts a new run.

## Authentication, ownership, and shutdown

Anonymous mode is for local exploration. For deployment, supply authentication, disable
anonymous access, and bind sessions to principals. HTTP and WebSocket routes verify
ownership. On shutdown, stop accepting traffic and finish or cancel work. Remaining
nonterminal runs become durable interrupted failures on the next start.
