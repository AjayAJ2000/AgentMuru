# Secure a deployment

Configure an `AuthProvider`, set `allow_anonymous=False`, restrict trusted hosts, CORS
origins, and WebSocket origins, and terminate TLS at a trusted proxy. Application
authentication may use the bearer/static protocol or an application adapter. Authorize
every session, run, artifact, approval, and event action against its principal.

Grant only required tool permissions. Mark secret arguments sensitive. Require approval
for mutations and execution. Run untrusted Python tools outside the Runtime process. Keep
credentials out of events, messages, artifacts, approval reasons, logs, and browser state.

## Checklist

- Restrict the database path and backup path with operating-system permissions.
- Use encrypted volumes when data at rest needs encryption; built-in SQLite is not encrypted.
- Enforce AgentMuru and proxy payload limits.
- Keep trusted hosts and origins explicit; avoid wildcard production origins.
- Terminate TLS before HTTP or WebSocket traffic reaches an untrusted network.
- Rotate secrets through the deployment platform, not durable Runtime records.
- Sandbox untrusted tools with their own identity and resource limits.
- Exercise backup restoration and `process_interrupted` recovery before launch.
