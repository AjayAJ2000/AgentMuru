# BrickflowUI Stability Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate every confirmed core-runtime defect in the approved stability specification and establish automated backend, frontend, browser, packaging, and documentation release gates.

**Architecture:** Extract navigation, patching, and CSV protocol logic from React components into pure TypeScript modules, then keep `App.tsx` and `Renderer.tsx` responsible only for orchestration and rendering. Harden Python output boundaries and render-context restoration with small helpers, and replace the deceptive fallback runtime with an explicit 503 diagnostic. Each behavior is introduced through a failing regression test before the smallest production change.

**Tech Stack:** Python 3.10+, FastAPI/Starlette, pytest, React 18, TypeScript, Vite, Vitest, ESLint, GitHub Actions, Playwright/browser smoke testing.

---

## File structure

- Create `frontend/src/runtime/applyPatch.ts`: immutable VDOM patching plus typed protocol errors.
- Create `frontend/src/runtime/applyPatch.test.ts`: patch operation and invalid-path coverage.
- Create `frontend/src/runtime/navigation.ts`: path normalization and navigation-message creation.
- Create `frontend/src/runtime/navigation.test.ts`: user navigation versus popstate behavior.
- Create `frontend/src/runtime/csv.ts`: RFC-style quoting and spreadsheet-safe CSV output.
- Create `frontend/src/runtime/csv.test.ts`: quoting, Unicode, and formula neutralization coverage.
- Create `frontend/src/runtime/chat.ts`: IME-safe submit predicate.
- Create `frontend/src/runtime/chat.test.ts`: composition and Enter-key coverage.
- Modify `frontend/src/App.tsx`: consume patch/navigation helpers and reconnect after invalid patches.
- Modify `frontend/src/Renderer.tsx`: consume CSV/chat helpers.
- Modify `frontend/package.json`, `frontend/package-lock.json`, `frontend/vite.config.ts`: add Vitest and a deterministic test command.
- Modify `brickflowui/state.py`: reset a render context using its `ContextVar` token.
- Modify `brickflowui/server.py`: restore context tokens and emit escaped real-shell or explicit missing-bundle responses.
- Modify `brickflowui/cli/main.py`: validate scaffold names before writing.
- Modify `tests/test_state.py`, `tests/test_app_server.py`, `tests/test_cli.py`: backend regressions.
- Modify `.github/workflows/ci.yml`: run frontend tests.
- Modify `docs/ROADMAP.md`: describe `0.1.13` as current and move future work forward.
- Create `docs/STABILITY.md`: supported guarantees, verification commands, and known limitations.
- Create `docs/verification/2026-06-28-stability-report.md`: exact final evidence.

### Task 1: Frontend test harness

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`
- Modify: `frontend/vite.config.ts`
- Create: `frontend/src/runtime/smoke.test.ts`

- [ ] **Step 1: Add the failing test-runner smoke test**

```ts
import { describe, expect, it } from 'vitest'

describe('frontend test harness', () => {
  it('executes TypeScript tests', () => expect(1 + 1).toBe(2))
})
```

- [ ] **Step 2: Run the missing test command**

Run: `npm test -- --run`

Expected: FAIL because `package.json` has no `test` script and Vitest is not installed.

- [ ] **Step 3: Install and configure Vitest**

Run: `npm install --save-dev vitest@^3.2.4`

Add to `frontend/package.json`:

```json
"test": "vitest"
```

Add to `frontend/vite.config.ts` inside `defineConfig`:

```ts
test: {
  environment: 'node',
  include: ['src/**/*.test.ts'],
},
```

- [ ] **Step 4: Verify the harness**

Run: `npm test -- --run`

Expected: PASS with one test.

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/vite.config.ts frontend/src/runtime/smoke.test.ts
git commit -m "test: add frontend vitest harness"
```

### Task 2: Render-context token restoration

**Files:**
- Modify: `tests/test_state.py`
- Modify: `brickflowui/state.py`
- Modify: `brickflowui/server.py`

- [ ] **Step 1: Write the failing nested-context test**

```python
def test_reset_render_context_restores_previous_context():
    outer = RenderContext(session_id="outer")
    inner = RenderContext(session_id="inner")
    outer_token = set_render_context(outer)
    try:
        inner_token = set_render_context(inner)
        reset_render_context(inner_token)
        assert get_context() is outer
    finally:
        reset_render_context(outer_token)
```

- [ ] **Step 2: Verify the missing API fails**

Run: `python -m pytest tests/test_state.py::test_reset_render_context_restores_previous_context -q`

Expected: FAIL because `reset_render_context` is not defined.

- [ ] **Step 3: Implement token restoration**

Add to `brickflowui/state.py`:

```python
def reset_render_context(token: Any) -> None:
    _current_context.reset(token)
```

Update both render `finally` blocks in `brickflowui/server.py`:

```python
reset_render_context(render_token)
```

- [ ] **Step 4: Verify state and server tests**

Run: `python -m pytest tests/test_state.py tests/test_app_server.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add brickflowui/state.py brickflowui/server.py tests/test_state.py
git commit -m "fix: restore nested render contexts"
```

### Task 3: Safe HTML shell and explicit missing-bundle failure

**Files:**
- Modify: `tests/test_app_server.py`
- Modify: `brickflowui/server.py`

- [ ] **Step 1: Write failing shell-boundary tests**

```python
def test_shell_escapes_title_and_favicon_html():
    app = App(title='</title><img src=x>', favicon='" onload="alert(1)')
    app.mount(lambda: VNode(type="div"))
    response = TestClient(create_asgi_app(app)).get("/")
    assert "</title><img" not in response.text
    assert 'onload="alert(1)' not in response.text


def test_missing_frontend_bundle_returns_diagnostic(monkeypatch):
    monkeypatch.setattr(server, "_FRONTEND_DIST", Path("missing-frontend-dist"))
    app = App()
    app.mount(lambda: VNode(type="div"))
    response = TestClient(create_asgi_app(app)).get("/")
    assert response.status_code == 503
    assert "frontend bundle is missing" in response.text.lower()
    assert "new WebSocket" not in response.text
```

- [ ] **Step 2: Confirm both tests fail for the intended reasons**

Run: `python -m pytest tests/test_app_server.py -k "escapes_title or missing_frontend_bundle" -q`

Expected: FAIL because the real-shell title is unescaped and fallback returns 200 with a WebSocket runtime.

- [ ] **Step 3: Implement output-boundary helpers**

Add helpers in `brickflowui/server.py`:

```python
def _safe_json_data(value: object) -> str:
    return json.dumps(value).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def _safe_style_text(value: str) -> str:
    return re.sub(r"</(?=style)", r"<\\/", value, flags=re.IGNORECASE)
```

Escape title and favicon with `html.escape(..., quote=True)`. Replace executable bootstrap assignment with a safe JSON data block:

```html
<script id="brickflow-bootstrap" type="application/json">SAFE_JSON</script>
```

Update `App.tsx` in Task 5 to read this element. Return the diagnostic shell with status code 503 when `index.html` is missing.

- [ ] **Step 4: Verify the complete server test module**

Run: `python -m pytest tests/test_app_server.py -q`

Expected: PASS after updating obsolete fallback assertions to the diagnostic contract.

- [ ] **Step 5: Commit**

```bash
git add brickflowui/server.py tests/test_app_server.py
git commit -m "fix: harden shell output and missing bundle handling"
```

### Task 4: Safe CLI scaffold targets

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `brickflowui/cli/main.py`

- [ ] **Step 1: Write failing path-validation tests**

```python
@pytest.mark.parametrize("name", ["../escape", "child/name", r"child\\name", ".", "CON"])
def test_new_command_rejects_unsafe_project_names(monkeypatch, tmp_path, name):
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)
    result = runner.invoke(app, ["new", name])
    assert result.exit_code == 2
    assert "single safe directory name" in result.output
    assert list(tmp_path.iterdir()) == []
```

- [ ] **Step 2: Confirm traversal is currently accepted**

Run: `python -m pytest tests/test_cli.py::test_new_command_rejects_unsafe_project_names -q`

Expected: FAIL because traversal/path-separator names are not validated.

- [ ] **Step 3: Implement validation before mutation**

Add `_validated_project_name(name: str) -> str` that rejects empty/dot names, `Path(name).is_absolute()`, `/`, `\\`, `Path(name).name != name`, and case-insensitive Windows device names `CON`, `PRN`, `AUX`, `NUL`, `COM1`-`COM9`, `LPT1`-`LPT9`. Resolve `Path.cwd() / name` and require its parent to equal `Path.cwd().resolve()`.

On validation failure, print `[ERROR] Project name must be a single safe directory name.` and raise `typer.Exit(2)`.

- [ ] **Step 4: Verify all CLI behavior**

Run: `python -m pytest tests/test_cli.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add brickflowui/cli/main.py tests/test_cli.py
git commit -m "fix: constrain CLI scaffold targets"
```

### Task 5: Robust patching and correct navigation history

**Files:**
- Create: `frontend/src/runtime/applyPatch.ts`
- Create: `frontend/src/runtime/applyPatch.test.ts`
- Create: `frontend/src/runtime/navigation.ts`
- Create: `frontend/src/runtime/navigation.test.ts`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Write failing patch tests**

```ts
it('rejects a nested patch whose parent path does not exist', () => {
  expect(() => applyPatch(root, { op: 'replace', path: [4, 0], node: leaf('x') }))
    .toThrow(PatchApplicationError)
})

it('applies replace, update_props, insert, and remove immutably', () => {
  const updated = applyPatches(root, [
    { op: 'update_props', path: [], props: { title: 'new' } },
    { op: 'insert', path: [1], node: leaf('second') },
    { op: 'replace', path: [0], node: leaf('first-updated') },
  ])
  expect(updated.props.title).toBe('new')
  expect(updated.children.map(child => child.props.value)).toEqual(['first-updated', 'second'])
  expect(root.props.title).toBe('old')
})
```

- [ ] **Step 2: Write failing navigation tests**

```ts
it('pushes history only for user navigation', () => {
  expect(navigationAction('/reports', 'user')).toEqual({
    message: { type: 'navigate', path: '/reports' },
    history: 'push',
  })
  expect(navigationAction('/home', 'popstate').history).toBe('none')
})
```

- [ ] **Step 3: Verify modules are missing**

Run: `npm test -- --run src/runtime/applyPatch.test.ts src/runtime/navigation.test.ts`

Expected: FAIL because the modules do not exist.

- [ ] **Step 4: Implement pure runtime modules**

`applyPatch.ts` must validate every index with `Number.isInteger(index) && index >= 0`, require an existing parent for nested operations, require nodes for insert/replace, and throw `PatchApplicationError` on malformed operations. `applyPatches` reduces patches without mutating the source tree.

`navigation.ts` exports:

```ts
export type NavigationSource = 'user' | 'popstate'
export function navigationAction(path: string, source: NavigationSource) {
  return {
    message: { type: 'navigate' as const, path },
    history: source === 'user' ? 'push' as const : 'none' as const,
  }
}
```

- [ ] **Step 5: Integrate helpers into `App.tsx`**

User navigation sends then pushes history. `popstate` sends without history mutation. Patch protocol errors set a visible runtime error and close the WebSocket so reconnect obtains a full tree. Read bootstrap configuration from `#brickflow-bootstrap` JSON text, retaining the old global only as a compatibility fallback for prebuilt assets during development.

- [ ] **Step 6: Verify unit tests, lint, and build**

Run: `npm test -- --run`

Run: `npm run lint`

Run: `npm run build`

Expected: all PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/runtime/applyPatch.ts frontend/src/runtime/applyPatch.test.ts frontend/src/runtime/navigation.ts frontend/src/runtime/navigation.test.ts frontend/src/App.tsx
git commit -m "fix: harden patches and browser navigation"
```

### Task 6: Spreadsheet-safe CSV and IME-safe chat

**Files:**
- Create: `frontend/src/runtime/csv.ts`
- Create: `frontend/src/runtime/csv.test.ts`
- Create: `frontend/src/runtime/chat.ts`
- Create: `frontend/src/runtime/chat.test.ts`
- Modify: `frontend/src/Renderer.tsx`

- [ ] **Step 1: Write failing CSV tests**

```ts
it.each(['=1+1', '+cmd', '-2+3', '@SUM(A1)', '\t=1', '\r=1'])(
  'neutralizes spreadsheet formula %s',
  value => expect(serializeCsv([{ label: 'Value', key: 'value' }], [{ value }]))
    .toContain(`"'${value.replaceAll('"', '""')}"`),
)

it('quotes headers, quotes, commas, and Unicode with CRLF and BOM', () => {
  expect(serializeCsv([{ label: 'Display, name', key: 'name' }], [{ name: 'A "quoted" ✓' }]))
    .toBe('\uFEFF"Display, name"\r\n"A ""quoted"" ✓"')
})
```

- [ ] **Step 2: Write failing chat predicate tests**

```ts
expect(shouldSubmitChatInput('Enter', false)).toBe(true)
expect(shouldSubmitChatInput('Enter', true)).toBe(false)
expect(shouldSubmitChatInput('a', false)).toBe(false)
```

- [ ] **Step 3: Verify both helpers are missing**

Run: `npm test -- --run src/runtime/csv.test.ts src/runtime/chat.test.ts`

Expected: FAIL because the modules do not exist.

- [ ] **Step 4: Implement and integrate helpers**

`serializeCsv` quotes every field, doubles quotes, prefixes dangerous cells with `'`, joins rows with `\r\n`, and prepends `\uFEFF`. `shouldSubmitChatInput` returns `key === 'Enter' && !isComposing`.

`Renderer.tsx` uses `serializeCsv` for export and checks `event.nativeEvent.isComposing`; on a true submit it calls `event.preventDefault()` before `submit()`.

- [ ] **Step 5: Verify frontend gates**

Run: `npm test -- --run`

Run: `npm run lint`

Run: `npm run build`

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/runtime/csv.ts frontend/src/runtime/csv.test.ts frontend/src/runtime/chat.ts frontend/src/runtime/chat.test.ts frontend/src/Renderer.tsx
git commit -m "fix: secure CSV export and IME submission"
```

### Task 7: CI and stability documentation

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `docs/ROADMAP.md`
- Create: `docs/STABILITY.md`

- [ ] **Step 1: Add the frontend test release gate**

Insert after `npm ci` in `.github/workflows/ci.yml`:

```yaml
- name: Run frontend tests
  working-directory: frontend
  run: npm test -- --run

- name: Run frontend lint
  working-directory: frontend
  run: npm run lint
```

- [ ] **Step 2: Correct roadmap release state**

Replace the stale `0.1.10`-`0.1.12` “recommended focus” sequence with a `0.1.13` current-baseline section listing shipped security/runtime/repository gates, then retain `0.2.0` as the next compatibility milestone.

- [ ] **Step 3: Document the stability contract**

`docs/STABILITY.md` must state supported Python versions, supported production frontend requirement, the missing-bundle 503 behavior, exact local verification commands, browser scenarios, Databricks components still awaiting the follow-up integration specification, and the difference between zero known reproducible defects and a claim of formal certification.

- [ ] **Step 4: Run documentation drift and strict build checks**

Run: `python scripts/generate_component_reference.py`

Run: `git diff --exit-code -- docs/components/reference`

Run: `python -m mkdocs build --strict`

Expected: generated references unchanged and strict docs build PASS.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/ci.yml docs/ROADMAP.md docs/STABILITY.md
git commit -m "docs: establish stability release gates"
```

### Task 8: Full packaging and browser verification

**Files:**
- Create: `docs/verification/2026-06-28-stability-report.md`
- Modify only if a failing gate reveals a reproducible defect, using a new failing test before each fix.

- [ ] **Step 1: Run all local automated gates**

Run from repository root:

```text
python -m pytest -q
python -m mkdocs build --strict
python -m build
```

Run from `frontend`:

```text
npm test -- --run
npm run lint
npm run build
```

Expected: every command exits 0 with no test failures or lint errors.

- [ ] **Step 2: Inspect built distributions**

Run: `python -m zipfile -l dist/brickflowui-0.1.13-py3-none-any.whl`

Expected: wheel includes `brickflowui/frontend/dist/index.html` and hashed assets.

- [ ] **Step 3: Run dependency audits**

Run: `python -m pip_audit`

Run from `frontend`: `npm audit --audit-level=high`

Expected: no unresolved high/critical vulnerability in a shipped runtime dependency. Record any tooling-only finding with package, path, and mitigation.

- [ ] **Step 4: Start a representative multi-page app**

Run: `python examples/acme_analytics_command_center/app.py`

Expected: server reaches its listening state without traceback.

- [ ] **Step 5: Execute browser matrix**

Verify initial load, WebSocket connection, state patch, direct deep link, user navigation, repeated Back/Forward, forced reconnect, table sort/pagination/export, chat composition/submit, theme switching, desktop viewport, and narrow viewport. Capture console errors and screenshots for any failure.

- [ ] **Step 6: Verify missing-bundle diagnostic separately**

Use the backend regression test and a temporary monkeypatched server path; do not delete or rename the real bundled assets. Confirm HTTP 503, remedy copy, and absence of WebSocket initialization.

- [ ] **Step 7: Write the evidence report**

Record commit, environment, exact command outputs, test counts, package contents, browser results, dependency-audit results, and residual limitations in `docs/verification/2026-06-28-stability-report.md`.

- [ ] **Step 8: Run final clean verification**

Run: `git diff --check`

Run: `python -m pytest -q`

Run from `frontend`: `npm test -- --run && npm run lint && npm run build`

Expected: clean whitespace check and all gates PASS.

- [ ] **Step 9: Commit verification evidence**

```bash
git add docs/verification/2026-06-28-stability-report.md
git commit -m "test: record stability verification evidence"
```

## Follow-up plans required before the broader product claim

After this plan passes, write separate designs and plans for:

1. functional Databricks component integration for `CatalogBrowser`, `WarehouseSelector`, and `JobTrigger`;
2. production lifecycle and load validation, including configurable session policy, observability, concurrency, and an actual Databricks Apps deployment.

These are not folded into this plan because they require distinct data contracts, credentials, deployment environments, and acceptance tests.
