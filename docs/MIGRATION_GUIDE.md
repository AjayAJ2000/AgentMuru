# Migration Guide

Use this page when you are upgrading an existing BrickflowUI app and want to know what to validate before calling the upgrade done.

## General Upgrade Checklist

After every upgrade:

1. retest your main navigation shell on desktop and mobile
2. retest all user inputs that sync state back to Python
3. verify loading behavior on the controls that trigger backend work
4. verify custom branding, logos, and loading assets
5. run your app against the current [Examples](./EXAMPLES.md) and [API Reference](./API_REFERENCE.md)

## Upgrading To 0.1.17

Version `0.1.17` preserves the public component API while strengthening runtime,
browser, security, and release-validation behavior.

Recheck these areas:

- rebuild pinned containers and Databricks App bundles with
  `brickflowui>=0.1.17`
- exercise reconnect behavior and event-driven updates in long-lived pages
- retest modals, popups, keyboard interaction, and mobile layouts with your
  application-specific content
- validate per-user and shared-app identity scopes in the target Databricks
  workspace; local tests do not substitute for live authorization evidence
- run the Python, frontend, example-smoke, resilience, strict-docs, package, and
  browser gates from the [Release Checklist](./RELEASE_CHECKLIST.md)

## Upgrading To 0.1.16

Version `0.1.16` preserves the public component API while consolidating the
showcase surface and hardening the flagship operational workflow.

Recheck these areas:

- update local scripts to launch source examples as modules from the repository
  root so they resolve the checked-out runtime
- replace retired example links with the maintained inventory in
  `examples/manifest.json`
- exercise the Pipeline Command Center navigation, Executive Brief modal,
  filters, graph interactions, triage actions, and assistant simulation
- rebuild pinned containers and application bundles with
  `brickflowui>=0.1.16`
- run the full frontend, Python, docs, package, installed-wheel, and browser
  acceptance matrix from the [Release Checklist](./RELEASE_CHECKLIST.md)

## Upgrading To 0.1.15

Version `0.1.15` is additive for existing component APIs and introduces complete
server-driven contracts for the Databricks catalog, warehouse, and job controls.

Recheck these areas:

- exercise both per-user and shared-app identity modes in the target Databricks
  Apps workspace, including denied and expired-credential paths
- verify forwarded authorization and user headers are supplied only by the
  trusted deployment boundary
- retest catalog selection, warehouse selection, job triggering, loading,
  empty, disabled, and error states
- rebuild pinned containers and application bundles with
  `brickflowui>=0.1.15`
- run the full frontend, Python, docs, package, installed-wheel, and browser
  acceptance matrix from the [Release Checklist](./RELEASE_CHECKLIST.md)

## Upgrading To 0.1.14

Version `0.1.14` is a protocol-compatible patch release. No component API
changes are required.

Recheck these areas:

- switch repeatedly between routed pages whose content trees have very different
  child counts
- use browser Back and Forward after those page switches
- confirm no `Runtime protocol error` banner appears and the WebSocket remains
  connected
- rebuild pinned containers and Databricks App deployments with
  `brickflowui>=0.1.14`

## Upgrading To 0.1.13

Recheck these areas:

- packaged frontend
  - rebuild source checkouts with `npm ci && npm run build` from `frontend/`
  - confirm the wheel or deployment contains `brickflowui/frontend/dist/index.html` and every referenced hashed asset
- navigation
  - exercise direct deep links, sidebar/top-nav clicks, and repeated browser Back/Forward operations
- exports and chat
  - verify CSV consumers accept the UTF-8 BOM and formula-neutralized cells
  - verify CJK input methods confirm composition without submitting ChatInput prematurely
- custom branding
  - confirm title, favicon, loading configuration, and theme tokens still render as intended
- progress indicators
  - verify progress fills are visible and proportional to `value / max`
  - friendly colors now resolve through theme tokens; explicit CSS colors remain supported
- development automation
  - add `npm test -- --run` and `npm run lint` to custom CI pipelines that previously ran only the frontend build

The incomplete fallback renderer was removed intentionally. A missing production frontend now returns HTTP 503 with build instructions rather than pretending that the application is healthy.

## Upgrading To 0.1.12

Recheck these areas:

- theme behavior
  - the framework now expects light-first defaults unless dark is explicitly configured
- loading identity
  - confirm your custom loading title, message, asset, and mode-specific configuration still render correctly
- media
  - retest `Image`, `Video`, and `Embed` behavior if you use local assets
- examples and scaffolds
  - prefer the newer examples as reference instead of older ad hoc experiments

## Upgrading To 0.1.11

Recheck these areas:

- input sync strategy
  - `Input` and related controls moved toward smoother local-first behavior
- loading controls
  - verify component-level loading states rather than relying only on page-level cues
- responsive layouts
  - retest sidebars, tabs, dense control bars, and modal flows on narrow widths

## If You Built Local Workarounds

If you previously added app-level workarounds for:

- typing lag
- dark-mode defaults
- custom loading screens
- mobile shell behavior

review whether the framework now covers that behavior directly. Removing old workarounds can simplify your app code after upgrade.

## What To Compare During Migration

The best reference set during upgrades is:

1. [API Reference](./API_REFERENCE.md)
2. [Examples](./EXAMPLES.md)
3. [Local Development](./LOCAL_DEVELOPMENT.md)
4. [Troubleshooting](./TROUBLESHOOTING.md)

## When To Pause An Upgrade

Pause and inspect more carefully if:

- a custom theme suddenly looks different
- your app depends on very dense interaction patterns
- you rely on secured routes or custom auth integration
- you serve local media or embeds in stricter environments

That does not necessarily mean the upgrade is unsafe. It means those are the highest-value regression zones to validate first.
