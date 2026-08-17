# Event reference

`RuntimeEvent` is the replay and observability envelope. Its fields are:

| Field | Type | Meaning |
| --- | --- | --- |
| `id` | `str` | Event UUID |
| `type` | `EventType` | Stable event name |
| `timestamp` | timezone-aware `datetime` | Normalized to UTC |
| `session_id` | `str` | Owning session |
| `sequence` | `int` | Positive session-local order after persistence |
| `run_id` | `str | None` | Related run |
| `trace_id` | `str | None` | Related trace |
| `parent_id` | `str | None` | Related parent event or span |
| `payload` | JSON mapping | Immutable JSON-safe public data |

`to_dict()` emits an ISO 8601 UTC timestamp ending in `Z`. `from_dict()` restores the event and
validates timezone and payload constraints.

## Session and message

- `session.started`
- `session.completed`
- `user.message.received`
- `assistant.message.started`
- `assistant.message.delta`
- `assistant.message.completed`

## Agent and model

- `agent.started`
- `agent.completed`
- `agent.failed`
- `agent.handoff`
- `model.request.started`
- `model.token.delta`
- `model.request.completed`
- `usage.recorded`

Model request events include provider and model ID. Failure details use stable AgentMuru codes and
fixed public messages.

## Tool and approval

- `tool.call.requested`
- `tool.call.started`
- `tool.call.completed`
- `tool.call.failed`
- `approval.requested`
- `approval.granted`
- `approval.rejected`
- `approval.expired`

Tool request payloads use redacted public arguments. Approval events carry actor and reason when
the decision supplies them.

## Artifact, workflow, and trace

- `artifact.created`
- `artifact.updated`
- `workflow.started`
- `workflow.step.started`
- `workflow.step.completed`
- `workflow.completed`
- `trace.span.started`
- `trace.span.completed`

## Run outcome

- `run.completed`
- `run.failed`
- `run.cancelled`

A run has one terminal outcome. A runtime started over durable state can append `run.failed` with
`process_interrupted` for work left nonterminal by the prior process.

## Replay rule

Consumers must persist or retain the last processed sequence, not infer order from timestamps.
Reconnect with `after=<sequence>` and apply only events with a larger sequence.
