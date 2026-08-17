# AgentMuru repository instructions

## Product center

AgentMuru is an AI application runtime. The browser is a projection of runtime state.
Do not move model calls, tool execution, approvals, workflows, or persistence into React
components. Do not reintroduce a VDOM or callback-driven application model.

## Dependency direction

`events/domain protocols <- runtime <- server/integrations/CLI/UI`.

- `agentmuru/core`, `sessions`, `models`, `tools`, `artifacts`, `approvals`, and
  `observability` cannot import FastAPI, React, Databricks, or vendor model SDKs.
- Provider and storage implementations satisfy core protocols without runtime edits.
- Frontend source consumes protocol version 1 and owns display state only.
- An event is appended to the session store before it is published.
- Per-session event sequence must remain monotonic and replayable.

## Public API

Stable top-level imports live in `agentmuru/__init__.py`. Add an export only when its API
is documented and tested. Model providers emit normalized `ModelEvent` values. Tools use
`Tool` and `@tool`; arbitrary callbacks are not runtime actions.

## Security

- Declared permissions are denied unless granted to the agent.
- High-risk or approval-required tools pause before invocation.
- Never serialize secrets, raw exception details, access tokens, or unredacted sensitive arguments.
- Authenticate and authorize HTTP and WebSocket actions against session ownership.
- Do not cache user-scoped Databricks clients or SQL connections across operations.

## Tests and commands

Write a failing test before implementation. Run focused tests after each change, then:

```powershell
python -m pytest -q
python -m ruff check agentmuru tests
python -m mypy agentmuru
cd frontend
npm test -- --run
npm run lint
npm run typecheck
npm run build
npm run check:bundle
cd ..
python -m mkdocs build --strict
python -m build
```

Update the relevant Get started, Build, Providers, Operate, Reference, or Labs page when
behavior or boundaries change. Never document an unverified capability as complete, and keep
experimental native work under `docs/labs/`.
