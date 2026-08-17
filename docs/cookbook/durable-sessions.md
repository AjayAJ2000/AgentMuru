# Reopen durable sessions

The executable scenario is `examples.durable_agent`.

```powershell
python examples/durable_agent.py
```

The scenario creates a SQLite-backed application, completes one run, constructs a new runtime
over the same file, and verifies that the session, run, messages, and events reopen.

## Compose persistence

```python
from agentmuru import Application, Runtime, SQLitePersistence

persistence = SQLitePersistence("agentmuru.db")
application = Application(
    agent=agent,
    session_store=persistence.sessions,
    artifact_store=persistence.artifacts,
)
runtime = Runtime(application, approvals=persistence.approval_service())
```

Use the stores from the same `SQLitePersistence` object so sessions, artifacts, and approval
records share one database and schema lifecycle.

## Make submissions idempotent

```python
run = await runtime.submit(
    session.id,
    "persist this",
    idempotency_key="client-request-1842",
)
```

Retrying with the same key returns the bound run instead of creating another run.

## Reopen safely

Create a new persistence object and runtime after the first process is fully stopped. The
bundled SQLite profile is designed for one active AgentMuru runtime process per database file.
See [SQLite operations](../operations/sqlite.md) for locking, backups, and recovery.
