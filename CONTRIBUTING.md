# Contributing to AgentMuru

Open an issue before proposing a public API or wire-protocol change. Runtime behavior
must be introduced with a failing test and must emit typed events. Provider adapters,
session stores, artifact stores, and renderers depend on core protocols; core never
imports them.

Before submitting a change, run the commands in `DEVELOPMENT.md`, update relevant docs,
and include security implications for tools, credentials, persistence, or browser data.
Do not add a capability to documentation until a deterministic test proves it.

All contributors must follow `CODE_OF_CONDUCT.md`.
