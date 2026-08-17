# Capabilities and limits

This page states the current Python 0.3 MVP boundary. Labs experiments are listed separately and
are not implied by the PyPI package.

## Runtime

| Capability | Status | Boundary |
| --- | --- | --- |
| Agents and multi-turn model execution | Included | One provider per agent |
| Typed tools | Included | JSON-schema-compatible Python signatures |
| Permissions and approvals | Included | Runtime-enforced, deny when a declared permission is not granted |
| Cancellation | Included | Active runtime task and provider stream |
| Handoffs | Included | Targets declared in one `Application` |
| Workflows | Included | In-process deterministic runner and checkpoints |
| Artifacts | Included | In-memory or SQLite artifact store |
| Traces and usage | Included | Default tracer is in memory |

## Providers

| Provider | SDK path | Text streaming | Tool calls | Usage | Credential-backed qualification |
| --- | --- | --- | --- | --- | --- |
| `FakeModel` | Core | Yes | Yes | Deterministic | Offline |
| OpenAI | Official Responses API | Yes | Yes | Yes | Required per deployment account |
| Anthropic | Official Messages API | Yes | Yes | Yes | Required per deployment account |
| Google | Official Gen AI SDK | Yes | Yes | Yes | Required per deployment account |

Adapter contract tests run without keys or network calls. They validate request translation,
stream handling, complete tool arguments, usage, cancellation behavior, and safe errors. A real
deployment must verify model access, region, quota, billing, safety policy, and data handling in
its provider accounts.

Structured output, vision, audio, reasoning-specific controls, and embeddings are not declared
as portable 0.3 capabilities.

## Persistence

| Store | Status | Boundary |
| --- | --- | --- |
| In-memory sessions and artifacts | Included | One process lifetime |
| SQLite sessions, events, approvals, artifacts, and idempotency | Included | One active runtime process per file, modest writes |
| PostgreSQL | Not included | Implement behind public store protocols |
| Durable trace backend | Not included | Export or replace the default tracer |

SQLite uses WAL, foreign keys, schema migration, bounded busy retries, atomic event sequences,
and interrupted-run recovery. It is not encrypted by AgentMuru.

## Server and Workspace

The package includes the FastAPI HTTP API, session WebSocket replay, bundled browser Workspace,
trusted-host middleware, explicit HTTP and WebSocket origin controls, authentication protocols,
session ownership, payload limits, and security headers.

The default anonymous configuration is for local use. AgentMuru does not ship a production user
directory, identity provider, TLS terminator, tool sandbox, distributed scheduler, or managed
deployment control plane.

## Databricks

Databricks SDK, SQL, and Unity Catalog helpers are optional. Offline tests verify configuration,
serialization, identity isolation, and input safety. Credential-backed workspace behavior must be
qualified in the target account.

## Labs

Go-native compilation, machine profiling, adaptive action routing, and local-model catalog work
remain under [Labs](labs/index.md). They are not part of the PyPI 0.3.0 MVP or its support claim.
