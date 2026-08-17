# Sessions and memory

A `Session` is the durable conversation and execution boundary. It contains messages, runs,
ordered events, optional user ownership, a title, and JSON-compatible metadata.

## Messages

Messages use four roles: `user`, `assistant`, `tool`, and `system`. Assistant messages can
include complete `AssistantToolCall` records with an ID, name, and object arguments. Tool-result
messages link back through `tool_call_id` and retain the tool name.

This structure is provider-neutral but preserves the information required to reconstruct each
official provider conversation.

## Runs

Every submission creates a `RunRecord` with an agent name and one of these states:

- `queued`
- `running`
- `waiting_approval`
- `completed`
- `failed`
- `cancelled`

Terminal runs include a completion time and may include a stable error code.

## Store choices

`InMemorySessionStore` is ideal for tests and short local demos. `SQLiteSessionStore`, exposed
through `SQLitePersistence`, survives process restarts and coordinates atomic event sequences,
idempotency keys, subscriptions, and interrupted-run recovery.

## Idempotency

Pass an `idempotency_key` to `Runtime.submit()` or the message API when a client may retry the
same request. The session store binds the key to one run and returns that run on a repeated
submission.

## Custom stores

A custom `SessionStore` must implement the full protocol, including explicit message and run
mutations, idempotency, event append and subscription, and interrupted-run recovery. Read the
[public API reference](../reference/public-api.md#stores) before replacing the bundled stores.
