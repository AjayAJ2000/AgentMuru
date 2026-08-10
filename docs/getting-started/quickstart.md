# Build your first local agent

Create and run an AgentMuru application in about five minutes. The generated starter uses
`FakeModel`, so this path does not require provider credentials or a network call after
installation.

## Prerequisites

- complete [installation](installation.md);
- confirm that `muru doctor` passes;
- choose a directory where AgentMuru can create a project folder.

## Create the application

```powershell
muru init hello-muru --name "Hello Muru"
cd hello-muru
```

The scaffold creates an `app.py` module with an `application` object that the AgentMuru
server can load.

## Run the application

```powershell
muru run app:application
```

Open `http://127.0.0.1:8000` in a browser.

## What you should see

Muru Workspace loads the starter application and projects its runtime state in the
browser. The first interaction uses the deterministic fake model, so AgentMuru should not
request provider credentials. Stop the server with `Ctrl+C` when you finish.

If the server does not start, rerun `muru doctor`, confirm that port 8000 is available,
and review [server and Workspace operations](../guides/server-and-workspace.md).

## Next steps

- [Govern tool execution](../cookbook/governed-tools.md).
- [Persist sessions with SQLite](../guides/sqlite-persistence.md).
- [Understand agents and models](../concepts/agents-and-models.md).
- [Look up the stable public API](../reference/public-api.md).
