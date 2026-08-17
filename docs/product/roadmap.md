# Roadmap

The roadmap is ordered by user-visible, qualified outcomes. Shipped work remains in the release
notes, while active work stays narrow enough to verify.

## Current: Python-first 0.3 MVP

The current release line provides:

- official OpenAI Responses, Anthropic Messages, and Google Gen AI adapters;
- provider-neutral streaming text, complete tool calls, usage, cancellation, and safe failures;
- durable assistant tool-call replay in SQLite;
- provider-aware `muru init` starters and executable examples;
- governed tools, approvals, artifacts, handoffs, workflows, traces, and event replay;
- a task-oriented documentation site and clean package metadata.

Release completion requires the full Python, frontend, documentation, distribution, and
clean-wheel qualification gates plus a credential-backed smoke check for each provider account
used by the project.

## Next: server-scale persistence

Add and qualify a PostgreSQL store implementation behind the current protocols.

Acceptance signals:

- explicit tenant and session ownership;
- migrations, transactions, event ordering, subscriptions, and idempotency;
- concurrent worker, retry, recovery, and isolation tests;
- managed backup and point-in-time recovery documentation;
- no change to agent, tool, provider, or Workspace application contracts.

## Next: operational provider evidence

Turn provider contract support into repeatable deployment evidence.

Acceptance signals:

- opt-in credential-backed smoke tests with no secret persistence;
- latency, token, failure, retry, and cost dashboards built from public events and traces;
- model-access and quota runbooks;
- documented data-handling and retention decisions per deployment.

## Later

- Durable trace exporters and application-owned telemetry backends.
- A broader authentication integration guide and deployment reference.
- Sustained load and concurrency envelopes for the server-scale store.
- Promotion of selected Labs work only after clean-machine, security, and reference-device gates.

## Not promised by the MVP

The roadmap does not imply automatic production model selection, built-in PostgreSQL,
distributed scheduling, a tool sandbox, production identity management, or qualified local-model
artifacts. Those claims require implementation and published evidence.
