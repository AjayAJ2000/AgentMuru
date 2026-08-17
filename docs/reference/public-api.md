# Public Python API

The package root exports the stable 0.3 application primitives. Provider, server, approval,
workflow, and lower-level model contracts live in their named public modules.

## Package exports

```python
from agentmuru import (
    Agent,
    Application,
    Artifact,
    ArtifactKind,
    EventType,
    FakeModel,
    InMemorySessionStore,
    Runtime,
    RuntimeEvent,
    SQLitePersistence,
    Session,
    Tool,
    __version__,
    tool,
)
```

`agentmuru.__all__` contains `Agent`, `Application`, `Artifact`, `ArtifactKind`, `EventType`,
`FakeModel`, `InMemorySessionStore`, `RuntimeEvent`, `Runtime`, `SQLitePersistence`, `Session`,
`Tool`, `__version__`, and `tool`.

## `Agent`

```python
Agent(
    name: str,
    instructions: str,
    model: ModelProvider,
    description: str = "",
    tools: tuple[Tool, ...] = (),
    permissions: frozenset[str] = frozenset(),
    model_settings: Mapping[str, Any] = {},
    metadata: Mapping[str, Any] = {},
)
```

Agent names must be non-empty. Tool names must be unique inside one agent. `agent.tool(name)`
returns the declared tool or raises `KeyError`.

## `Application`

```python
Application(
    agent: Agent,
    agents: tuple[Agent, ...] = (),
    title: str = "AgentMuru",
    description: str = "A governed AI application",
    session_store: SessionStore = InMemorySessionStore(),
    artifact_store: ArtifactStore = InMemoryArtifactStore(),
    metadata: Mapping[str, Any] = {},
)
```

The primary and secondary agent names must be unique. `get_agent(name)` resolves any declared
agent. `run(host="127.0.0.1", port=8000)` starts the bundled server.

## `Runtime`

`Runtime(application, *, policy=None, approvals=None, tracer=None, max_model_turns=24,
approval_timeout=300.0)` coordinates execution.

Important methods:

| Method | Result |
| --- | --- |
| `create_session(user_id=None, title=None)` | Create and emit `session.started` |
| `await submit(session_id, content, idempotency_key=None)` | Persist a message and queue one run |
| `await wait(run_id)` | Wait for terminal run state |
| `await cancel(run_id)` | Cancel an active run |
| `await wait_for_approval(run_id)` | Wait until the run pauses for approval |
| `await decide_approval(approval_id, decision, actor, reason=None)` | Record the human decision |
| `await handoff(from_run_id, to_agent, reason)` | Create a run for another declared agent |
| `create_artifact(...)` | Persist an artifact and emit its event |

## `tool` and `Tool`

`@tool` derives a provider schema from Python type hints. Keyword options include `name`,
`description`, `permission`, `approval`, `risk`, `timeout`, `retries`, `side_effects`, and
`sensitive_fields`.

`Tool.provider_schema()` returns the normalized model-facing schema. `redact_arguments()` masks
sensitive fields. `await invoke(arguments)` validates, coerces, times, retries, and invokes the
handler.

## Sessions

`Session` contains ID, UTC timestamps, optional owner and title, metadata, messages, runs, and
events. `InMemorySessionStore` implements the complete `SessionStore` contract for one process.

Messages and store protocols are available from `agentmuru.sessions`:

```python
from agentmuru.sessions import AssistantToolCall, Message, MessageRole, RunRecord, RunStatus
```

## Stores

`SQLitePersistence(path, *, busy_timeout_ms=5000, max_retries=4, poll_interval=0.05)` exposes:

- `sessions`, a `SQLiteSessionStore`;
- `artifacts`, a `SQLiteArtifactStore`;
- `approvals`, a `SQLiteApprovalStore`;
- `approval_service()`, an `ApprovalService` over that approval store.

Store protocols are public from `agentmuru.sessions`, `agentmuru.artifacts`, and
`agentmuru.approvals`. A custom session store must implement explicit message and run mutation,
idempotency, recovery, ordered event append, and async subscription.

## Model events

```python
from agentmuru.models import (
    ModelCapabilities,
    ModelCompleted,
    ModelFailed,
    ModelProvider,
    ModelRequest,
    TextDelta,
    ToolCall,
    Usage,
)
```

See the [provider contract](providers.md) before implementing `ModelProvider`.

## Approvals and server

Approval types are public from `agentmuru.approvals`. Server types are public from
`agentmuru.server`, including `ServerSettings`, `Principal`, `AuthProvider`, `BearerTokenAuth`,
`StaticAuthProvider`, and `create_asgi_app`.

## Workflows

```python
from agentmuru.workflows import Step, StepResult, Workflow, WorkflowResult, WorkflowRunner
```

Workflow handlers receive a state dictionary and return `StepResult` or a value accepted by the
runner. Each completed step produces a checkpoint.
