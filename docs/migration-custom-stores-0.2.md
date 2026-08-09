# Migrate custom stores to 0.2

Runtime no longer mutates session-owned lists as its persistence mechanism. Custom stores
must implement each write explicitly.

## Required session operations

- `append_message`: write one ordered message for a session.
- `create_run`: insert a run.
- `update_run`: persist status, completion, and error changes.
- `get_run`: read without a Runtime-owned index.
- `get_idempotent_run`: read a session-scoped key binding.
- `bind_idempotency_key`: create the session/run binding.
- `recover_interrupted_runs`: fail nonterminal records with `process_interrupted`.
- `append_event`: allocate sequence atomically, commit, then publish.

Keep `create`, `get`, `list`, `save`, `events`, and replay/follow subscription behavior.
Run `tests/sessions/test_store_contract.py` against the adapter.

Approval stores implement `create`, `get`, `list`, and `save`; waiter futures remain local.
Artifact stores accept text, bytes, and finite JSON and reject unsupported content before
insert. Map lock exhaustion to `storage_busy` and invalid/newer storage to safe corruption
or migration errors without exposing data.
