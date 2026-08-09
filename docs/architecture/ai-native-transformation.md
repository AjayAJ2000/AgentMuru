# AI-native transformation log

## Completed

- Renamed distribution, package, CLI, workspace, examples, and public documentation to AgentMuru.
- Replaced the component-first public API with agents, models, tools, sessions, runtime, and events.
- Added ordered event persistence/replay, deterministic provider tests, cancellation, and idempotency.
- Added permission enforcement, resumable approvals, artifact storage, traces, usage, and redaction.
- Added deterministic workflows, explicit memory, provider-neutral knowledge/guardrail/MCP seams, and handoffs.
- Replaced VDOM transport with protocol version 1 HTTP/WebSocket runtime actions and event streaming.
- Rebuilt the browser as Muru Workspace with sessions, streaming, tools, approvals, artifacts, errors, usage, and traces.
- Migrated useful Databricks adapters beneath an optional integration boundary.
- Added standard-library SQLite persistence for sessions, messages, runs, events, artifacts,
  approvals, and idempotency with atomic sequence allocation and restart recovery.
- Added complete scenario, clean-wheel, server, Workspace, and documentation qualification.

## Removed

- Python component and hook APIs as the application's conceptual center.
- VDOM serialization, component patching, page callbacks, and generic React renderer.
- UI-centric examples, component reference catalog, obsolete branding, and legacy CLI/package names.
- Compatibility imports and protocol aliases.

## Verification status

Fresh 0.2 evidence includes 124 Python tests, 9 frontend tests, 3 Chromium flows, static
analysis, strict documentation, built distributions, and a second isolated wheel environment
with no source-path injection. SQLite and in-memory stores are implemented. Databricks
adapter contracts and optional imports are tested, but hosted credential verification is
separate. Production model providers and PostgreSQL remain planned.
