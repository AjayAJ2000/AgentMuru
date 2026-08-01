# BrickFlowUI Release Hardening Design

**Date:** 2026-08-01  
**Status:** Approved design, pending implementation plan  
**Scope:** Locally automatable release confidence plus an explicit Databricks workspace evidence path

## Goal

Close the actionable gaps from the 2026-07-31 end-user QA pass without turning ordinary pull-request CI into a slow or credential-dependent system. The result must prove supported Python versions, common accessibility rules, WebSocket reconnect/session hygiene, bounded local concurrency, representative browser behavior, and frontend bundle budgets. Databricks-only claims must require real workspace evidence.

## Design principles

- Fast deterministic checks run on every pull request.
- Chromium, load, and workspace checks are separate release gates.
- Credentials are never required for ordinary contributors.
- A missing external prerequisite produces a clear blocked result, never a false pass.
- Existing public APIs remain compatible.
- New behavior is implemented test-first and every threshold is explicit.

## 1. Python compatibility matrix

The existing `validate` CI job remains the full frontend, documentation, generated-reference, and packaging gate on Python 3.11. Python unit tests move into a dedicated matrix job for Python 3.10, 3.11, 3.12, and 3.13.

The matrix job will:

1. install `.[dev]`;
2. run `python -m pytest -q -p no:cacheprovider`;
3. avoid Node, MkDocs, and package builds so each matrix entry remains focused.

The full `validate` job will stop duplicating pytest after the matrix owns it. This makes the supported-version contract visible and keeps failures attributable to a specific Python version.

## 2. Accessibility and representative browser gate

Add a separate Playwright-based browser suite rather than trying to infer accessibility from serialized VNodes or JSDOM. The suite will use `@playwright/test` and `@axe-core/playwright` with Chromium.

Two maintained examples will be exercised:

- `examples/counter/app.py` for the minimal interaction and generated-starter shape;
- `examples/component_studio/app.py` for broad component rendering.

Checks will cover:

- meaningful content replaces the loading screen;
- no browser console errors or failed same-origin assets;
- primary headings and named controls exist;
- the counter changes exactly once per click;
- Axe reports no serious or critical violations;
- document width does not exceed viewport width at `390x844`;
- native keyboard Tab navigation reaches an interactive control;
- component studio renders a defined set of representative component labels.

Browser QA will live in its own workflow triggered by `workflow_dispatch`, a weekly schedule, and pushes to `main`. It will not block every pull request. The workflow installs the package, builds the frontend, installs Chromium, starts the two examples on isolated ports, and runs `npm run test:e2e`.

Color contrast remains a real-browser Axe check. The suite must not disable serious or critical rules merely to make the gate pass; any narrowly excluded rule requires a comment explaining the unsupported runtime condition.

## 3. WebSocket reconnect and session reliability

The current frontend reconnect loop uses a fixed 2.5-second retry and can schedule work from `onclose` after component disposal. Replace this implicit behavior with a small testable reconnect policy module.

The policy will provide:

- delays of 500 ms, 1 s, 2 s, 4 s, 8 s, then a 10 s cap;
- attempt reset after a successful open;
- at most one pending reconnect timer;
- no reconnect scheduled after disposal;
- pending UI events cleared on disconnect.

`App.tsx` will consume the policy while keeping existing user-visible connection states and messages.

Python integration tests will prove:

- session and route dictionaries are empty after disconnect;
- effect cleanup runs on disconnect;
- state from one WebSocket session never appears in another;
- repeated connect/disconnect cycles do not grow session registries;
- several simultaneous sessions can render and update independently.

The deterministic session tests remain part of normal pytest CI.

## 4. Bounded runtime resilience command

Add `scripts/runtime_resilience.py` as a release-oriented local command. It will start the counter example on an isolated port, connect multiple real WebSocket clients, trigger counter events, disconnect, reconnect, and report structured results.

Defaults:

- 20 concurrent sessions;
- 3 reconnect cycles;
- 30-second total command deadline;
- zero tolerated protocol failures;
- event round-trip p95 below 1,000 ms on the local release runner.

All values are configurable through CLI flags. Output includes session count, successful events, reconnects, failures, median latency, p95 latency, and total duration. The process always terminates the child server in a `finally` block. Tokens, headers, and payload secrets are never printed.

The browser/release workflow will run a smaller deterministic profile of 10 sessions and 2 reconnect cycles. Maintainers can run the defaults locally before a release.

## 5. Databricks workspace validation harness

Local mocks cannot prove Databricks OAuth, resource permissions, or forwarded identity. Add `scripts/validate_databricks_workspace.py` and `docs/DATABRICKS_RELEASE_VALIDATION.md` to turn that external requirement into a repeatable evidence collection step.

The command accepts:

- an app URL;
- two Databricks CLI profile names representing users with different permissions;
- expected catalog, warehouse, and job identifiers;
- an output JSON path under an ignored directory.

It uses the optional Databricks SDK to record, for each profile:

- authenticated subject identity;
- catalog visibility result;
- warehouse visibility result;
- job visibility result;
- root app HTTP status when an authenticated request can be made with the profile configuration.

The harness redacts hosts to their origin, never prints or serializes tokens, and returns nonzero when identities collapse to the same subject, expected permission differences are absent, a required resource check fails, or configuration is incomplete. It does not trigger a job or execute SQL by default; those state-changing checks remain explicit manual checklist items.

When the optional Databricks dependencies, profiles, or app URL are missing, the command exits with a clear prerequisite error. CI will not treat this as a pass, and ordinary CI will not invoke the command.

## 6. Frontend bundle budgets

The current Plotly chunk is already lazy and separate. Add a bundle-budget command that prevents silent regressions without forcing a risky visualization rewrite.

Initial uncompressed ceilings:

- entry chunk: 850 KB;
- charts chunk: 1.1 MB;
- Plotly chunk: 7.5 MB;
- vendor chunk: 250 KB.

The checker discovers the hashed files by prefix, fails when a required chunk is missing or duplicated, and reports actual versus allowed bytes. `npm run check:bundle` runs after the Vite build in full CI and publish validation.

## Error handling and reporting

- CI matrix failures identify the Python version.
- Browser failures retain Playwright traces and screenshots as workflow artifacts.
- Runtime resilience failures print bounded diagnostics and exit nonzero.
- Databricks validation writes redacted JSON evidence and exits nonzero on incomplete proof.
- Bundle-budget failures name the offending chunk and overage.

No gate retries indefinitely. Server startup, browser navigation, WebSocket events, and release commands all have bounded deadlines.

## Files and boundaries

Expected new files:

- `frontend/playwright.config.ts`
- `frontend/e2e/framework.spec.ts`
- `frontend/src/runtime/reconnect.ts`
- `frontend/src/runtime/reconnect.test.ts`
- `frontend/scripts/check-bundle-budget.mjs`
- `tests/test_runtime_resilience.py`
- `scripts/runtime_resilience.py`
- `scripts/validate_databricks_workspace.py`
- `docs/DATABRICKS_RELEASE_VALIDATION.md`
- `.github/workflows/browser-qa.yml`

Expected modified files:

- `.github/workflows/ci.yml`
- `.github/workflows/publish.yml`
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/src/App.tsx`
- `tests/test_app_server.py`
- `DEVELOPMENT.md`
- `docs/STABILITY.md`

The reconnect policy module owns retry state only. The Python resilience command owns process and client orchestration only. The Databricks harness owns external evidence collection only. Browser tests consume public UI behavior and must not depend on private React structure.

## Acceptance criteria

The hardening pass is complete when:

1. Python tests pass on 3.10, 3.11, 3.12, and 3.13 in CI configuration.
2. Existing and new Python/frontend tests pass locally on the available runtime.
3. Reconnect policy tests prove backoff, reset, single-timer, and disposal behavior.
4. Session reliability tests prove cleanup and isolation across repeated/concurrent clients.
5. Chromium checks pass for counter and component studio at desktop and mobile sizes.
6. Axe reports no serious or critical violations on the audited surfaces.
7. The bounded resilience command passes its CI profile and terminates all child processes.
8. Bundle budgets pass against a fresh Vite build.
9. Databricks validation fails safely without prerequisites and documents the exact real-workspace procedure.
10. Strict docs, package build, Twine, generated references, and the existing 17-example smoke sweep remain green.

## Non-goals

- Claiming formal WCAG conformance.
- Automatically deploying or modifying a Databricks App.
- Triggering jobs, executing SQL, changing workspace permissions, or storing credentials.
- Replacing Plotly or redesigning charts in this pass.
- Claiming multi-process production capacity from a bounded local test.
- Visually snapshotting every component state.

