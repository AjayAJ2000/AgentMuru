# AgentMuru

[![PyPI](https://img.shields.io/pypi/v/agentmuru?label=PyPI)](https://pypi.org/project/agentmuru/)
[![Python](https://img.shields.io/pypi/pyversions/agentmuru)](https://pypi.org/project/agentmuru/)
[![CI](https://github.com/AjayAJ2000/AgentMuru/actions/workflows/ci.yml/badge.svg)](https://github.com/AjayAJ2000/AgentMuru/actions/workflows/ci.yml)
[![Documentation](https://img.shields.io/badge/docs-online-0A7C7F)](https://ajayaj2000.github.io/AgentMuru/)
[![License: MIT](https://img.shields.io/badge/license-MIT-0D5F8A.svg)](LICENSE)

Build agents you can see, steer, and trust.

AgentMuru is a Python runtime and browser Workspace for observable, human-governed AI
applications. It keeps model turns, tool calls, approvals, events, sessions, artifacts,
workflows, and traces inside one explicit application model.

## Run the local MVP

```powershell
python -m pip install agentmuru==0.3.0
muru doctor
muru init my-agent --name "My Agent"
cd my-agent
muru run app:application
```

Open `http://127.0.0.1:8000`. The default starter uses `FakeModel`, so it runs without a
credential or network call.

## Use an official model provider

```powershell
muru init my-openai-agent --provider openai
muru init my-anthropic-agent --provider anthropic
muru init my-google-agent --provider google
```

AgentMuru 0.3 includes official SDK adapters for OpenAI Responses, Anthropic Messages, and
Google Gen AI. Each adapter streams into the same normalized text, tool-call, completion,
usage, and failure events. API keys stay in provider-standard environment variables.

## Add durable local persistence

```python
from agentmuru import Agent, Application, FakeModel, Runtime, SQLitePersistence

persistence = SQLitePersistence("agentmuru.db")
application = Application(
    agent=Agent(
        name="support",
        instructions="Answer support questions using approved tools.",
        model=FakeModel.responses("AgentMuru is ready."),
    ),
    session_store=persistence.sessions,
    artifact_store=persistence.artifacts,
)
runtime = Runtime(application, approvals=persistence.approval_service())
```

`SQLitePersistence` stores sessions, complete assistant tool calls, runs, ordered events,
artifacts, approvals, and idempotency keys in one file. Operate one active AgentMuru runtime
process per SQLite file.

## MVP scope

- Python 3.10 through 3.13.
- Typed agents and tools with deny-by-default permissions.
- Human approval for sensitive tool execution.
- Official OpenAI, Anthropic, and Google model adapters.
- In-memory or SQLite session, approval, and artifact stores.
- FastAPI HTTP and WebSocket transport with the bundled React Workspace.
- Explicit workflows, handoffs, trace spans, usage, replay, cancellation, and recovery.
- Optional Databricks adapters outside the core dependency set.

The Go-native adaptive runtime remains an experimental Labs track and is not part of the
PyPI 0.3.0 package.

## Develop

```powershell
git clone https://github.com/AjayAJ2000/AgentMuru.git
cd AgentMuru
python -m pip install -e ".[dev,docs,providers]"
python -m pytest -q
python -m mkdocs build --strict
```

Read the full documentation at
[https://ajayaj2000.github.io/AgentMuru/](https://ajayaj2000.github.io/AgentMuru/).

AgentMuru is available under the MIT License.
