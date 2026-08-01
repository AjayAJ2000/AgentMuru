# Roadmap

This roadmap focuses on making BrickflowUI feel dependable in enterprise dashboard, portal, and internal-tool scenarios while keeping the framework practical for Python-first builders.

It is shaped by both BrickflowUI's current direction and recurring pain seen in similar frameworks and internal-tool platforms.

## What Similar Products Keep Getting Wrong

Recurring themes from public issues and community feedback around similar tools:

- frequent rerenders and callback fan-out can make large apps feel laggy
- tables and editors often lose scroll position or interaction context after refreshes
- loading states are inconsistent when data is driven by variables instead of direct query bindings
- mobile behavior is often an afterthought for admin and internal tools
- auth and RBAC are usually treated as deployment workarounds instead of first-class framework concepts
- proxy, CSP, and enterprise deployment constraints surface late and become release blockers

These are not edge cases. They are the problems teams run into when they try to move from a demo to a real operational portal.

## Immediate Direction

The near-term goal is not to make BrickflowUI "feature busy." It is to make the framework more reliable, more scalable, and more deployment-ready while continuing to broaden the product surface in additive ways.

## Next Update Tracks

### Track 1: Runtime Performance And Large-State UX

Priority themes:

- reduce avoidable rerenders further
- preserve local interaction state across backend-driven updates
- improve table and editor behavior under heavy use
- make loading and optimistic interactions more predictable

Expected work:

- table scroll and focus preservation after patch updates
- optional pagination helpers and dataset slicing patterns
- more granular patch/update strategies for high-frequency components
- better instrumentation hooks for event latency and render timing

### Track 2: Enterprise App Shells

Priority themes:

- make professional app layouts easier to build without custom frontend work
- improve navigation patterns for portals and admin tools
- tighten mobile and tablet behavior

Expected work:

- more complete app-shell primitives
- better left-nav and top-nav composition patterns
- denser admin/dashboard layout options
- improved responsive behavior for data-heavy pages
- premium visual primitives for design-led surfaces:
  - `IconButton`
  - `SegmentedControl`
  - `Stack` / overlay helper
  - `AspectFrame`
  - glass surface tokens
  - richer display typography control
  - breakpoint-aware shell helpers for desktop-first composition
  - stronger image framing and hero-media placement controls

### Track 3: Security, Identity, And Governance

Priority themes:

- make secure defaults easier
- improve auth and role-aware app patterns
- document governance and deployment expectations clearly

Expected work:

- stronger examples for role-gated pages and route protection
- clearer patterns for internal versus external users
- better maintainer docs for GitHub repo hardening and release governance
- more explicit deployment guidance for enterprise environments

### Track 4: Data Product Surface

Priority themes:

- support more production dashboard use cases directly
- improve interactive analytics workflows
- make pipeline and operational views first-class

Expected work:

- better table drilldown and row detail patterns
- richer chart interactions and linked views
- more pipeline, DAG, status, and workflow representations
- more polished export and refresh behaviors

## Proposed Release Shape

### `0.1.13`

Current stability baseline:

- session cleanup, origin checks, trusted-host support, security headers, and safer API fallback behavior
- nested render-context restoration and deterministic VDOM child-removal ordering
- explicit missing-frontend diagnostics and HTML-safe shell/bootstrap embedding
- validated CLI scaffold targets
- browser-history, patch-protocol, CSV export, and IME regression coverage
- frontend tests, lint, type-check, build, Python tests, docs drift, and package build as CI gates

### `0.2.0`

Recommended focus:

- unify public API naming where it is still inconsistent
- formalize preferred composition patterns
- tighten visual-state conventions across components
- ship a migration guide for any intentional cleanup
- validate app/user authorization and Databricks components in a real Apps workspace
- add sustained-load, multi-process, and long-session lifecycle verification

## The Product Standard

The framework should be able to support:

- a serious executive dashboard
- an operational pipeline portal
- a secure internal admin tool
- a branded customer or partner-facing workspace

without the user having to break out of the library for core UX, security, or deployment expectations.

That is the bar the roadmap should keep serving.

## Delivery Process

Operationally, roadmap work should move through:

- `dev` for active integration
- `test` for validation and release-candidate hardening
- `main` for production release

That keeps product evolution fast without making public release quality accidental.

