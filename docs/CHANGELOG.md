# Changelog

This page tracks the highest-signal changes for evaluators and adopters. It is not meant to replace commit history. It is meant to explain what changed, why it matters, and what to recheck when you upgrade.

## 0.1.17

Focus: end-user reliability, browser accessibility, safer runtime failure handling,
and broader release validation.

Highlights:

- Python 3.13 joins the CI compatibility matrix alongside Python 3.10–3.12
- WebSocket reconnect behavior, incremental VDOM patches, handler generations,
  and bounded session cleanup have expanded regression and resilience coverage
- authentication failures expose actionable status codes without leaking provider
  exception details, while media URLs and runtime error messages receive stricter
  browser-facing safety checks
- browser tests now cover desktop and mobile user journeys plus serious and
  critical Axe accessibility findings for maintained examples
- frontend bundle budgets, dependency auditing, generated-document drift, example
  smoke tests, and package-content checks are enforced together in release gates
- a read-only Databricks validation procedure records live-platform evidence
  separately from locally verified behavior

Upgrade notes:

- rebuild containers and Databricks App bundles with `brickflowui>=0.1.17`
- regenerate and commit the packaged frontend bundle when building from source
- validate identity and authorization scopes in the target Databricks workspace
- no existing public component constructor was intentionally removed

## 0.1.16

Focus: a smaller, end-to-end showcase foundation and a more resilient flagship
data-operations experience.

Highlights:

- the public example archive is consolidated into six maintained,
  manifest-listed applications with redundant and incomplete demos retired
- the Data Pipeline Command Center now demonstrates operational KPIs, filters,
  dependency flow, reliability signals, triage, simulated actions, and an
  assistant workflow from one normalized data boundary
- modal focus behavior, mobile navigation wrapping, queued event handling, and
  source-checkout launches have regression coverage across browser and server
  boundaries
- local example commands resolve the checked-out `0.1.16` runtime instead of a
  stale globally installed BrickflowUI package
- CI installs visualization dependencies wherever the full example suite runs,
  treats PowerShell reparse-point coverage as Windows-only, and upgrades audited
  packaging tools past known vulnerabilities

Upgrade notes:

- rebuild containers and Databricks App bundles with `brickflowui>=0.1.16`
- refresh source-checkout launch commands to use
  `python -m examples.data_pipeline_command_center.app`
- replace retired example links with the maintained entries in
  `examples/manifest.json`
- no existing public component constructor was intentionally removed

## 0.1.15

Focus: identity-safe Databricks integrations, complete server-driven Databricks
components, and stronger runtime/release boundaries.

Highlights:

- per-user Databricks SQL and SDK clients are operation-scoped from forwarded
  identity headers, while shared app-identity SQL access is health-checked and
  serialized for safe reuse
- `CatalogBrowser`, `WarehouseSelector`, and `JobTrigger` now have complete
  renderer, loading, empty, disabled, error, selection, and trigger contracts
- forwarded Databricks user identity is recognized without exposing access
  tokens in logs, repr output, equality, component props, or browser payloads
- local asset registration is root-bounded, size-limited, revalidated, and LRU
  evicted; browser runtime errors expose only a support correlation ID
- incremental patch handling supports nested prop updates, preserves one render
  generation of queued events, caches handler call shapes, and reconnects on
  invalid browser patches
- frontend tests, lint, type checks, dependency audit, committed-bundle drift,
  manifest-driven example smoke checks, strict docs, and package build are
  enforced in the Python 3.11 integration gate; Python tests, Ruff, and MyPy run
  across the supported Python 3.10, 3.11, and 3.12 matrix
- frontend dependencies and the packaged production bundle were refreshed with
  no known npm vulnerabilities at release preparation time

Upgrade notes:

- rebuild containers and Databricks App bundles with `brickflowui>=0.1.15`
- deployments using per-user identity must forward the supported authorization
  and user headers and grant the corresponding Databricks scopes
- validate both per-user and shared-app modes in your own Databricks Apps
  workspace; this release does not claim an external workspace certification
- no existing public component constructor was intentionally removed

## 0.1.14

Focus: reliable incremental rendering during routed page changes.

Highlights:

- child-list removals are now emitted from the highest index downward, so every
  patch remains valid as the browser applies the sequence
- switching from a page with many children to a smaller page no longer produces
  `Patch index ... is outside the child list` protocol errors
- strict frontend validation and reconnect recovery remain enabled for genuinely
  malformed or out-of-bounds patches
- regression coverage spans root and nested trees, all old/new child counts from
  zero through twelve, repeated large/small navigation, and concurrent sessions

Upgrade notes:

- upgrade runtimes that serve multi-page applications to `0.1.14`
- rebuild containers and Databricks App bundles so the Python runtime and
  packaged metadata report the same version
- no public component API changed in this patch release

## 0.1.13

Focus: core-runtime stability, browser correctness, safer exports and scaffolding, and enforceable release gates.

Highlights:

- browser Back/Forward synchronization no longer pushes duplicate history entries
- frontend VDOM patches are validated and fail closed with full-state reconnect recovery
- nested Python render contexts restore their previous `ContextVar` token correctly
- application title, favicon, theme CSS, and loading bootstrap values are embedded at safe HTML boundaries
- missing frontend assets return an actionable HTTP 503 instead of a frozen fallback renderer
- CSV export neutralizes spreadsheet formulas, uses a browser-safe download lifecycle, and emits Excel-friendly UTF-8 output
- ChatInput respects IME composition and preserves back-to-back change/submit events across one render generation
- progress fills now map friendly color names to defined theme tokens, so an 85 value visibly fills 85% instead of rendering transparent
- runtime version reporting now follows the source/package version instead of an unrelated globally installed release
- incremental patches recursively serialize VNodes nested in changed props
- `brickflowui new` rejects traversal, absolute, reserved, and unsafe scaffold targets before writing
- frontend Vitest and ESLint gates now run in CI alongside Python, docs, and package builds
- obsolete duplicate examples were removed in favor of the maintained flagship set

Upgrade notes:

- source checkouts must build the React frontend; missing assets are now an explicit deployment failure
- rebuild custom containers or Databricks App bundles so they include the `0.1.13` hashed frontend assets
- run the browser history, CSV export, and chat-input checks in [Stability Contract](./STABILITY.md)
- `CatalogBrowser`, `WarehouseSelector`, and `JobTrigger` remain experimental until their dedicated end-to-end Databricks contracts ship

## 0.1.12

Focus: framework hardening, stronger product surfaces, enterprise-facing docs, and broader example coverage.

Highlights:

- broader dashboard and workflow surface including pipeline, chat, kanban, status, and media patterns
- stronger loading, theming, and branded runtime behavior
- responsive shell improvements and richer example apps
- auth-aware docs and deployment guidance
- landing page, docs portal, and reference content expanded to better support evaluation

Upgrade notes:

- review your theme config if you depend on older dark-mode assumptions
- prefer the latest examples when adopting loading, media, and preset-driven theming

## 0.1.11

Focus: responsiveness, polish, and reliability in day-to-day builder flows.

Highlights:

- smoother typing and local-first input behavior
- stronger loading-state handling across interactive components
- improved shell behavior for mobile and denser layouts
- more polished examples and better scaffolding experience

Upgrade notes:

- if you built custom workarounds for input lag, revisit them against the current runtime
- retest mobile layout behavior in your main apps

## 0.1.10

Focus: stabilization and scalability-oriented runtime improvements.

Highlights:

- deferred frontend tree updates and smoother rerender handling
- better guidance around performance and local testing
- stronger docs on runtime behavior

## 0.1.9 and Earlier

The project moved through several rapid polish and capability passes in the `0.1.x` line. If you are upgrading from an older `0.1.x` release, use:

- [Migration Guide](./MIGRATION_GUIDE.md)
- [Examples](./EXAMPLES.md)
- [API Reference](./API_REFERENCE.md)

## Release Discipline Going Forward

Every user-visible library change should update:

- package version
- docs references
- example requirements
- scaffolded template requirements
- release-facing upgrade guidance
