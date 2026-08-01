# BrickFlowUI Release Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add enforced compatibility, reconnect/session reliability, accessibility/browser, resilience, Databricks evidence, and bundle-budget gates without burdening ordinary contributors with external credentials.

**Architecture:** Fast Python and frontend checks remain in pull-request CI. Chromium, bounded load, and Databricks workspace evidence use explicit release workflows or commands with hard timeouts and redacted output. Small pure helpers own reconnect policy, bundle discovery, statistics, and validation so each boundary is directly testable.

**Tech Stack:** Python 3.10–3.13, pytest, FastAPI TestClient, asyncio, websockets, React 18, TypeScript, Vitest, Playwright Chromium, Axe, GitHub Actions.

## Global Constraints

- Preserve the pre-existing changes in `brickflowui/vdom.py` and `tests/test_vdom.py`.
- Preserve the earlier QA changes in `brickflowui/cli/main.py` and `tests/test_cli.py`.
- Do not publish, deploy, trigger Databricks jobs, execute SQL, change permissions, or store credentials.
- Fast deterministic checks run on pull requests; Chromium/load/workspace checks remain separate release gates.
- Existing public Python and component APIs remain compatible.
- Every server, browser, WebSocket, and subprocess wait is bounded.
- Databricks tokens must never be printed, serialized into evidence, or committed.

---

### Task 1: Supported Python matrix and metadata

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `pyproject.toml`
- Modify: `docs/STABILITY.md`

**Interfaces:**
- Consumes: `python -m pytest -q -p no:cacheprovider` as the supported-runtime test contract.
- Produces: a `python-tests` matrix for `3.10`, `3.11`, `3.12`, and `3.13`; package/docs metadata matching that matrix.

- [ ] **Step 1: Add the Python test matrix**

Add this job before `validate` in `.github/workflows/ci.yml`:

```yaml
  python-tests:
    name: Python ${{ matrix.python-version }}
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.10", "3.11", "3.12", "3.13"]
    steps:
      - name: Check out repository
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install Python dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install -e .[dev]
      - name: Run Python tests
        run: python -m pytest -q -p no:cacheprovider
```

Remove the duplicate `Run tests` pytest step from `validate`.

- [ ] **Step 2: Align supported-version metadata**

Add the classifier below to `pyproject.toml`:

```toml
"Programming Language :: Python :: 3.13",
```

Change the opening stability sentence to:

```text
BrickflowUI 0.1.13 targets Python 3.10, 3.11, 3.12, and 3.13.
```

- [ ] **Step 3: Validate syntax and the available runtime**

Run:

```powershell
python -c "import pathlib,yaml; yaml.safe_load(pathlib.Path('.github/workflows/ci.yml').read_text(encoding='utf-8')); print('ci-yaml-ok')"
python -m pytest -q -p no:cacheprovider
```

Expected: YAML parses and all locally available Python tests pass.

- [ ] **Step 4: Commit the compatibility gate**

```powershell
git add .github/workflows/ci.yml pyproject.toml docs/STABILITY.md
git commit -m "ci: test supported Python versions"
```

### Task 2: Testable reconnect controller

**Files:**
- Create: `frontend/src/runtime/reconnect.ts`
- Create: `frontend/src/runtime/reconnect.test.ts`
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Produces: `reconnectDelay(attempt: number): number` and `createReconnectController(connect, schedule?, cancel?)`.
- Consumes: a `connect(): void` callback; timer functions matching `setTimeout` and `clearTimeout`.

- [ ] **Step 1: Write failing reconnect tests**

Create `frontend/src/runtime/reconnect.test.ts`:

```ts
import { describe, expect, it, vi } from 'vitest'
import { createReconnectController, reconnectDelay } from './reconnect'

describe('reconnect policy', () => {
  it('uses bounded exponential delays', () => {
    expect([0, 1, 2, 3, 4, 5, 8].map(reconnectDelay)).toEqual([
      500, 1000, 2000, 4000, 8000, 10000, 10000,
    ])
  })

  it('allows one timer, resets after open, and stops after disposal', () => {
    const connect = vi.fn()
    const callbacks: Array<() => void> = []
    const delays: number[] = []
    const schedule = vi.fn((callback: () => void, delay: number) => {
      callbacks.push(callback)
      delays.push(delay)
      return callbacks.length
    })
    const cancel = vi.fn()
    const controller = createReconnectController(connect, schedule, cancel)

    controller.closed()
    controller.closed()
    expect(delays).toEqual([500])
    callbacks.shift()?.()
    expect(connect).toHaveBeenCalledTimes(1)

    controller.closed()
    expect(delays).toEqual([500, 1000])
    controller.opened()
    callbacks.shift()?.()
    controller.closed()
    expect(delays).toEqual([500, 1000, 500])

    controller.dispose()
    controller.closed()
    expect(cancel).toHaveBeenCalledTimes(1)
    expect(delays).toEqual([500, 1000, 500])
  })
})
```

- [ ] **Step 2: Verify the reconnect tests fail**

Run:

```powershell
npm --prefix frontend test -- --run src/runtime/reconnect.test.ts
```

Expected: FAIL because `./reconnect` does not exist.

- [ ] **Step 3: Implement the reconnect controller**

Create `frontend/src/runtime/reconnect.ts`:

```ts
type TimerId = ReturnType<typeof setTimeout>
type Schedule = (callback: () => void, delay: number) => TimerId
type Cancel = (timer: TimerId) => void

export function reconnectDelay(attempt: number): number {
  return Math.min(500 * (2 ** Math.max(0, attempt)), 10_000)
}

export function createReconnectController(
  connect: () => void,
  schedule: Schedule = setTimeout,
  cancel: Cancel = clearTimeout,
) {
  let attempt = 0
  let timer: TimerId | null = null
  let disposed = false

  return {
    opened() {
      attempt = 0
    },
    closed() {
      if (disposed || timer !== null) return
      const delay = reconnectDelay(attempt++)
      timer = schedule(() => {
        timer = null
        if (!disposed) connect()
      }, delay)
    },
    dispose() {
      disposed = true
      if (timer !== null) cancel(timer)
      timer = null
    },
  }
}
```

- [ ] **Step 4: Integrate the controller into `App.tsx`**

Import `createReconnectController`, create it before the first `connect()`, call `opened()` from `ws.onopen`, call `closed()` from `ws.onclose`, and call `dispose()` before closing the WebSocket in effect cleanup. Remove the direct `setTimeout(connect, 2500)` and `clearTimeout(reconnectTimer)` code.

- [ ] **Step 5: Run focused and complete frontend checks**

```powershell
npm --prefix frontend test -- --run
npm --prefix frontend run lint
npm --prefix frontend run typecheck
```

Expected: all frontend tests, lint, and type checking pass.

- [ ] **Step 6: Commit reconnect reliability**

```powershell
git add frontend/src/runtime/reconnect.ts frontend/src/runtime/reconnect.test.ts frontend/src/App.tsx
git commit -m "fix: bound websocket reconnect retries"
```

### Task 3: Session cleanup, isolation, and concurrency

**Files:**
- Modify: `tests/test_app_server.py`

**Interfaces:**
- Consumes: `create_asgi_app(App)` and FastAPI `TestClient.websocket_connect`.
- Produces: deterministic regression coverage for cleanup, effect disposal, repeated connections, and session isolation.

- [ ] **Step 1: Add disconnect cleanup tests**

Append tests that create an app with a `use_effect` cleanup callback, connect and receive a full tree, then assert after the context exits:

```python
def test_websocket_disconnect_cleans_session_and_effects():
    app = App()
    cleaned = {"count": 0}

    @app.page("/")
    def home():
        db.use_effect(lambda: lambda: cleaned.__setitem__("count", cleaned["count"] + 1), [])
        return db.Text("ready")

    client = TestClient(create_asgi_app(app))
    with client.websocket_connect("/events") as websocket:
        assert websocket.receive_json()["type"] == "full"
        assert len(app._sessions) == 1

    assert app._sessions == {}
    assert app._session_paths == {}
    assert cleaned["count"] == 1
```

Add a 20-cycle test that connects, receives the full tree, disconnects, and asserts both registries are empty after every cycle.

- [ ] **Step 2: Add independent concurrent-session tests**

Create one counter app, open two nested WebSocket contexts, capture each `Button` event ID, update only the first session, and assert the first patch contains count `1`. Then update the second session and assert its first patch also contains count `1`, proving it did not inherit the first session's state.

Add a `ThreadPoolExecutor(max_workers=8)` test where each worker creates a `TestClient`, connects, receives one full tree, and returns its rendered session marker. Assert eight successful results and empty registries after all workers finish.

- [ ] **Step 3: Run the new tests and inspect any failure as a runtime defect**

```powershell
python -m pytest -q -p no:cacheprovider tests/test_app_server.py -k "disconnect or session or concurrent"
```

Expected: all focused lifecycle tests pass with the current cleanup implementation. If a test fails, follow systematic debugging before modifying production server code.

- [ ] **Step 4: Run the complete Python suite**

```powershell
python -m pytest -q -p no:cacheprovider
```

- [ ] **Step 5: Commit session reliability coverage**

```powershell
git add tests/test_app_server.py
git commit -m "test: cover websocket session resilience"
```

### Task 4: Bounded runtime resilience command

**Files:**
- Create: `scripts/runtime_resilience.py`
- Create: `tests/test_runtime_resilience.py`
- Modify: `DEVELOPMENT.md`

**Interfaces:**
- Produces: `percentile(values: list[float], percentile_value: float) -> float`, `find_event_id(tree: dict, label: str) -> str`, `ResilienceResult`, and CLI flags `--sessions`, `--cycles`, `--port`, `--deadline`, `--max-p95-ms`.
- Consumes: `examples/counter/app.py`, the `/events` WebSocket protocol, and `DATABRICKS_APP_PORT`.

- [ ] **Step 1: Write failing helper tests**

Create `tests/test_runtime_resilience.py`:

```python
import pytest
from scripts.runtime_resilience import find_event_id, percentile


def test_percentile_uses_nearest_rank():
    assert percentile([10.0, 20.0, 30.0, 40.0], 95) == 40.0
    assert percentile([30.0, 10.0, 20.0], 50) == 20.0


def test_find_event_id_locates_named_button():
    tree = {
        "type": "Column",
        "props": {},
        "children": [{"type": "Button", "props": {"label": "+", "click": "event-1"}, "children": []}],
    }
    assert find_event_id(tree, "+") == "event-1"


def test_find_event_id_rejects_missing_button():
    with pytest.raises(ValueError, match="button"):
        find_event_id({"type": "Text", "props": {}, "children": []}, "+")
```

- [ ] **Step 2: Verify helper tests fail**

```powershell
python -m pytest -q -p no:cacheprovider tests/test_runtime_resilience.py
```

Expected: FAIL because `scripts.runtime_resilience` does not exist.

- [ ] **Step 3: Implement the command**

Create an asyncio command with:

```python
@dataclass(frozen=True)
class ResilienceResult:
    sessions: int
    cycles: int
    successful_events: int
    reconnects: int
    failures: tuple[str, ...]
    median_ms: float
    p95_ms: float
    duration_ms: float
```

Use `subprocess.Popen([sys.executable, str(counter_app)])`, set `DATABRICKS_APP_PORT`, poll the root HTTP URL until ready, then run `sessions` asyncio tasks. Each task connects for every cycle, receives a `full` tree, finds the `+` button event, sends one event, waits for `patch` and `event_complete` under a per-event timeout, records latency, and disconnects. Wrap the entire async run in `asyncio.timeout(deadline)` and terminate the server in `finally` using the same bounded terminate/kill pattern as `scripts/smoke_examples.py`.

Print one JSON object made from `asdict(result)`. Return exit code `1` when failures are nonempty or `p95_ms > max_p95_ms`; otherwise return `0`.

- [ ] **Step 4: Verify helpers and a small real run**

```powershell
python -m pytest -q -p no:cacheprovider tests/test_runtime_resilience.py
python scripts/runtime_resilience.py --sessions 3 --cycles 1 --deadline 20 --max-p95-ms 1000
```

Expected: helper tests pass; real command reports three successful events, zero failures, and exits zero.

- [ ] **Step 5: Document local usage**

Add default and small-profile commands to `DEVELOPMENT.md`, including the 20-session/3-cycle defaults and the fact that the command is bounded local evidence, not a multi-process capacity claim.

- [ ] **Step 6: Commit runtime resilience**

```powershell
git add scripts/runtime_resilience.py tests/test_runtime_resilience.py DEVELOPMENT.md
git commit -m "test: add bounded runtime resilience check"
```

### Task 5: Frontend bundle budgets

**Files:**
- Create: `frontend/scripts/check-bundle-budget.mjs`
- Create: `frontend/scripts/check-bundle-budget.test.mjs`
- Modify: `frontend/package.json`
- Modify: `.github/workflows/ci.yml`
- Modify: `.github/workflows/publish.yml`

**Interfaces:**
- Produces: `npm run check:bundle` and exported `checkBudgets(distDir, budgets)`.
- Consumes: hashed Vite chunks under `brickflowui/frontend/dist/assets`.

- [ ] **Step 1: Write a failing bundle-checker test**

Create `frontend/scripts/check-bundle-budget.test.mjs` with Node's built-in test runner. The test creates a temporary directory containing `index-test.js` at 11 bytes and calls `checkBudgets(dir, {'index-': 10})`. Assert `result.ok === false`, the row's `actual === 11`, and `allowed === 10`. Add a second case with no matching file and assert the row reports `reason === 'missing'`. Remove the temporary directory in `finally`.

Run:

```powershell
node --test frontend/scripts/check-bundle-budget.test.mjs
```

Expected: FAIL because `check-bundle-budget.mjs` does not exist.

- [ ] **Step 2: Implement the bundle checker**

Implement exported budgets:

```js
export const DEFAULT_BUDGETS = {
  'index-': 850_000,
  'charts-': 1_100_000,
  'plotly.min-': 7_500_000,
  'vendor-': 250_000,
}
```

`checkBudgets` must ignore `.map` files, require exactly one `.js` file for each prefix, and return `{ok, rows}` where every row contains `prefix`, `file`, `actual`, `allowed`, `ok`, and an optional `reason` of `missing`, `duplicate`, or `oversized`. The CLI prints every row and exits nonzero when any row is missing, duplicated, or oversized.

- [ ] **Step 3: Add package and workflow commands**

Add to `frontend/package.json`:

```json
"check:bundle": "node scripts/check-bundle-budget.mjs"
```

Add:

```json
"test:bundle": "node --test scripts/check-bundle-budget.test.mjs"
```

Run `npm run check:bundle` immediately after `npm run build` in CI and publish validation.

- [ ] **Step 4: Run failure-path and real-bundle checks**

```powershell
npm --prefix frontend run test:bundle
npm --prefix frontend run build
npm --prefix frontend run check:bundle
```

Expected: self-test proves an oversized asset is rejected; the real current bundle passes all four budgets.

- [ ] **Step 5: Commit bundle budgets**

```powershell
git add frontend/scripts/check-bundle-budget.mjs frontend/scripts/check-bundle-budget.test.mjs frontend/package.json .github/workflows/ci.yml .github/workflows/publish.yml
git commit -m "ci: enforce frontend bundle budgets"
```

### Task 6: Playwright and Axe browser release gate

**Files:**
- Create: `frontend/playwright.config.ts`
- Create: `frontend/e2e/framework.spec.ts`
- Create: `.github/workflows/browser-qa.yml`
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`

**Interfaces:**
- Produces: `npm run test:e2e` against counter on port `8065` and component studio on port `8066`.
- Consumes: `@playwright/test`, `@axe-core/playwright`, and built packaged frontend assets.

- [ ] **Step 1: Install browser test dependencies**

```powershell
npm --prefix frontend install --save-dev @playwright/test @axe-core/playwright
```

Add:

```json
"test:e2e": "playwright test"
```

- [ ] **Step 2: Configure two bounded local servers**

Create `frontend/playwright.config.ts` with Chromium only, `trace: 'retain-on-failure'`, `screenshot: 'only-on-failure'`, a 30-second test timeout, and two `webServer` entries:

```ts
webServer: [
  {
    command: 'python ../examples/counter/app.py',
    port: 8065,
    env: { DATABRICKS_APP_PORT: '8065' },
    timeout: 30_000,
    reuseExistingServer: !process.env.CI,
  },
  {
    command: 'python ../examples/component_studio/app.py',
    port: 8066,
    env: { DATABRICKS_APP_PORT: '8066' },
    timeout: 30_000,
    reuseExistingServer: !process.env.CI,
  },
]
```

- [ ] **Step 3: Write browser and accessibility tests**

In `frontend/e2e/framework.spec.ts`, attach console/pageerror/requestfailed collectors before navigation. For counter:

1. navigate to port 8065;
2. expect heading `Counter` and button `+`;
3. click `+` and expect visible count `1`;
4. run `new AxeBuilder({ page }).analyze()` and assert no violations with impact `serious` or `critical`;
5. set viewport `390x844` and assert `document.documentElement.scrollWidth <= 390`;
6. press Tab until a button is focused, with a maximum of six presses;
7. assert captured error arrays are empty.

For component studio, navigate to port 8066 and assert `BrickflowUI Component Studio`, `Component inventory`, `Search components`, and the `Overview`, `Visuals`, `Media`, and `Workflow` tabs. Click `Open detail drawer`, assert the `Why this example matters` dialog, and close it. Click `Visuals`, assert `Runs vs success rate`, `Latency trend`, and `Pipeline map`. Run the same Axe severity check on the overview and visuals states, then assert no console/page/request errors.

- [ ] **Step 4: Add the release workflow**

Create `.github/workflows/browser-qa.yml` triggered by push to `main`, weekly cron, and `workflow_dispatch`. Install Python 3.11, Node 22, `.[dev]`, `npm ci`, run the frontend build and bundle check, install Chromium with `npx playwright install --with-deps chromium`, run `npm run test:e2e`, then run:

```text
python scripts/runtime_resilience.py --sessions 10 --cycles 2 --deadline 30 --max-p95-ms 1000
```

Upload `frontend/playwright-report` and `frontend/test-results` with `actions/upload-artifact@v4` on failure.

- [ ] **Step 5: Run browser checks locally**

```powershell
npm --prefix frontend exec playwright install chromium
npm --prefix frontend run test:e2e
```

Expected: both examples load, interactions pass, no serious/critical Axe violations, no overflow, and no browser errors.

- [ ] **Step 6: Commit browser QA**

```powershell
git add frontend/playwright.config.ts frontend/e2e/framework.spec.ts frontend/package.json frontend/package-lock.json .github/workflows/browser-qa.yml
git commit -m "test: add browser accessibility release gate"
```

### Task 7: Databricks workspace evidence harness

**Files:**
- Create: `scripts/validate_databricks_workspace.py`
- Create: `tests/test_databricks_workspace_validation.py`
- Create: `docs/DATABRICKS_RELEASE_VALIDATION.md`

**Interfaces:**
- Produces: `redact_origin(url: str) -> str`, `validate_results(results: list[dict]) -> list[str]`, and a read-only CLI accepting `--app-url`, `--profile-a`, `--profile-b`, `--catalog`, `--warehouse-id`, `--job-id`, and `--output`.
- Consumes: optional `databricks.sdk.WorkspaceClient` profiles and an authenticated app root request.

- [ ] **Step 1: Write failing redaction and evidence tests**

Create tests that assert:

```python
def test_redact_origin_drops_credentials_path_and_query():
    assert redact_origin("https://token@example.cloud/path?q=secret") == "https://example.cloud"


def test_validate_results_rejects_same_subject_and_missing_permission_difference():
    results = [
        {"profile": "a", "subject": "same", "catalog": True, "warehouse": True, "job": True},
        {"profile": "b", "subject": "same", "catalog": True, "warehouse": True, "job": True},
    ]
    errors = validate_results(results)
    assert any("different subjects" in item for item in errors)
    assert any("permission difference" in item for item in errors)
```

Add a subprocess test that runs the script without arguments and asserts a nonzero exit plus a prerequisite/configuration message without the word `passed`.

- [ ] **Step 2: Verify tests fail**

```powershell
python -m pytest -q -p no:cacheprovider tests/test_databricks_workspace_validation.py
```

Expected: FAIL because the validation module does not exist.

- [ ] **Step 3: Implement read-only evidence collection**

Parse arguments with `argparse`. Import `WorkspaceClient` inside `main` and convert missing optional dependencies into an actionable prerequisite error. Create one client per profile, call `current_user.me()`, `catalogs.get`, `warehouses.get`, and `jobs.get`, recording boolean access and sanitized exception type names. Use `urllib.request` for the app root only when a usable profile token is available; never include the token in output or errors.

Write JSON only after validation completes, create only the requested parent directory, and ensure the serialized structure contains no `token`, `authorization`, or credential values. Return nonzero for identical subjects, no permission difference, failed required resource checks, or incomplete configuration.

- [ ] **Step 4: Document the real workspace procedure**

Write `docs/DATABRICKS_RELEASE_VALIDATION.md` with profile setup, the exact read-only command, expected redacted JSON fields, manual SQL/job checks that require explicit operator action, two-user permission expectations, and cleanup. State that the harness does not deploy or mutate resources.

- [ ] **Step 5: Run focused tests and safe missing-prerequisite behavior**

```powershell
python -m pytest -q -p no:cacheprovider tests/test_databricks_workspace_validation.py
python scripts/validate_databricks_workspace.py
```

Expected: tests pass; direct invocation exits nonzero with a concise configuration message and no traceback or secret.

- [ ] **Step 6: Commit the Databricks harness**

```powershell
git add scripts/validate_databricks_workspace.py tests/test_databricks_workspace_validation.py docs/DATABRICKS_RELEASE_VALIDATION.md
git commit -m "test: add Databricks release evidence harness"
```

### Task 8: Documentation, full verification, and report update

**Files:**
- Modify: `docs/STABILITY.md`
- Modify: `DEVELOPMENT.md`
- Modify: `docs/verification/2026-07-31-end-user-framework-qa.md`

**Interfaces:**
- Consumes: every command and result from Tasks 1–7.
- Produces: a truthful release-hardening record that separates local/CI proof from workspace-only evidence.

- [ ] **Step 1: Update stability and development commands**

Document:

```text
npm --prefix frontend run check:bundle
npm --prefix frontend run test:e2e
python scripts/runtime_resilience.py
python scripts/validate_databricks_workspace.py --help
```

State which commands are fast PR gates and which are release/workspace gates.

- [ ] **Step 2: Run the complete local gate set**

```powershell
python -m pytest -q -p no:cacheprovider
python scripts/generate_component_reference.py
git diff --exit-code -- docs/components/reference
python -m mkdocs build --strict -d .tmp/release-hardening/site
python scripts/smoke_examples.py
npm --prefix frontend test -- --run
npm --prefix frontend run lint
npm --prefix frontend run typecheck
npm --prefix frontend audit --audit-level=high
npm --prefix frontend run build
npm --prefix frontend run check:bundle
npm --prefix frontend run test:e2e
python scripts/runtime_resilience.py --sessions 10 --cycles 2 --deadline 30 --max-p95-ms 1000
python -m build --outdir .tmp/release-hardening/dist
python -m twine check .tmp/release-hardening/dist/*
git diff --check
```

Expected: every locally available gate exits zero. The Databricks harness is verified through tests and its safe nonzero prerequisite path, not counted as a workspace pass.

- [ ] **Step 3: Update the verification report**

Add exact test counts, browser/Axe results, resilience statistics, bundle sizes, CI matrix configuration, and the remaining need for real Databricks profiles/resources. Remove only limitations that the new evidence actually closes.

- [ ] **Step 4: Inspect the final change set**

```powershell
git status --short
git diff --stat
git diff --check
```

Confirm the pre-existing VDOM and earlier CLI changes remain intact and are not accidentally bundled into unrelated commits.

- [ ] **Step 5: Commit documentation and verification evidence**

```powershell
git add docs/STABILITY.md DEVELOPMENT.md docs/verification/2026-07-31-end-user-framework-qa.md docs/superpowers/plans/2026-08-01-release-hardening.md
git commit -m "docs: record release hardening gates"
```
