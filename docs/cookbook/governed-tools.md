# Govern tool execution

The executable scenario is `examples.governed_tool_agent`.

```powershell
python examples/governed_tool_agent.py
```

It runs five deterministic policy paths: granted permission, denied permission, approved
mutation, rejected mutation, and expired approval. Only the approved path executes the side
effect.

## Define a sensitive mutation

```python
from agentmuru import tool

@tool(
    permission="records.write",
    approval="required",
    risk="high",
    side_effects=True,
    sensitive_fields={"access_token"},
)
def update_record(record_id: str, access_token: str) -> dict[str, str]:
    return {"record_id": record_id, "status": "updated"}
```

Grant `records.write` in the agent definition. The declaration and grant are separate so a tool
cannot grant itself through model output.

## Decide an approval

```python
request = await runtime.wait_for_approval(run.id)
await runtime.decide_approval(
    request.id,
    ApprovalDecision.APPROVE,
    actor="operator@example.com",
    reason="Ticket OPS-142 authorizes this update",
)
completed = await runtime.wait(run.id)
```

Reject with `ApprovalDecision.REJECT`. Configure a finite runtime approval timeout to expire an
unanswered request. In every non-approved path, verify that the handler did not run.

## Inspect the evidence

The session timeline includes `tool.call.requested`, `approval.requested`, the decision event,
and either tool completion or terminal failure. Sensitive values are `[REDACTED]` in public
event arguments.
