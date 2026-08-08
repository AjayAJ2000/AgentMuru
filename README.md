# AgentMuru

AgentMuru is a Python-native runtime and workspace for building observable,
human-governed AI applications. Agents, tools, events, sessions, approvals,
artifacts, workflows, and traces are the application. Muru Workspace is their UI.

```python
from agentmuru import Agent, Application, FakeModel, tool

@tool(permission="customer.read")
def lookup_customer(customer_id: str) -> dict[str, str]:
    return {"customer_id": customer_id, "status": "active"}

agent = Agent(
    name="customer-intelligence",
    instructions="Investigate customer questions using approved tools.",
    model=FakeModel.responses("The customer is active."),
    tools=(lookup_customer,),
    permissions=frozenset({"customer.read"}),
)

application = Application(agent=agent, title="Customer Intelligence")

if __name__ == "__main__":
    application.run()
```

Open `http://127.0.0.1:8000` to use Muru Workspace.

## Why AgentMuru

- Provider-neutral streaming model interface with a deterministic fake provider.
- Typed, ordered runtime events with replay and reconnect cursors.
- Explicit sessions, messages, runs, artifacts, approvals, usage, and traces.
- Type-derived tools with permissions, risk, timeout, retries, and redaction.
- Resumable human approval before dangerous tool execution.
- Deterministic workflows and typed agent handoffs without orchestration theater.
- FastAPI HTTP/WebSocket protocol and a purpose-built React workspace.
- Optional Databricks adapters without Databricks coupling in the runtime core.

## Install and run

```powershell
python -m pip install -e ".[dev,docs]"
muru doctor
muru run examples.hello_agent:application
```

Create a project:

```powershell
muru init my-agent --name "My Agent"
cd my-agent
muru dev app:application
```

## Runtime flow

```text
User objective
  -> AgentMuru Runtime
  -> model stream / tool request
  -> permission and optional approval
  -> tool result / artifact
  -> ordered events and trace
  -> Muru Workspace projection
```

## Security defaults

Tool permissions are deny-by-default when a capability is declared but not granted.
High-risk and explicitly gated tools pause before execution. Sensitive arguments are
redacted from public events. The server enforces session ownership, payload limits,
trusted hosts, optional origin allowlists, and safe error payloads. Application owners
remain responsible for provider credentials, durable store encryption, deployment auth,
and sandboxing untrusted tool code.

## Commands

```powershell
python -m pytest -q
python -m ruff check agentmuru tests
python -m mypy agentmuru
cd frontend
npm test -- --run
npm run typecheck
npm run lint
npm run build
```

See the [getting started guide](docs/getting-started.md),
[architecture](docs/architecture/target-state.md), and
[migration guide](docs/migration-from-legacy-ui.md).

## Status

AgentMuru is an alpha release. The in-memory stores and `FakeModel` are complete local
implementations. Durable stores, production model providers, MCP clients, and remote
workflow workers are extension interfaces until concrete adapters are added and verified.

License: MIT.
