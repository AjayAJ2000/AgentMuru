# Release notes

## 0.3.0

- Added `OpenAIModel`, `AnthropicModel`, and `GoogleGenAIModel` on the official provider SDKs.
- Added normalized provider settings, tool calls, usage, safe error codes, cancellation cleanup,
  and optional dependency guidance.
- Persisted complete assistant tool calls before tool results and migrated SQLite to the current
  schema.
- Added provider-aware `muru init --provider` starters and executable provider examples.
- Added provider extras with verified SDK floors and aligned Python, frontend, workflow, and
  distribution versions.
- Rebuilt the documentation around Get started, Build, Providers, Operate, Reference, Labs, and
  Project tasks.
- Clarified that the Python package and browser Workspace are the MVP while native work remains
  in Labs.

Limitations: use one active runtime process per SQLite file. The package does not include
PostgreSQL, durable trace export, a tool sandbox, or production identity management. Real provider
access and quotas remain deployment-specific.

## 0.3.0-alpha.1 native preview

- Added a separate native terminal workspace, hardware discovery, responsive layouts, durable
  redacted events, and session restore.
- Added signed model-catalog verification, atomic installation, compatible llama.cpp runtime
  selection, authenticated loopback supervision, constrained decisions, and bounded residency.
- Added portable agent-pack contracts, deterministic requirements compilation, simulation-only
  routing, explanations, and measured fixture gates.

This remains a separate GitHub prerelease. The public model catalog is empty and action effects
remain simulated.

## 0.2.0

- Added `SQLitePersistence` for sessions, messages, runs, ordered events, artifacts, approvals,
  and idempotency.
- Added WAL, foreign keys, schema versioning, atomic event counters, bounded busy retries, and
  stable storage errors.
- Added honest restart recovery with `process_interrupted`.
- Qualified browser reconnect, restart, approvals, artifacts, cancellation, handoffs, workflows,
  CLI scaffolding, and optional Databricks imports.

## 0.1.0

- Established the AgentMuru Python runtime, Workspace, CLI, provider-neutral models, typed tools,
  permissions, sessions, events, cancellation, approvals, artifacts, traces, workflows, and
  handoffs.
