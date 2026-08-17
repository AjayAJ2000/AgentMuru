# Architecture

AgentMuru follows a dependency-inward Python architecture. Application behavior does not depend
on the browser, server framework, database adapter, Databricks, or a hosted-model SDK.

```text
Workspace / CLI / FastAPI / integrations
                    |
              Application
                    |
          Runtime / agents / workflows
                    |
 events / tools / approvals / store protocols
                    |
 in-memory and SQLite adapters / official model adapters
```

## Application boundary

`Application` declares agents and stores. `Runtime` owns execution and policy. The browser and
HTTP API consume runtime state instead of embedding a second execution engine.

## Provider boundary

`ModelProvider` normalizes text, complete tool calls, completion usage, and safe failures. The
OpenAI, Anthropic, and Google integrations depend on their official SDKs, while runtime and agent
packages depend only on AgentMuru model events.

## State boundary

Session, artifact, and approval protocols define explicit mutations. The runtime calls methods
such as append message, create run, update run, bind idempotency, append event, and recover
interrupted work. Retrieved objects are not treated as magical durable state.

In-memory and SQLite implementations share these protocols. SQLite is the bundled durable local
adapter. Server-scale stores can implement the same boundary without changing agents or tools.

## Transport boundary

FastAPI exposes snapshots, commands, ordered event replay, and a WebSocket follow stream. Muru
Workspace hydrates from a snapshot and resumes from a sequence cursor. Protocol state remains
typed and versioned.

## Security boundary

Model output is treated as untrusted input. Tool registration, schema validation, permissions,
approval, redaction, timeout, retries, and execution all remain runtime-controlled. Server
identity and session ownership are independent from provider identity.

## Labs boundary

The Go-native module has separate contracts, release artifacts, and qualification. Machine
profiling, pack compilation, adaptive routing, local models, and host-capability brokering do not
expand the Python package claim until they pass their own promotion gates.
