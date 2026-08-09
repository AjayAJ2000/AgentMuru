# Changelog

## 0.2.0

- Added `SQLitePersistence` for sessions, messages, runs, atomic ordered events, artifacts,
  approvals, and idempotency using the Python standard library.
- Replaced implicit session-list mutation with explicit store operations and shared adapter
  contracts.
- Added WAL, foreign keys, schema versioning, `BEGIN IMMEDIATE` event counters, a 5-second
  busy timeout, bounded retries, safe serialization, and storage error codes.
- Added honest restart behavior: nonterminal runs become failed with `process_interrupted`
  and durable history remains replayable.
- Qualified SQLite HTTP/WebSocket restore, Muru Workspace reconnect/restart, approvals,
  artifacts, cancellation, handoffs, workflows, and optional Databricks imports.
- Added six runnable scenario examples, an isolated clean-wheel harness, generated evidence,
  operator/deployment guides, migration notes, and an executable cookbook.
- Adopted the DataMuru product-family Hybrid Vel Eye mark, Peacock Teal, Cobalt Wing, and
  Eye Gold documentation identity.

Limitations: use one active Runtime process per SQLite file; SQLite is not encrypted;
credential-backed Databricks calls, production model providers, and PostgreSQL are not
claimed as completed in this release.

## 0.1.0

- Re-founded the project as AgentMuru.
- Added provider-neutral agents, models, typed tools, permissions, sessions, events, runtime, and cancellation.
- Added resumable approvals, artifacts, traces, usage, deterministic workflows, and typed handoffs.
- Added protocol version 1 HTTP/WebSocket server and Muru Workspace.
- Added `muru` CLI, runtime-first examples, architecture documentation, and migration guide.
- Removed the former component/VDOM public architecture and all compatibility aliases.
