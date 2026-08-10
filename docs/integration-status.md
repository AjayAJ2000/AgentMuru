# Current capabilities and limits

Use this page to confirm what AgentMuru 0.2 supports before you choose an integration or
deployment shape. Capability claims use four precise states:

- **Implemented**: shipped in the runtime and exercised directly.
- **Contract tested**: adapter behavior is verified with deterministic fakes.
- **Credential verified**: exercised against an authorized live service.
- **Planned**: roadmap work, not a current capability.

| Capability | State | Evidence | Boundary |
| --- | --- | --- | --- |
| FakeModel | Implemented | Runtime and scenario suites | Deterministic; not a production provider |
| In-memory stores | Implemented | Shared store contracts | Process-local only |
| SQLite persistence | Implemented | Reopen, concurrency, browser restart, clean wheel | One Runtime process per file |
| Databricks SDK/SQL imports | Contract tested | Optional-extra clean install and adapter tests | No live workspace call in offline gate |
| Databricks live workspace | Contract tested | Identity/config behavior | Credential verification is not recorded yet |
| Production model provider | Planned | Roadmap | FakeModel is the current concrete provider |
| PostgreSQL store | Planned | Store protocols and roadmap | SQLite is the current durable implementation |

The latest machine-readable and rendered evidence is in
[AgentMuru qualification evidence](qualification.md).
