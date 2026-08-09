# Architecture decisions

## Runtime first

Agent execution is the application. UI is a projection so runtime tests need no browser.

## Events before rendering

Events support streaming, replay, observability, and multiple consumers without frontend coupling.

## Explicit sessions

Sessions define ownership and persistence boundaries; no global mutable application state exists.

## Provider neutrality

Normalized model events keep vendor SDK semantics outside agents and runtime code.

## Governed tools

Permissions and approvals exist because Python callbacks are not an adequate enterprise security model.

## First-class artifacts

AI applications produce structured work, not only chat text. Artifacts have stable identities and storage.

## Explicit store mutations

Runtime calls abstract operations such as `append_message`, `create_run`, `update_run`,
and `append_event`. It does not use mutation of retrieved in-memory objects as persistence.
This keeps dependency direction inward and makes every durable write auditable and testable.

## SQLite as the local durable default

SQLite is the best standard-library, zero-service default for a single-file local Runtime.
AgentMuru uses foreign keys, WAL, schema versioning, transactions, a busy timeout, bounded
retry, and `BEGIN IMMEDIATE` counter allocation. PostgreSQL remains the planned server-scale
adapter rather than an unnecessary default dependency.

## Honest process recovery

Python coroutines cannot be resurrected after process loss. Nonterminal durable runs are
failed with `process_interrupted`; users continue from history with a new run.
