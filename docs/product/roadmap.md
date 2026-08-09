# AgentMuru product roadmap

This roadmap is ordered by verified product outcomes. It separates shipped behavior from
the next implementation targets and keeps legacy UI work out of the active AgentMuru plan.

## Now: AgentMuru 0.2 qualification and durable local persistence

**Status: complete**

AgentMuru 0.2 combines product qualification with a standard-library SQLite persistence
adapter. The release now has durable sessions, messages, runs, ordered events, artifacts,
approvals, and idempotency records behind the same store protocols used by the in-memory
default.

Completion evidence:

- the [qualification report](../qualification.md) passes the clean-wheel CLI, scaffold,
  server, runtime, approval, handoff, workflow, and SQLite restart checks;
- the [SQLite operator guide](../guides/sqlite-persistence.md) records schema, transaction,
  backup, recovery, concurrency, and process-restart behavior;
- the [integration status](../integration-status.md) separates contract-tested adapters
  from credential-backed live checks;
- the [cookbook](../cookbook/index.md) executes every supported scenario from the built
  wheel; and
- release workflows gate documentation and package publication on fresh qualification.

## Next: production model-provider adapter

Add the first production provider without coupling vendor code to the application or
runtime layers.

Acceptance signals:

- provider configuration is explicit and secrets stay outside persisted events;
- streaming text, tool calls, provider errors, cancellation, and usage metadata map to
  AgentMuru's typed event contract;
- deterministic `FakeModel` development and qualification remain unchanged;
- credential-backed tests are opt-in and contract tests run without network access; and
- installation, operations, failure modes, and cost visibility are documented.

## After Next: PostgreSQL persistence

Add a PostgreSQL adapter for multi-tenant and higher-concurrency deployments after the
provider boundary is proven.

Acceptance signals:

- the existing store protocols remain the application boundary;
- migrations, transactions, event ordering, retries, and tenant isolation are explicit;
- concurrency and recovery tests cover multiple workers; and
- SQLite remains the zero-service local default.

## Later

- Validate Databricks identity and user-scoped operations in an explicit credential-backed
  environment.
- Establish sustained load and concurrency envelopes beyond the local SQLite target.
- Add production observability outcomes for provider latency, tool execution, approvals,
  persistence contention, and cost.

## Archived legacy direction

The former component-catalog and virtual-DOM roadmap belonged to BrickFlowUI. Those
outcomes are not relabeled as completed AgentMuru work and do not belong in the active
product board. Any useful migration context remains in the
[legacy UI migration guide](../migration-from-legacy-ui.md).
