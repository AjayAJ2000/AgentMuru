# Run workflows and handoffs

**Outcome:** keep workflows deterministic and make agent transfer an explicit new run.

Handoff module: `examples.handoff_agent`

```powershell
python examples/handoff_agent.py
```

Expected: researcher and writer runs both complete with one `agent.handoff` event carrying
the reason and target run ID. Muru Workspace shows each run and the ordered transfer.

Workflow module: `examples.workflow_agent`

```powershell
python examples/workflow_agent.py
```

Expected: `research` and `summarize` checkpoints and the summary “AgentMuru verified 2
facts.” Unknown target agents fail before a target run; workflow handler failures return a
stable failure code after configured retries.

Qualified by `tests/qualification/test_scenarios.py::test_handoff_scenario_runs_both_agents`,
`test_workflow_scenario_returns_checkpoint_evidence`, and focused handoff/workflow tests.
