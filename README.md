# AgentMuru

[![PyPI](https://img.shields.io/pypi/v/agentmuru?label=PyPI)](https://pypi.org/project/agentmuru/)
[![Python](https://img.shields.io/pypi/pyversions/agentmuru)](https://pypi.org/project/agentmuru/)
[![CI](https://github.com/AjayAJ2000/AgentMuru/actions/workflows/ci.yml/badge.svg)](https://github.com/AjayAJ2000/AgentMuru/actions/workflows/ci.yml)
[![Documentation](https://img.shields.io/badge/docs-online-0A7C7F)](https://ajayaj2000.github.io/AgentMuru/)
[![License: MIT](https://img.shields.io/badge/license-MIT-0D5F8A.svg)](LICENSE)

Build agents you can see, steer, and trust.

AgentMuru is a Python-native runtime and Workspace for observable, human-governed AI
applications. Agents, tools, events, sessions, approvals, artifacts, workflows, and traces
are the application. Muru Workspace is their replayable operator projection.

## Install and run

```powershell
python -m pip install agentmuru==0.2.0
muru doctor
muru init my-agent --name "My Agent"
cd my-agent
muru run app:application
```

Open `http://127.0.0.1:8000`. The scaffold uses `FakeModel`, so the first run is local and
credential-free.

## Durable local Runtime

```python
from agentmuru import Agent, Application, FakeModel, Runtime, SQLitePersistence

persistence = SQLitePersistence("agentmuru.db")
application = Application(
    agent=Agent(
        name="customer-intelligence",
        instructions="Investigate customer questions using governed tools.",
        model=FakeModel.responses("The customer is active."),
    ),
    session_store=persistence.sessions,
    artifact_store=persistence.artifacts,
)
runtime = Runtime(application, approvals=persistence.approval_service())
```

`SQLitePersistence` uses the standard library and stores sessions, messages, runs, ordered
events, artifacts, approvals, and idempotency keys in one file. It enables foreign keys and
WAL, uses atomic event counters, retries bounded lock contention, and marks nonterminal
runs `process_interrupted` after restart. Operate one active Runtime process per file.

## Why AgentMuru

- Provider-neutral streaming model events and a deterministic local provider.
- Ordered, replayable Runtime events with reconnect cursors.
- Typed tools with deny-by-default permissions, risk, approval, and redaction.
- Durable sessions, artifacts, approval audit records, and idempotency.
- Explicit workflows and agent handoffs with stable run identities.
- FastAPI HTTP/WebSocket protocol and an accessible React Workspace.
- Optional Databricks adapters outside the core dependency direction.

## Verified in 0.2.0

- 124 Python tests across Runtime, storage, security, server, integrations, workflows, CLI,
  examples, packaging, and docs contracts.
- 9 frontend state/component tests and 3 Chromium flows, including a real server restart.
- Ruff, MyPy, frontend lint/type/build/bundle gates, and strict MkDocs.
- An isolated wheel install with user-site and `PYTHONPATH` disabled, including CLI,
  scaffold, server health, durable reopen, approvals, handoff, workflow, and Databricks
  optional imports.

See the [qualification evidence](https://ajayaj2000.github.io/AgentMuru/qualification/)
and [integration status](https://ajayaj2000.github.io/AgentMuru/integration-status/).
Credential-backed Databricks calls are recorded separately and are not claimed by the
offline contract gate. Production model providers and PostgreSQL are planned follow-ons.

## Security and SQLite limits

Tool permissions are deny-by-default when declared but not granted. Risky actions pause
for approval. Sensitive arguments are redacted from public events. Deployments must add
authentication, explicit trusted hosts/origins, TLS, database path permissions, backup,
and sandboxing for untrusted tools. Built-in SQLite is not encrypted and is intended for
one Runtime process with modest write concurrency.

## Contribute

```powershell
git clone https://github.com/AjayAJ2000/AgentMuru.git
cd AgentMuru
python -m pip install -e ".[dev,docs]"
python -m pytest -q
python -m mkdocs build --strict
```

Documentation: [https://ajayaj2000.github.io/AgentMuru/](https://ajayaj2000.github.io/AgentMuru/)

License: MIT.
