# AgentMuru AI-Native Rearchitecture Design

## Decision

BrickflowUI will be re-founded in place as **AgentMuru**, a Python-first runtime and
workspace framework for building observable, human-governed AI applications. This is
a clean break: the distribution, Python package, CLI, frontend identity, documentation,
examples, and wire protocol will use AgentMuru terminology. No `brickflowui` import,
CLI alias, or compatibility facade will remain.

The product identity is:

- product: **AgentMuru**;
- framework: **AgentMuru Runtime**;
- Python distribution and package: `agentmuru`;
- CLI: `muru`;
- browser application: **Muru Workspace**.

## Product Boundary

AgentMuru occupies the intersection of an agent runtime, an AI application workspace,
human-in-the-loop control, artifacts, observability, and enterprise data applications.
It is not a model-provider SDK, a general workflow orchestrator, a UI component catalog,
or a Databricks-only product.

The first release must provide one complete local vertical slice: a user message starts
an agent run; a provider streams output and can request tools; policy can pause a risky
tool for approval; the run emits typed events; sessions, messages, artifacts, approvals,
usage, and traces can be inspected in the workspace; workflows compose deterministic
steps; and all runtime behavior is testable without a browser or external credentials.

## Current Architecture

The current repository is component-first:

```text
Public component API
    -> Python VNode construction and hooks
    -> per-WebSocket RenderContext
    -> VDOM serialization and patches
    -> FastAPI/WebSocket transport
    -> generic React component renderer
```

Useful engineering to salvage includes the FastAPI delivery shell, WebSocket lifecycle
hardening, origin/host/CSRF/authentication controls, safe local-asset serving, React/Vite
build pipeline, and Databricks service adapters. The component catalog, hook-driven
application state, page callback model, and VDOM patch protocol must not remain the
application's center of gravity.

## Target Architecture

Dependency direction is inward and acyclic:

```text
Integrations / Server / CLI / Workspace UI
                    |
Application orchestration and projections
                    |
Runtime + Agents + Workflows
                    |
Events + Domain models + Provider/Store protocols
```

Core domain code has no FastAPI, React, Databricks, or vendor-model dependency. Provider,
session-store, artifact-store, and exporter integrations depend on protocols defined by
the core. The UI consumes a runtime event/projection protocol and never owns agent logic.

The Python package is organized by responsibility:

```text
agentmuru/
  core/            application, runtime, events, context, lifecycle
  agents/          agent definition and runner
  models/          provider protocol, responses, capabilities, registry, fake provider
  tools/           decorator, schema, registry, permissions, execution
  sessions/        session domain and store protocol/in-memory store
  artifacts/       artifact domain and store
  approvals/       requests, decisions, approval policy
  workflows/       deterministic steps, runner, checkpoints
  observability/   traces, spans, usage and in-memory exporter
  memory/          explicit memory protocol and conversation implementation
  knowledge/       source/document/retriever protocols
  guardrails/      input/output/tool guardrail protocols
  protocols/       MCP and interoperability seams
  server/          HTTP/WebSocket adapter and workspace projection
  integrations/    optional provider, Databricks, and storage adapters
  cli/             `muru` commands and project template
  ui/              retained Python rendering primitives only where runtime projections use them
```

## Public API

The smallest useful application is:

```python
from agentmuru import Agent, Application, FakeModel, tool

@tool
def lookup_customer(customer_id: str) -> dict[str, str]:
    return {"customer_id": customer_id, "status": "active"}

agent = Agent(
    name="Customer Intelligence",
    instructions="Investigate customer questions using available tools.",
    model=FakeModel.responses("How can I help?"),
    tools=[lookup_customer],
)

app = Application(agent=agent)
app.run()
```

`Application` is configuration and composition. `Runtime` owns execution. `Agent` is a
provider-neutral definition. `ModelProvider` translates messages and tool schemas into a
stream of normalized model events. `Tool` owns schema and policy metadata, not UI callbacks.

## Runtime and Event Flow

Every mutation is represented by a typed, serializable event envelope containing an event
ID, event type, timestamp, session ID, run ID, trace ID, optional parent ID, sequence, and
typed payload. The initial event set covers sessions, messages, agent lifecycle, model
streaming, tools, approvals, artifacts, workflow steps, cancellation, completion, failure,
usage, and tracing.

```text
User message
  -> Session/UserMessage event
  -> Agent run + trace
  -> normalized model stream
  -> token/tool/artifact events
  -> policy and optional approval pause
  -> tool execution and model continuation
  -> completion/failure event
  -> projection update streamed to every subscribed client
```

Events are appended to the session store before publication. A monotonically increasing
session sequence supports reconnection and replay. Client actions carry idempotency keys.
Slow clients receive bounded queues and can reconnect from their last sequence.

## Sessions and Persistence

`Session` explicitly owns messages, runs, events, artifacts, approval references, and
metadata. `SessionStore` supports create/get/save/list and atomic event append. The release
ships an isolated, concurrency-safe `InMemorySessionStore`; persistent implementations are
adapters. Memory is explicit and opt-in rather than implicit retention.

## Models and Tools

The model boundary supports generate/stream, text deltas, structured completion, tool-call
requests, usage, and capability metadata. `FakeModel` deterministically drives all tests and
examples. A registry accepts provider factories without editing runtime code.

The `@tool` decorator derives JSON Schema from Python annotations and dataclasses, records
side effects, risk, permissions, approval mode, timeout, retries, and redaction metadata.
Arguments are validated before invocation. Async and sync handlers are supported; sync
handlers run off the event loop. Tool failures are explicit events and never silently
converted to success text.

## Governance and Security

Permissions use namespaced strings such as `database.read`, `database.write`, `network`,
`filesystem.read`, `filesystem.write`, `execute`, and `secret`. Default policy denies
undeclared capabilities and requires approval for dangerous or explicitly gated tools.
Approval requests are durable runtime records with approve/reject decisions, actor, reason,
timestamps, timeout, and audit events. Secrets and fields marked sensitive are redacted
from serialized events, traces, logs, and browser payloads.

The retained server protections include explicit trusted hosts/origins, safe auth defaults,
bounded payloads, CSRF controls for cookie-authenticated writes, and allowlisted local assets.
Runtime action endpoints authorize both the principal and requested operation.

## Artifacts and Workspace

Artifacts have stable IDs, kind, name, MIME type, content or reference, creator, metadata,
and timestamps. The initial kinds are markdown, code, JSON, table, chart, file, image, SQL,
and report. Unsupported kinds render as a safe metadata/download view.

Muru Workspace is a purpose-built runtime projection with:

- session/run rail;
- conversation and streamed assistant output;
- visible model/tool activity;
- approval cards with approve/reject actions;
- artifact workspace with type-aware renderers;
- run state, cancellation, errors, usage, and reconnect indicators;
- trace timeline showing nested model/tool/workflow spans.

The frontend receives protocol messages rather than VDOM trees. It keeps ephemeral display
state only; authoritative application state remains in the runtime/session store.

## Workflows and Multi-Agent Boundary

The first workflow engine is deterministic and intentionally small: sequential steps,
conditional transitions, typed state, retries, agent/tool/approval steps, checkpoints, and
events. A typed handoff transfers control between registered agents and emits explicit
handoff events. Parallel distributed orchestration, schedulers, and durable remote workers
remain extension points rather than simulated features.

## Server and CLI

FastAPI exposes health, application metadata, sessions, event history, artifacts, approvals,
message submission, cancellation, and a WebSocket event stream. The protocol is versioned.
The server adapter depends only on `Application`/`Runtime` interfaces.

The `muru` CLI provides `init`, `dev`, `run`, `doctor`, and `version`. The starter project is
the smallest working AgentMuru agent and uses `FakeModel` until a real provider is configured.

## Migration and Removal

This is a 1.0-style clean break. Existing component imports, hooks, VDOM application APIs,
the `brickflowui` command, component-reference documentation, and UI-centric examples are
removed. Security, transport, theming, and Databricks code are migrated only when they fit a
new boundary. The migration guide maps real old APIs to their AgentMuru replacements and
states explicitly where there is no equivalent.

## Error Handling

Domain errors have stable codes and safe public messages. Internal exceptions retain causes
in server logs and trace metadata after redaction. Cancellation is cooperative and terminal.
Timeouts and retry exhaustion emit typed terminal events. An approval rejection is a modeled
decision, not an exception. Protocol errors never expose stack traces to clients.

## Testing and Definition of Done

Tests are layered:

- unit tests for domain models, event serialization, schemas, policy, stores, artifacts,
  approvals, traces, workflows, and provider normalization;
- runtime integration tests for streaming, tools, approval pause/resume, cancellation,
  failure, replay, handoff, and concurrency isolation;
- server contract tests for auth, validation, replay, and WebSocket actions;
- frontend tests for reducers/projections and all workspace states;
- packaging, CLI, examples, type checking, linting, frontend build, documentation build,
  dependency audit where available, and a deterministic end-to-end smoke test.

Completion requires the repository to be accurately describable as an AI application
framework whose runtime renders into an AI workspace. Capabilities not implemented and
verified locally will be listed as extension points rather than advertised as complete.

## Delivery Slices

1. Rename and establish architecture boundaries, instructions, and transformation log.
2. Build events, sessions, providers, agents, tools, runtime, artifacts, approvals, and traces.
3. Build the versioned server protocol and Muru Workspace projection.
4. Add cancellation, policy enforcement, workflows, handoff, and extension protocols.
5. Replace CLI, examples, README, architecture, migration, security, and contributor docs.
6. Remove obsolete code/assets, run the broad verification suite, inspect the release diff,
   and record any honest external-verification limits.
