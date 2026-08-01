# Databricks Identity and Components Design

**Date:** 2026-07-14  
**Status:** Approved for implementation  
**Target:** BrickflowUI `dev` branch after the 2026-07-14 stability audit

## Objective

Complete the remaining Databricks capability boundary without weakening BrickflowUI's multi-user isolation. The runtime must support both shared app identity and per-user identity, make three public Databricks components functional and honest about their state, bound local asset exposure, and keep internal exception details out of browser messages.

## Identity model

BrickflowUI keeps the existing `app`, `user`, and `hybrid` authentication modes. A normalized principal may carry private request credentials, but those credentials are excluded from equality, representation, serialization, logs, and VDOM payloads.

- App identity uses Databricks unified authentication and may reuse one guarded connection.
- User identity uses the forwarded `x-forwarded-access-token` and opens an operation-scoped connection that is always closed.
- Hybrid mode selects user identity when a forwarded user token is present and otherwise uses app identity.
- A user connection is never inserted into a process-global or cross-session cache.
- Callers can inject a connection factory or service adapter for testing and local development.

The SQL module owns connection creation and lifecycle. Query helpers acquire a connection through a provider context manager so commit, rollback, close, and reuse rules are centralized. App-identity reuse is protected by a lock because the connector connection and cursors must not be used concurrently.

## Databricks service boundary

`brickflowui.databricks.services` provides small typed operations for catalog browsing, warehouse discovery, and job execution. It consumes the current private identity context and the existing Databricks SDK/SQL helpers. The services return plain serializable records and never return SDK objects or credentials.

The frontend never calls Databricks APIs directly. Application authors load data or trigger work in Python callbacks, then pass serializable state into components. This keeps authorization, retries, auditing, and secrets on the server.

## Component contracts

### CatalogBrowser

Accepts a normalized tree of catalogs, schemas, and tables plus `selected`, `loading`, `error`, `empty_message`, and `disabled`. Selection emits an opaque record containing the selected level and identifiers. Keyboard navigation and labelled controls are required.

### WarehouseSelector

Accepts warehouse records with `id`, `name`, and optional `state`, plus `selected_id`, `loading`, `error`, `empty_message`, and `disabled`. Selection emits only the selected warehouse ID.

### JobTrigger

Renders a server-driven job action with `status`, `run_id`, `loading`, `error`, and `disabled`. Clicking emits a `trigger` event; the Python callback performs the Databricks operation and updates component state. Completion remains a compatibility alias for applications that already supply it, but the browser does not poll Databricks or fabricate completion.

Every component exposes useful loading, empty, permission-denied, error, and retry-friendly states without showing raw server exceptions.

## Safe errors

Browser error messages use a stable public message and a random correlation ID. Full exception details and the correlation ID are recorded in server logs. Authentication and authorization responses may retain their intentionally public messages; arbitrary render and handler exceptions may not.

## Asset boundary

Local assets are allowed only beneath configured roots. The default root is the application working directory, preserving normal relative-path ergonomics while preventing accidental publication of arbitrary files elsewhere. The registry is bounded with least-recently-used eviction and validates that a requested asset still resolves beneath an approved root before serving it.

## Compatibility

Existing component constructors continue to work. New props are additive. Existing app identity remains the default. Existing environment-token behavior remains available for local development, but it is treated as app identity and never as a per-user credential.

## Verification

- Python tests prove token privacy, user/app connection lifecycle, concurrency locking, service normalization, asset containment, and error redaction.
- Frontend tests prove all three components render and dispatch correct events in normal, loading, empty, disabled, and error states.
- Component parity must have no declared exceptions.
- Full Python, frontend, documentation, packaging, isolated-wheel, and browser gates must pass.
- A real Databricks Apps deployment remains an external release gate when credentials are unavailable locally.

## Non-goals

- Retaining or refreshing forwarded user tokens after their request/session context ends.
- Browser-side Databricks API calls.
- A general-purpose connection pool.
- Automatic background polling for job completion.
- Claiming real Databricks authorization verification without a deployed test workspace.
