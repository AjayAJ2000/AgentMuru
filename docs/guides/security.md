# Secure a deployment

Configure an `AuthProvider`, set `allow_anonymous=False`, restrict trusted hosts and
WebSocket origins, and terminate TLS at a trusted proxy. Authorize every session, run,
artifact, and approval action against the principal.

Grant agents only the tool permissions they require. Mark secret arguments as sensitive.
Require approval for mutations and execution. Run untrusted Python tools outside the
runtime process. Encrypt durable stores and keep provider credentials out of events,
messages, artifacts, logs, and browser state.
