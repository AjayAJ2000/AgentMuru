# Stable public API

The names below are exported by `agentmuru.__all__` in 0.2.0. Imports from internal
modules may change without the same compatibility promise.

## Application and execution

### `Agent`

`from agentmuru import Agent`

Defines a stable name, instructions, normalized model provider, tools, and granted
permissions. Duplicate tool names are rejected.

### `Application`

`from agentmuru import Application`

Groups the primary agent, handoff targets, metadata, and store protocols.

### `Runtime`

`from agentmuru import Runtime`

Owns active coroutines and exposes session creation, submit, wait, cancel, handoff,
approval, artifact, and event operations.

### `FakeModel`

`from agentmuru import FakeModel`

Deterministic local provider for tests and credential-free exploration. Use
`FakeModel.responses(...)`, `FakeModel.script(...)`, or `FakeModel.turns(...)`.

## Tools and artifacts

### `tool` and `Tool`

`from agentmuru import Tool, tool`

`@tool` derives JSON schema from a typed function and may declare permission, approval,
risk, side effects, retry, timeout, and sensitive arguments. `Tool` is its runtime form.

### `Artifact` and `ArtifactKind`

`from agentmuru import Artifact, ArtifactKind`

Addressable outputs. Durable content accepts text, bytes, or finite JSON values. Kinds are
markdown, code, JSON, table, chart, file, image, SQL, and report.

## Sessions, events, and persistence

### `Session`

`from agentmuru import Session`

Contains ordered messages, runs, events, JSON metadata, and ownership fields.

### `RuntimeEvent` and `EventType`

`from agentmuru import EventType, RuntimeEvent`

Events use per-session positive sequences, finite JSON payloads, and public dictionary
round trips.

### `InMemorySessionStore`

`from agentmuru import InMemorySessionStore`

Process-local implementation for tests and ephemeral examples.

### `SQLitePersistence`

```python
from agentmuru import SQLitePersistence
```

`SQLitePersistence(path, *, busy_timeout_ms=5000, max_retries=4,
poll_interval=0.05)` composes `.sessions`, `.artifacts`, `.approvals`, `.database`, and
`.approval_service()` around one standard-library SQLite file.

## Package metadata

### `__version__`

`from agentmuru import __version__`

AgentMuru 0.2 reports `0.2.0`.

## Minimal executable example

```python
import asyncio
from agentmuru import Agent, Application, FakeModel, Runtime

async def main() -> None:
    runtime = Runtime(Application(
        agent=Agent(name="assistant", instructions="", model=FakeModel.responses("Ready."))
    ))
    session = runtime.create_session()
    run = await runtime.submit(session.id, "hello")
    print((await runtime.wait(run.id)).status.value)

asyncio.run(main())
```
