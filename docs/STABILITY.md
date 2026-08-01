# Stability Contract

BrickflowUI 0.1.13 targets Python 3.10, 3.11, 3.12, and 3.13. Each release claim is limited to the interpreters actually exercised by CI or the release report.

## Supported runtime contract

- The production React frontend bundle is mandatory. A complete wheel includes `brickflowui/frontend/dist/index.html` and its referenced hashed assets.
- If those files are missing, the server returns HTTP 503 with an actionable diagnostic. It does not start a partial fallback renderer or open a WebSocket.
- Python VNodes, serialized event props, patch operations, browser navigation, and session-scoped state form one versioned runtime contract and must be tested together.
- A stable release means no known reproducible critical or high-severity defect remains in the supported core paths. It is not a security certification or a guarantee that no undiscovered defect exists.

## Local verification

From the repository root:

```text
python -m pytest -q -p no:cacheprovider
python scripts/generate_component_reference.py
git diff --exit-code -- docs/components/reference
python -m mkdocs build --strict
python -m build
```

From `frontend/`:

```text
npm ci
npm test -- --run
npm run lint
npm run typecheck
npm audit --audit-level=high
npm run build
```

Release verification additionally inspects the wheel and source distribution, installs the wheel into an isolated environment, starts a minimal application outside the source tree, and checks browser load, WebSocket interaction, direct links, reconnect behavior, theme switching, narrow layouts, and browser-console errors.

## Known capability boundaries

- `CatalogBrowser`, `WarehouseSelector`, and `JobTrigger` have server-driven renderer, loading, empty, disabled, error, and event contracts. Databricks operations remain explicit Python calls so credentials and SDK objects never enter the browser.
- Per-user and shared-app identity are both supported. User SQL/SDK clients are operation-scoped from forwarded authorization headers; the guarded app-identity SQL connection is reusable. A deployment must still configure and verify the required Databricks authorization scopes.
- Formal concurrency, load, long-running-session, and deployed Databricks Apps validation are separate production-lifecycle gates.
- Browser and platform results are recorded in the current verification report; unavailable infrastructure is reported as a limitation rather than inferred as passing.
