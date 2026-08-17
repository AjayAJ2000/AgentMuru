# Architecture decisions

These decisions describe the active 0.3 product, not an earlier project direction.

## Execution is the application

Agent definitions, runtime state, tools, policy, approvals, and stores are the application. User
interfaces project that state. Runtime tests therefore need no browser.

## Events precede rendering

Ordered events support streaming, replay, observability, recovery, and multiple consumers without
coupling execution to React or FastAPI.

## Sessions are explicit

Sessions define ownership, conversation, run, event, artifact, and idempotency boundaries. There
is no global mutable conversation state.

## Provider SDKs stay at the edge

Official SDK adapters translate request and stream shapes into `ModelEvent`. Runtime code never
imports provider response types. Provider-specific fields require an explicit options mapping.

## Assistant tool calls are durable

The runtime persists complete assistant tool calls before linked tool results. SQLite stores call
IDs, names, and object arguments. This ordering makes replay valid for the next hosted-model turn.

## Tools are governed capabilities

Python callbacks alone are not a security model. Tool schema, declared permission, granted
permission, risk, side-effect classification, redaction, approval, timeout, and retries are
separate controls.

## Store writes are explicit

Runtime calls protocol mutations such as `append_message`, `create_run`, `update_run`, and
`append_event`. Adapters can make each operation atomic and auditable.

## SQLite is the durable local default

SQLite provides a zero-service, standard-library path for one active runtime process. AgentMuru
uses foreign keys, WAL, migration, bounded busy retries, and `BEGIN IMMEDIATE` sequence
allocation. Higher-concurrency deployments should replace the store, not add hidden SQLite
coordination.

## Process recovery is honest

A Python coroutine cannot be recreated after process loss. Nonterminal durable runs fail with
`process_interrupted`, while their messages, tool calls, events, approvals, and artifacts remain
available for inspection and a new run.
