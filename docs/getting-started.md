# Getting started

## Install the verified release

```powershell
python -m pip install agentmuru==0.2.0
muru doctor
```

Create a small application and run it:

```powershell
muru init hello-muru --name "Hello Muru"
cd hello-muru
muru run app:application
```

Open `http://127.0.0.1:8000`. The starter uses `FakeModel`, so it needs no provider
credentials. `muru doctor` verifies the Python runtime and bundled Workspace assets.

## Add a durable local store

The default application uses in-memory stores. For restart-safe sessions, compose the
application with SQLite:

```python
from pathlib import Path

from agentmuru import Agent, Application, FakeModel, Runtime, SQLitePersistence

persistence = SQLitePersistence(Path("agentmuru.db"))
application = Application(
    agent=Agent(
        name="assistant",
        instructions="Help the operator.",
        model=FakeModel.responses("Ready."),
    ),
    session_store=persistence.sessions,
    artifact_store=persistence.artifacts,
)
runtime = Runtime(application, approvals=persistence.approval_service())
```

SQLite is the verified default for one local Runtime process and modest write concurrency.
Read the [SQLite operator guide](guides/sqlite-persistence.md) before deploying it.

## Add a tool

```python
from agentmuru import tool

@tool(permission="catalog.read")
def lookup_table(name: str) -> dict[str, str]:
    return {"name": name, "owner": "data-platform"}
```

Grant `catalog.read` on the `Agent`. If a permission is declared but not granted, the
runtime blocks the call. Set `approval="required"` for actions that need a human decision.

## Contribute from source

Source installation is for contributors, not the primary product path:

```powershell
git clone https://github.com/AjayAJ2000/AgentMuru.git
cd AgentMuru
python -m pip install -e ".[dev,docs]"
python -m pytest -q
```

Continue with the [public API](reference/public-api.md) or
[server and Workspace operations](guides/server-and-workspace.md).
