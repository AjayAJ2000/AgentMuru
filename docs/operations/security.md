# Security

The default server permits anonymous local use. A network deployment must configure identity,
ownership, transport controls, data protection, and tool isolation explicitly.

## Configure the server boundary

```python
from agentmuru.server import BearerTokenAuth, Principal, ServerSettings, create_asgi_app

principal = Principal(subject="operator-1", authenticated=True, roles=("operator",))
settings = ServerSettings(
    allow_anonymous=False,
    auth_provider=BearerTokenAuth({secret_token: principal}),
    trusted_hosts=("agents.example.com",),
    cors_origins=("https://agents.example.com",),
    websocket_origins=("https://agents.example.com",),
    max_message_chars=20_000,
)
asgi = create_asgi_app(application, settings=settings)
```

`BearerTokenAuth` is a small deterministic provider for tests and private deployments. Implement
the `AuthProvider` protocol to integrate an application identity system. Do not hard-code tokens
in source as shown by the mapping shape above.

HTTP and WebSocket routes authorize session ownership. The server also sends content type,
referrer, content security, and frame-ancestor headers.

## Govern tools

- Grant only permissions required by one agent.
- Mark mutation and external-execution tools as side effects.
- Require approval for sensitive work.
- Mark secret arguments in `sensitive_fields`.
- Keep timeouts and retries finite.
- Run untrusted Python tools outside the runtime process with a separate identity and resource
  limits.

A model request cannot grant a permission or approve its own tool call.

## Protect data

Built-in SQLite is not encrypted. Use restricted database and backup paths plus encrypted
storage when data at rest requires protection. Keep credentials out of messages, events,
artifacts, approval reasons, traces, logs, and browser state.

## Deployment checklist

- Disable anonymous access.
- Validate tokens or sessions through a production identity provider.
- Set exact trusted hosts, CORS origins, and WebSocket origins.
- Terminate TLS at a maintained proxy or load balancer.
- Align proxy and AgentMuru payload limits.
- Store provider credentials in a managed secret system.
- Test rejection, approval expiry, cancellation, reconnect, backup restore, and process recovery.
- Review provider data-handling and retention settings for the selected account.
