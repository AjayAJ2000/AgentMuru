# Govern tool execution

**Outcome:** demonstrate all permission/approval outcomes and prove only the approved
mutation executes.

Module: `examples.governed_tool_agent`

```powershell
python examples/governed_tool_agent.py
```

Expected terminal result includes `allow=completed`, `deny=permission_denied`,
`approve=completed`, `reject=completed`, `expiry=approval_expired`, and `mutations=1`.

Muru Workspace shows requested tools, the pending approval card, actor decisions, expiry,
and terminal run state. Rejection is a reviewed tool outcome and the agent may continue;
expiry fails the run. Missing grants fail before invocation. Redacted arguments, not raw
sensitive inputs, enter public events.

Qualified by `tests/qualification/test_scenarios.py::test_governed_tool_scenario_exercises_every_policy_outcome`
and the Runtime approval/tool suites.
