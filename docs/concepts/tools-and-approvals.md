# Tools and approvals

The `@tool` decorator converts a typed Python function into a validated provider schema and an
async execution boundary.

```python
from agentmuru import tool

@tool(
    permission="orders.refund",
    approval="required",
    risk="high",
    side_effects=True,
    sensitive_fields={"payment_token"},
)
def refund_order(order_id: str, payment_token: str) -> dict[str, str]:
    """Refund one approved order."""
    return {"order_id": order_id, "status": "refunded"}
```

## Validation

The function signature becomes JSON Schema. Required parameters stay required, defaults are
preserved, unknown arguments fail, and values are coerced against supported Python type hints.
Sync handlers run in a worker thread. Async handlers run in the event loop.

Each tool also controls timeout, retries, risk, side-effect classification, permission, and
fields that must be redacted from public events.

## Permission comes first

Declaring `permission="orders.refund"` does not grant it. The agent must also include that
string in `Agent.permissions`. A missing grant ends the run with `permission_denied` before the
handler executes.

## Approval modes

| Mode | Behavior |
| --- | --- |
| `auto` | Policy decides from risk and side-effect metadata |
| `required` | Runtime always creates an approval request before execution |
| `never` | Runtime never pauses for human approval |

An approval stores the tool name, public arguments, permission, risk, actor, reason, and final
decision. Rejection and expiry do not execute the handler.

## Safe event payloads

Sensitive fields become `[REDACTED]` before tool arguments enter public runtime events. The
runtime persists the complete assistant tool call for provider continuity, while operator
events expose only the redacted view.
