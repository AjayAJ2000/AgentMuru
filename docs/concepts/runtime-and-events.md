# Runtime and events

`Runtime` turns a submitted message into one ordered, observable run. It owns the state machine
instead of delegating control to a provider SDK.

## Turn lifecycle

1. Persist the user message and create a run.
2. Emit `agent.started` and `model.request.started`.
3. Stream `model.token.delta` events while collecting assistant text.
4. Collect complete tool calls and persist the assistant message.
5. Emit `tool.call.requested`, then evaluate permission and approval.
6. Execute allowed tools and persist tool-result messages.
7. Request another model turn when tools returned results.
8. Persist the final assistant message and emit `run.completed`.

The assistant tool-call message always precedes its tool-result messages. That invariant is
required by hosted-provider conversation APIs and by durable replay.

## Event identity

Every `RuntimeEvent` has a UUID, UTC timestamp, session ID, session-local positive sequence,
and JSON-safe payload. Run, trace, and parent IDs are present when the event belongs to those
scopes.

Stores assign the sequence atomically. Consumers reconnect with the last observed sequence and
request only later events.

## Terminal outcomes

A run ends as `completed`, `failed`, or `cancelled`. Stable error codes let clients react
without parsing provider messages. Examples include `permission_denied`, `tool_failed`,
`model_rate_limit`, `model_invalid_tool_arguments`, `approval_expired`, `storage_busy`, and
`process_interrupted`.

## Cancellation

Cancelling an active run cancels the runtime task, closes provider streams where supported,
marks the run cancelled, and emits `run.cancelled`. `Runtime.wait()` uses shielding so a caller
timeout does not implicitly cancel the underlying run.

See the [event reference](../reference/events.md) for the complete event family.
