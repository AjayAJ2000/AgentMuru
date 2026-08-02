# Roadmap

BrickflowUI's roadmap prioritizes dependable enterprise dashboards, portals,
and internal tools while keeping the framework practical for Python-first
builders. The executive roadmap tracks outcomes; task-level implementation
detail belongs in the linked issues and pull requests.

## Current Production Baseline: 0.1.17

BrickflowUI 0.1.17 is the current production baseline. The following behavior
is shipped and covered by local or CI verification:

- Python 3.10–3.13 compatibility gates;
- session-scoped state, reconnect recovery, and bounded multi-session
  resilience checks;
- maintained desktop and mobile browser journeys with Playwright and Axe
  checks for serious and critical accessibility findings;
- frontend build drift checks, dependency audits, and enforced bundle budgets;
- validated WebSocket origins and browser CSRF boundaries, hardened HTML and
  media configuration, fail-closed authentication errors, and safer
  incremental patch values;
- Databricks service contracts plus tested, read-only tooling for collecting
  sanitized identity, catalog, warehouse, and job metadata evidence;
- an explicit Ruff lint policy selecting `E4`, `E7`, `E9`, and `F`; and
- release gates covering tests, browser QA, documentation, package builds,
  trusted PyPI publishing, and digital attestations.

### Verification Boundary

The repository verifies framework behavior, security boundaries, packaging,
browser journeys, and the Databricks evidence collector locally and in CI.
That evidence does not prove behavior inside a real Databricks workspace.

Until workspace evidence is collected and reviewed, BrickflowUI does not claim
that real Databricks OAuth, Unity Catalog permissions, SQL warehouse access,
or job execution has passed. The shipped evidence workflow is deliberately
read-only: it does not deploy an app, execute SQL, run a job, change grants, or
mutate workspace resources.

## Next Milestone: 0.2.0

0.2.0 remains the next compatibility and product milestone. Recommended
implementation order follows the current outcome-level roadmap issues.

### A. Production Evidence And Delivery Maintenance

- [#43: Validate identity and authorization in real Databricks Apps deployments](https://github.com/AjayAJ2000/brickflowUI/issues/43)
- [#44: Validate sustained load, multi-process operation, and long-running sessions](https://github.com/AjayAJ2000/brickflowUI/issues/44)
- [#45: Add production runtime observability and latency instrumentation](https://github.com/AjayAJ2000/brickflowUI/issues/45)
- [#46: Upgrade GitHub Actions to Node 24-compatible action versions](https://github.com/AjayAJ2000/brickflowUI/issues/46)

These outcomes establish production evidence, operating limits, diagnostic
visibility, and a maintained delivery foundation before the compatibility
contract is finalized.

### B. Compatibility Contract

- [#47: Standardize public APIs and publish the 0.2 migration guide](https://github.com/AjayAJ2000/brickflowUI/issues/47)

The 0.2 contract should align naming, preferred composition patterns,
visual-state conventions, deprecations, and validated migration guidance.

### C. Product Capability Improvements

- [#48: Preserve table focus and scroll during granular state patches](https://github.com/AjayAJ2000/brickflowUI/issues/48)
- [#49: Build responsive enterprise application-shell primitives](https://github.com/AjayAJ2000/brickflowUI/issues/49)
- [#50: Add first-class role-gated pages and route protection](https://github.com/AjayAJ2000/brickflowUI/issues/50)
- [#51: Add linked analytics, drilldowns, and polished refresh/export workflows](https://github.com/AjayAJ2000/brickflowUI/issues/51)
- [#52: Model pipelines, DAGs, and operational workflows](https://github.com/AjayAJ2000/brickflowUI/issues/52)

These epics improve data-heavy interaction stability, responsive application
shells, authorization, linked analytics, and operational workflow modeling.

## Product Standard

The framework should support a serious executive dashboard, an operational
pipeline portal, a secure internal admin tool, and a branded customer or
partner-facing workspace without requiring users to leave the library for core
UX, security, or deployment expectations.

## Delivery Process

Roadmap work moves through `dev` for active integration, `test` for release
candidate validation, and `main` for production releases. Release automation
must continue to reject commits that are not reachable from `main`.
