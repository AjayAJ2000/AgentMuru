# Reopen durable sessions

**Outcome:** complete a run, release the first Runtime, reopen the same database, and read
the original run, two messages, and twelve ordered events.

Module: `examples.durable_agent`

```powershell
python examples/durable_agent.py
```

`create_application(database_path)` returns an `Application` and `SQLitePersistence` for
explicit Runtime composition. Expected status is `completed` with one session/run, two
messages, and twelve events.

Muru Workspace hydrates the snapshot then follows new events after its last sequence. A
restart during nonterminal work produces `process_interrupted`; it does not resume Python
coroutines. Lock exhaustion surfaces as `storage_busy`.

Qualified by `tests/qualification/test_scenarios.py::test_durable_scenario_restores_history_from_same_file`,
SQLite Runtime tests, HTTP/WebSocket reopen tests, and the Chromium restart flow.
