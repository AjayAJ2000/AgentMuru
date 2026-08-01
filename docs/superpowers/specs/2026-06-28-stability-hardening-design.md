# BrickflowUI Stability Hardening Design

**Date:** 2026-06-28  
**Status:** Proposed for implementation  
**Target:** BrickflowUI `0.1.13` on the `dev` branch

## Objective

Bring BrickflowUI to a defensible stable-product baseline: zero known reproducible defects in the supported core runtime, explicit behavior when optional assets are unavailable, automated regression coverage for backend and frontend behavior, and a repeatable release-verification record.

This work cannot honestly guarantee that no undiscovered bug exists. Completion means every confirmed defect in this specification is fixed, all agreed verification gates pass, and any residual limitation is documented rather than hidden.

## Scope and sequencing

The work is divided into independently verifiable projects so that failures can be isolated and reviewed.

1. **Core stability hardening (this specification):** navigation, render-context correctness, fallback behavior, shell escaping, CLI path safety, CSV export safety, IME behavior, frontend patch robustness, tests, documentation, and release checks.
2. **Databricks component integration (follow-up specification):** make `CatalogBrowser`, `WarehouseSelector`, and `JobTrigger` functional end to end. Adding cosmetic renderer cases without data contracts is explicitly rejected.
3. **Production lifecycle hardening (follow-up specification):** load testing, session observability, configurable connection/session policy, and deployment-specific validation on Databricks Apps.

Only project 1 is implemented under this specification. Projects 2 and 3 follow the same design, test, and verification gates before the product is declared stable for their respective capabilities.

## Confirmed defects addressed

### Browser navigation

`frontend/src/App.tsx` currently uses the same function for user navigation and `popstate` synchronization. Because the function always calls `history.pushState`, browser Back and Forward operations add new entries.

The frontend will separate these operations:

- user-initiated navigation sends the path and pushes history;
- browser-history synchronization sends the already-selected path without mutating history;
- navigation preserves the pathname, search string, and hash where applicable;
- navigation is testable without establishing a real WebSocket connection.

### Render context restoration

`set_render_context` returns a `ContextVar` token, but render paths discard it and set the context to `None`. The state module will expose token-based restoration, and both full and patch render paths will restore the prior context in `finally` blocks. This prevents nested render contexts from being overwritten and follows the Python `contextvars` contract.

### Missing frontend bundle behavior

The fallback shell currently presents itself as a functional renderer while silently ignoring incremental patches and omitting the deep-link path. Maintaining a second incomplete frontend runtime would duplicate the React renderer and remain a permanent correctness risk.

When `brickflowui/frontend/dist/index.html` is unavailable, the server will instead return a clear diagnostic page that:

- states that the frontend bundle is missing;
- provides the exact supported build/install remedy;
- does not open a WebSocket or pretend to render the application;
- preserves safe branding and loading presentation where useful;
- returns a server-error status so automated probes cannot mistake it for a healthy application.

Packaged wheels and source distributions will be tested to ensure the real frontend bundle is included, making the diagnostic an exceptional development/install failure path.

### HTML and configuration boundaries

Application titles, favicon URLs, bootstrap JSON, and generated theme CSS are inserted into the HTML shell. The implementation will use context-appropriate escaping and safe JSON embedding so configuration values cannot terminate their containing HTML element.

Theme values remain developer-controlled CSS values. The hardening boundary prevents HTML element termination and control-character injection without imposing a restrictive color-only grammar that would break supported gradients, shadows, font stacks, and CSS functions.

### CLI target safety

`brickflowui new` will accept a single project-directory name, reject absolute paths, parent traversal, path separators, empty/dot names, and Windows-reserved names, and verify that the resolved target remains directly below the current working directory. Validation occurs before any filesystem mutation.

### CSV export safety

Table CSV generation will move into a pure, testable helper. It will:

- quote headers and cells according to CSV rules;
- double embedded quotes;
- neutralize spreadsheet formulas beginning with `=`, `+`, `-`, `@`, tab, or carriage return after leading whitespace handling;
- use CRLF row endings and a UTF-8 BOM for spreadsheet compatibility;
- preserve ordinary numeric and textual values.

### IME-safe chat submission

`ChatInput` will not submit when Enter is used to confirm an active input-method composition. It will also prevent the browser's default submission behavior only for an actual BrickflowUI submit action.

### Patch robustness

Frontend patch application will be extracted into a pure module and tested for root replacement, prop updates, insertion, removal, nested updates, and invalid paths. Invalid server patches will not crash the UI or mutate an unrelated node. They will produce a controlled diagnostic and trigger a full-state recovery strategy rather than silently corrupting the client tree.

## Findings intentionally not treated as defects

- Event-handler registries are rebuilt on each render and are not unbounded.
- WebSocket sessions are removed in a `finally` block; a configurable lifecycle policy belongs to production lifecycle hardening rather than this bug fix.
- VDOM text values are props and are already included in prop diffs.
- Navigation cleanup clears effect records, and render indices are reset before every render.
- Missing `Origin` is permitted for non-browser clients; browser-like unsafe requests with the CSRF cookie still require the matching header.
- Conditional hook calls violate hook ordering rules. Documentation and future development-time diagnostics may improve this, but changing hook identity semantics is not part of this stability slice.
- Theme configuration is trusted developer input. This slice hardens the HTML boundary without pretending it is an end-user input channel.

## Architecture and file boundaries

### Frontend

- `frontend/src/runtime/applyPatch.ts`: pure VDOM patch application and typed failure result.
- `frontend/src/runtime/navigation.ts`: pure path/history decisions and WebSocket navigation message creation.
- `frontend/src/runtime/csv.ts`: pure CSV serialization and spreadsheet-formula neutralization.
- `frontend/src/App.tsx`: connection lifecycle and React state orchestration using the extracted runtime helpers.
- `frontend/src/Renderer.tsx`: component rendering; `ChatInput` delegates composition-safe submit decisions to a small helper where practical.
- `frontend/src/**/*.test.ts(x)`: Vitest tests colocated with runtime behavior.
- `frontend/vite.config.ts` and `frontend/package.json`: test runner configuration and scripts.

### Backend

- `brickflowui/state.py`: token-based render-context restoration.
- `brickflowui/server.py`: correct context restoration, safe HTML embedding, and explicit missing-bundle response.
- `brickflowui/cli/main.py`: project-name validation before scaffolding.
- `tests/test_state.py`, `tests/test_app_server.py`, and CLI tests: regression coverage for each backend behavior.

### Documentation and verification

- `docs/ROADMAP.md`: synchronize the current release and separate completed work from future focus.
- `docs/STABILITY.md`: supported stability claim, verification gates, and known limitations.
- `.github/workflows/ci.yml`: run frontend tests in addition to build, Python tests, docs, and package build.
- a final verification report records exact commands, results, browser scenarios, and residual limitations.

## Error handling and recovery

- A missing frontend bundle fails visibly and returns a non-success HTTP status.
- Invalid frontend patches never apply to a sibling or truncated path. The client reports the protocol error and reconnects to obtain a full tree.
- Navigation only updates browser history after the navigation message can be sent.
- CLI validation fails before directory creation and gives a specific actionable message.
- Escaping is performed at the output boundary, preserving internal configuration values.

## Testing strategy

### Test-driven implementation

Every behavior change begins with a focused failing test. Each test is run in isolation to confirm the expected failure before production code changes, then rerun after the minimal fix.

### Backend gates

- full `python -m pytest -q` suite;
- targeted state, server, auth/CSRF, VDOM, theme, CLI, and packaging tests;
- wheel and source-distribution build;
- install the built wheel into an isolated environment and import/run a minimal app;
- verify packaged frontend files are present.

### Frontend gates

- Vitest unit/component suite;
- TypeScript/Vite production build;
- ESLint with zero errors;
- tests for navigation, all patch operations and invalid paths, CSV injection cases, and IME composition;
- no console errors during browser scenarios.

### Browser gates

Using a locally started example application:

- initial load and WebSocket connection;
- state update and incremental patch rendering;
- multi-page navigation plus repeated Back/Forward operations;
- reconnect after forced WebSocket closure;
- table sort, pagination, and CSV export;
- chat input typing, IME composition simulation, and submission;
- light/dark theme switching;
- responsive desktop and narrow viewport smoke tests;
- direct deep link to a non-root page;
- visible missing-bundle diagnostic tested separately.

### Security and quality gates

- existing security tests and GitHub workflow configuration remain green;
- shell title/bootstrap/theme termination payloads are regression tested;
- CLI traversal cases are regression tested;
- CSV formula cases are regression tested;
- dependency audit results are recorded and actionable high/critical findings are resolved or explicitly blocked with evidence;
- generated docs and component reference pages show no drift.

## Acceptance criteria

Project 1 is complete only when:

1. Every confirmed defect in this specification has a regression test and a passing fix.
2. Python tests, frontend tests, lint, frontend production build, docs build, and package build all pass.
3. The built package contains and serves the production frontend.
4. The browser scenario matrix passes without uncaught exceptions or console errors.
5. CI runs the new frontend tests.
6. Documentation accurately distinguishes supported behavior, exceptional fallback behavior, and follow-up Databricks/lifecycle work.
7. A final residual-risk audit finds no known reproducible core defect. Any unresolved external or environment-specific issue is documented with reproduction evidence and impact.

## Non-goals for this project

- Claiming formal security certification or regulatory compliance.
- Implementing a second fallback VDOM renderer.
- Adding polling, reducers, uploads, Markdown, plugins, or other roadmap features unrelated to confirmed stability defects.
- Shipping nonfunctional visual shells for Databricks components.
- Redesigning the public component API before the `0.2.0` compatibility plan.

## Follow-up stability projects

After this project passes its acceptance gates, the next specification will define real data contracts, authentication behavior, loading/error states, and browser tests for `CatalogBrowser`, `WarehouseSelector`, and `JobTrigger`. The final production-lifecycle project will then validate concurrency, session policy, observability, load behavior, and an actual Databricks Apps deployment.
