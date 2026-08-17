# Configuration

AgentMuru keeps configuration close to the object that owns it. There is no global application
configuration file in the 0.3 MVP.

## Provider environment variables

| Provider | Variable | Extra |
| --- | --- | --- |
| OpenAI | `OPENAI_API_KEY` | `agentmuru[openai]` |
| Anthropic | `ANTHROPIC_API_KEY` | `agentmuru[anthropic]` |
| Google Gen AI | `GOOGLE_API_KEY` | `agentmuru[google]` |

Official SDKs read these variables when AgentMuru creates a client on the first model turn.
Constructors also accept explicit credentials or injected clients for an application-managed
secret and connection lifecycle.

## Agent settings

Put normalized provider request settings in `Agent.model_settings`:

```python
agent = Agent(
    name="assistant",
    instructions="Answer clearly.",
    model=OpenAIModel(),
    model_settings={
        "temperature": 0.2,
        "max_output_tokens": 600,
        "provider_options": {"service_tier": "auto"},
    },
)
```

Provider-specific option support follows the installed SDK and selected model. Reserved request
and connection fields cannot be overridden in `provider_options`.

## Runtime settings

Configure execution when constructing `Runtime`:

| Argument | Default | Purpose |
| --- | --- | --- |
| `policy` | `PermissionPolicy()` | Permission evaluation |
| `approvals` | `ApprovalService()` | Human decision store and waiters |
| `tracer` | `Tracer()` | Run spans and usage |
| `max_model_turns` | `24` | Bound tool and model loops |
| `approval_timeout` | `300.0` seconds | Expire unanswered approvals; `None` disables expiry |

## SQLite settings

`SQLitePersistence` accepts database path, busy timeout in milliseconds, bounded retry count,
and cross-instance event polling interval. See [SQLite persistence](../operations/sqlite.md).

## Server settings

`ServerSettings` owns:

- `allow_anonymous`
- `auth_provider`
- `trusted_hosts`
- `cors_origins`
- `websocket_origins`
- `max_message_chars`
- `frontend_dir`

Defaults are intended for local use. Configure every network and identity boundary explicitly in
a deployment.

## CLI reload variable

`muru dev` sets `AGENTMURU_APP` internally so the reload process can recreate the ASGI app. An
application normally should not set this variable itself.

## Databricks variables

The optional Databricks integration reads `DATABRICKS_HOST`, `DATABRICKS_WAREHOUSE_ID`,
`DATABRICKS_TOKEN`, `DATABRICKS_OAUTH_TOKEN`, `DATABRICKS_VOLUME_URI`, `DATABRICKS_APP_PORT`, and
`DATABRICKS_APP_NAME` as needed by the selected helper and identity path.
