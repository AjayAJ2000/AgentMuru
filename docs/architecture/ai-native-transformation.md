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

## Removed

- Python component and hook APIs as the application's conceptual center.
- VDOM serialization, component patching, page callbacks, and generic React renderer.
- UI-centric examples, component reference catalog, obsolete branding, and legacy CLI/package names.
- Compatibility imports and protocol aliases.

## Verification status

Local deterministic verification covers domain, runtime, security, server, integrations,
workflow, frontend projection, packaging, CLI, examples, and documentation. Production
provider credentials, durable external stores, and hosted Databricks resources require
environment-specific validation and are not represented as locally verified features.
