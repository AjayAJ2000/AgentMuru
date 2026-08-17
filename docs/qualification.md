# Qualification

AgentMuru release claims come from repeatable gates. Offline contracts and credential-backed live
checks remain separate so fixture evidence cannot be mistaken for provider or device evidence.

## Python and package gate

CI runs Python 3.10, 3.11, 3.12, and 3.13. The gate includes:

- the full Pytest suite;
- Ruff and MyPy;
- provider request, streaming, tool-call, usage, failure, and cancellation contracts without
  network access;
- CLI, scaffold, examples, packaging, branding, and documentation contracts;
- source distribution and wheel construction plus metadata inspection.

## Workspace gate

The frontend gate installs from `package-lock.json`, then runs component tests, lint, TypeScript
checks, production build, bundle tests, and bundle budgets. Browser flows cover the real server,
session interaction, reconnect, approval states, and restart behavior.

## Documentation gate

MkDocs builds with `--strict`. The contract verifies current installation commands, task-based
navigation, provider pages, operational limits, stable references, Labs separation, asset links,
and absence of legacy public identity.

## Clean-wheel gate

`qualification/run_clean_install.py` creates an isolated virtual environment, disables user-site
and inherited Python paths, installs the built wheel, checks dependency consistency, runs the CLI,
imports a generated scaffold, starts the packaged server, and exercises installed runtime paths.

Run it after building:

```powershell
python -m build
python qualification/run_clean_install.py `
  --wheel dist/agentmuru-0.3.0-py3-none-any.whl `
  --report .tmp/qualification.json
```

The installed smoke path covers runtime execution, approvals, handoff, workflow, durable SQLite
reopen, interrupted-run recovery, and optional integration imports.

## Credential-backed checks

Official provider contract tests do not prove that a deployment account can use a model. Before
release into an environment, run one restricted live request per selected provider and record:

- account and region without secrets;
- model ID and access outcome;
- text streaming and one harmless tool call;
- token usage and stable failure handling;
- quota and billing controls;
- provider data retention and privacy configuration.

Databricks live checks follow the same opt-in rule.

## Native Labs evidence

The action-router fixture gate builds the Go CLI, runs native tests, measures all 40 included
cases, requires at least 95% correct routing, validates every result, and requires zero executed
effects. It does not qualify a public model, low-end device, Android device, container boundary,
or live internet retrieval.
