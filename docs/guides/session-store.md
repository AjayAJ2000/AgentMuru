# Add a session store

Implement `SessionStore` without changing Runtime. AgentMuru 0.2 requires:

- `create`, `get`, `list`, and `save` for session records;
- `append_message` for explicit ordered message writes;
- `create_run`, `update_run`, and `get_run` for durable transitions;
- `get_idempotent_run` and `bind_idempotency_key` for session-scoped replay;
- `recover_interrupted_runs` for honest process-restart semantics;
- `append_event`, `events`, and compatible replay/follow subscription behavior.

`append_event` must allocate the next sequence atomically. Persist, commit, then publish.
Never assign a sequence from an in-memory object when multiple store clients can write.

Use `tests/sessions/test_store_contract.py` as an adapter contract. A production adapter
also needs ownership queries, retention, encryption, backups, migrations, safe errors, and
reconnect subscriptions. See the [0.2 custom-store migration](../migration-custom-stores-0.2.md).
