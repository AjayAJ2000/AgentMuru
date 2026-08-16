# Clean-wheel qualification

This harness proves the built AgentMuru wheel works outside the source checkout.
It creates an isolated virtual environment, installs the exact wheel with the
Databricks extra, checks dependency consistency, runs the CLI and scaffold,
executes durable/runtime/governance/handoff/workflow smoke scenarios, and starts
the installed HTTP server on a free loopback port.

```powershell
python -m build
python qualification/run_clean_install.py `
  --wheel dist/agentmuru-0.2.0-py3-none-any.whl `
  --report .tmp/qualification.json
```

The command exits nonzero when any required check fails. Live Databricks calls
remain opt-in and are explicitly reported as not attempted by the offline gate.

## Native action-router simulation

Build the native CLI and measure the flagship 40-case portable pack:

```powershell
.\qualification\edge\action_router_simulation.ps1 -GoExecutable go
```

The report is fixture-level evidence. It verifies compilation, routing, default-deny policy,
and zero executed effects; it does not substitute for a model or reference-device report.
