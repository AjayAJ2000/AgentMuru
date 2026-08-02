# Stability Contract

BrickflowUI `0.1.17` is an alpha framework with a tested core-runtime baseline. “Stable” here means that the supported verification gates pass and there are no known reproducible core defects at release time. It is not a claim that undiscovered defects are impossible, nor is it a security or regulatory certification.

## Supported baseline

- Python 3.10, 3.11, 3.12, and 3.13 are supported package targets. CI runs the core
  test, Ruff, and MyPy gates on every supported Python version; the complete
  frontend, documentation, example-smoke, bundle-drift, and package integration
  gate runs on Python 3.11.
- The backend is FastAPI/Starlette and the browser runtime is the packaged React production build.
- Published wheels must contain `brickflowui/frontend/dist/index.html` and its referenced hashed assets.
- A source checkout must run `npm ci` and `npm run build` in `frontend/` before it can serve an application.
- If the frontend bundle is missing, BrickflowUI returns an actionable HTTP 503 diagnostic. It does not expose the old incomplete fallback renderer.

## Release gates

Run from the repository root:

```powershell
python -m pytest -q -p no:cacheprovider
python scripts/smoke_examples.py
python scripts/runtime_resilience.py
python scripts/generate_component_reference.py
git diff --exit-code -- docs/components/reference
python -m mkdocs build --strict
python -m build
```

Run from `frontend/`:

```powershell
npm ci
npm test -- --run
npm run lint
npm run typecheck
npm run build
npm run test:bundle
npm run check:bundle
npm run test:e2e
git diff --exit-code -- ..\brickflowui\frontend\dist
npm audit --audit-level=high
```

The release is not ready when a supported-Python test, lint, type-check, example
smoke, build, committed-bundle drift, documentation-drift, package-content, or
high-severity runtime dependency gate fails.

## Browser verification

A representative multi-page application must pass:

- initial page load and WebSocket connection;
- event dispatch and incremental state patching;
- direct deep links;
- repeated user navigation and browser Back/Forward operations;
- reconnect after a forced WebSocket closure;
- table sorting, pagination, and CSV export;
- standalone and table progress indicators with proportional width and a non-transparent computed color;
- chat typing, IME composition, and submission;
- light/dark theme switching;
- desktop and narrow viewport smoke tests;
- a console check with no uncaught exceptions.

## Security boundaries

BrickflowUI escapes application titles and favicon attributes, embeds loading configuration as inert JSON data, prevents configured CSS from terminating its style element, validates scaffold targets, validates WebSocket origins, requires CSRF tokens for browser-like unsafe HTTP requests, and neutralizes spreadsheet formulas in CSV exports.

The runtime accepts event handlers from only the current and immediately previous render generations. This narrow compatibility window preserves ordered browser events such as ChatInput's final change plus submit without retaining stale handlers indefinitely.

Theme files and application configuration are trusted developer inputs. Authentication supports both user identity and shared application identity; deployment owners must configure the mode and provider appropriate for their environment.

## Known capability boundaries

- `CatalogBrowser`, `WarehouseSelector`, and `JobTrigger` have server-driven renderer, loading, empty, disabled, error, and event contracts. Databricks operations remain explicit Python calls so credentials and SDK objects never enter the browser.
- Per-user and shared-app identity are both supported. User SQL/SDK clients are operation-scoped from forwarded authorization headers; the guarded app-identity SQL connection is reusable. A deployment must still configure and verify the required Databricks authorization scopes.
- CI exercises Python 3.10 through 3.13. Local evidence may cover only the interpreters installed on the release workstation.
- A bounded 20-session reconnect campaign is part of local validation. Sustained load, multi-process deployment, backpressure, and long-session memory campaigns remain production-lifecycle gates.
- The Chromium end-user gate covers the counter and component studio at desktop and mobile widths, including serious/critical Axe checks. Cross-browser and formal accessibility conformance testing remain separate gates.
- Live Databricks evidence is collected with the read-only procedure in [Databricks Release Validation](./DATABRICKS_RELEASE_VALIDATION.md); unavailable infrastructure is never inferred as passing.
- Browser and platform results are recorded in the current verification report; unavailable infrastructure is reported as a limitation rather than inferred as passing.

## Reporting a regression

Open a GitHub issue with the BrickflowUI version, Python and Node versions, operating system, minimal reproduction, complete traceback or browser-console error, and whether the failure occurs from source or an installed wheel. A regression fix must include a test that fails before the fix and passes afterward.
