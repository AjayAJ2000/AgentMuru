# Databricks Identity and Components Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete BrickflowUI's identity-safe Databricks integration, component contracts, asset boundary, and public error boundary.

**Architecture:** Private request credentials flow through the existing principal context into an injectable SQL connection provider. User connections are operation-scoped; app connections are guarded and reusable. Databricks components remain server-driven and receive only serializable state.

**Tech Stack:** Python 3.10+, FastAPI, ContextVar, Databricks SDK/SQL connector, React 18, TypeScript, Vitest, pytest.

## Global Constraints

- Preserve `app`, `user`, and `hybrid` authentication modes.
- Never serialize, log, represent, or globally cache a forwarded user access token.
- Keep existing public constructor calls compatible.
- Do not touch the user's pre-existing `brickflowui/vdom.py` and `tests/test_vdom.py` changes.
- Use a failing regression test before each production behavior change.

---

### Task 1: Private credentials and identity-aware SQL lifecycle

**Files:**
- Modify: `brickflowui/auth.py`
- Replace internals: `brickflowui/databricks/sql.py`
- Modify: `tests/test_app_server.py`
- Modify: `tests/test_databricks_sql.py`

**Interfaces:**
- Produces: `Principal.access_token: Optional[str]` with `repr=False, compare=False`; `connection(identity=None)` context manager; injectable `set_connection_factory()` test seam.
- Consumes: `current_principal()` and `x-forwarded-access-token` request/websocket headers.

- [ ] **Step 1: Write failing token privacy and header extraction tests**

```python
principal = HeaderAuthProvider()._from_mapping({
    "x-brickflow-user-id": "alice",
    "x-forwarded-access-token": "secret",
})
assert principal.access_token == "secret"
assert "secret" not in repr(principal)
assert principal == dataclasses.replace(principal, access_token="different")
```

- [ ] **Step 2: Run the focused test and confirm RED**

Run: `python -m pytest tests/test_app_server.py -k forwarded_access_token -q -p no:cacheprovider`  
Expected: FAIL because `Principal` has no private access-token field.

- [ ] **Step 3: Add the private credential field and extract only the forwarded token**

```python
access_token: Optional[str] = field(default=None, repr=False, compare=False)
```

- [ ] **Step 4: Write failing SQL lifecycle tests**

```python
with connection(user_principal) as conn:
    assert conn is created_user_connection
assert created_user_connection.closed

with connection(app_principal) as first:
    pass
with connection(app_principal) as second:
    assert second is first
```

- [ ] **Step 5: Run and confirm RED**

Run: `python -m pytest tests/test_databricks_sql.py -q -p no:cacheprovider`  
Expected: FAIL because the provider API does not exist and the current connection is global.

- [ ] **Step 6: Implement the provider context manager**

```python
@contextmanager
def connection(identity: Optional[Principal] = None):
    principal = identity or current_principal()
    if principal.principal_type == "user":
        conn = _connect(access_token=principal.access_token)
        try:
            yield conn
        finally:
            conn.close()
        return
    with _app_connection_lock:
        yield _healthy_app_connection()
```

- [ ] **Step 7: Route query, execute, and transaction through the provider and run focused tests**

Run: `python -m pytest tests/test_databricks_sql.py tests/test_app_server.py -q -p no:cacheprovider`  
Expected: PASS.

- [ ] **Step 8: Commit the isolated identity lifecycle slice**

```powershell
git add brickflowui/auth.py brickflowui/databricks/sql.py tests/test_app_server.py tests/test_databricks_sql.py
git commit -m "fix: isolate Databricks SQL identities"
```

### Task 2: Typed Databricks services

**Files:**
- Create: `brickflowui/databricks/services.py`
- Modify: `brickflowui/databricks/__init__.py`
- Create: `tests/test_databricks_services.py`

**Interfaces:**
- Produces: `catalog_tree() -> list[dict]`, `list_warehouses() -> list[dict]`, `trigger_job(job_id: str, parameters: Optional[dict] = None) -> dict`.
- Consumes: injectable workspace client factory and current identity-aware SQL/provider context.

- [ ] **Step 1: Write failing normalization tests using small fake clients**

```python
assert list_warehouses(client=fake) == [
    {"id": "w1", "name": "Starter", "state": "RUNNING"}
]
assert trigger_job("42", client=fake) == {"job_id": "42", "run_id": "99", "status": "QUEUED"}
```

- [ ] **Step 2: Confirm RED**

Run: `python -m pytest tests/test_databricks_services.py -q -p no:cacheprovider`  
Expected: FAIL because the services module does not exist.

- [ ] **Step 3: Implement narrow adapters that return plain records**

```python
def list_warehouses(*, client=None) -> list[dict[str, Any]]:
    workspace = client or workspace_client()
    return [{"id": str(item.id), "name": item.name or str(item.id),
             "state": _enum_value(item.state)} for item in workspace.warehouses.list()]
```

- [ ] **Step 4: Verify service tests**

Run: `python -m pytest tests/test_databricks_services.py tests/test_databricks_uc.py -q -p no:cacheprovider`  
Expected: PASS.

- [ ] **Step 5: Commit the service adapters**

```powershell
git add brickflowui/databricks/services.py brickflowui/databricks/__init__.py tests/test_databricks_services.py
git commit -m "feat: add Databricks service adapters"
```

### Task 3: Complete Python and React component contracts

**Files:**
- Modify: `brickflowui/components.py`
- Modify: `frontend/src/Renderer.tsx`
- Create: `frontend/src/runtime/databricksComponents.test.tsx`
- Modify: `tests/test_components.py`
- Modify: `frontend/src/index.css`

**Interfaces:**
- Produces: complete `CatalogBrowser`, `WarehouseSelector`, and `JobTrigger` VNode props and renderer cases.
- Consumes: normalized records returned by Task 2 and the existing event dispatch protocol.

- [ ] **Step 1: Write failing Python serialization and parity tests**

```python
node = db.WarehouseSelector(warehouses=[{"id": "w1", "name": "Starter"}], loading=True)
assert node.props["warehouses"][0]["id"] == "w1"
assert python_types - renderer_types == set()
```

- [ ] **Step 2: Confirm Python RED**

Run: `python -m pytest tests/test_components.py -k 'databricks or frontend_maps' -q -p no:cacheprovider`  
Expected: FAIL because props and renderer mappings are missing.

- [ ] **Step 3: Write failing React tests for rendering, accessibility, state, and dispatch**

```tsx
render(<Renderer node={warehouseNode} ctx={ctx} />)
fireEvent.change(screen.getByLabelText('SQL Warehouse'), { target: { value: 'w1' } })
expect(dispatch).toHaveBeenCalledWith('handler-id', 'w1')
```

- [ ] **Step 4: Confirm frontend RED**

Run: `npm --prefix frontend test -- databricksComponents.test.tsx --run`  
Expected: FAIL because no Databricks renderer cases exist.

- [ ] **Step 5: Implement additive constructors and accessible renderer cases**

```python
props={"warehouses": warehouses or [], "selectedId": selected_id,
       "label": label, "loading": loading, "error": error,
       "emptyMessage": empty_message, "disabled": disabled}
```

- [ ] **Step 6: Verify Python and frontend GREEN**

Run: `python -m pytest tests/test_components.py -q -p no:cacheprovider`  
Run: `npm --prefix frontend test -- --run`  
Expected: all focused tests PASS.

- [ ] **Step 7: Commit the complete component contracts**

```powershell
git add brickflowui/components.py frontend/src/Renderer.tsx frontend/src/runtime/databricksComponents.test.tsx frontend/src/index.css tests/test_components.py
git commit -m "feat: complete Databricks components"
```

### Task 4: Asset containment and safe public errors

**Files:**
- Modify: `brickflowui/app.py`
- Modify: `brickflowui/server.py`
- Modify: `tests/test_app_server.py`

**Interfaces:**
- Produces: `asset_roots`, `asset_registry_limit`, containment-aware asset registry; `_public_error_message(correlation_id)`.
- Consumes: existing `resolve_asset_url`, asset route, and WebSocket error flow.

- [ ] **Step 1: Write failing containment, eviction, and revalidation tests**

```python
app = App(asset_roots=[safe_root], asset_registry_limit=2)
assert app.asset_url(outside_file) == outside_file
assert app.asset_url(first_file).startswith("/__brickflow_asset__/")
assert app.get_registered_asset(first_id) is None after registering three distinct files
```

- [ ] **Step 2: Confirm asset RED**

Run: `python -m pytest tests/test_app_server.py -k asset -q -p no:cacheprovider`  
Expected: FAIL because arbitrary existing files register and the registry is unbounded.

- [ ] **Step 3: Implement resolved-root containment and bounded LRU storage**

```python
if not any(path == root or root in path.parents for root in self.asset_roots):
    return None
self._asset_registry.move_to_end(digest)
while len(self._asset_registry) > self.asset_registry_limit:
    self._asset_registry.popitem(last=False)
```

- [ ] **Step 4: Write failing error-redaction test**

```python
assert "database-password" not in websocket_error["message"]
assert websocket_error["error_id"]
assert "database-password" in caplog.text
```

- [ ] **Step 5: Confirm error RED**

Run: `python -m pytest tests/test_app_server.py -k error_redaction -q -p no:cacheprovider`  
Expected: FAIL because exception text is currently returned to the browser.

- [ ] **Step 6: Implement correlated public errors and verify focused tests**

Run: `python -m pytest tests/test_app_server.py -q -p no:cacheprovider`  
Expected: PASS.

- [ ] **Step 7: Commit the asset and error boundaries**

```powershell
git add brickflowui/app.py brickflowui/server.py tests/test_app_server.py
git commit -m "fix: bound assets and redact runtime errors"
```

### Task 5: Documentation and complete verification

**Files:**
- Modify: `docs/STABILITY.md`
- Modify: `docs/components/catalog.md`
- Modify: `SKILL.md`
- Modify: `docs/verification/2026-07-14-agentic-stability-report.md`
- Rebuild: `brickflowui/frontend/dist/**`

**Interfaces:**
- Produces: accurate identity/component usage guidance and final evidence.
- Consumes: Tasks 1-4.

- [ ] **Step 1: Document both authorization modes and server-driven component usage**

```python
warehouses = db.databricks.list_warehouses()
return db.WarehouseSelector(warehouses=warehouses, on_select=set_warehouse)
```

- [ ] **Step 2: Remove the incomplete-component warning only after parity and behavior tests pass**

- [ ] **Step 3: Run the complete verification matrix**

Run: `python -m pytest -q -p no:cacheprovider`  
Run: `npm --prefix frontend test -- --run`  
Run: `npm --prefix frontend run lint`  
Run: `npm --prefix frontend run typecheck`  
Run: `npm --prefix frontend run build`  
Run: `python scripts/generate_component_reference.py`  
Run: `git diff --exit-code -- docs/components/reference`  
Run: `python -m mkdocs build --strict`  
Run: `python -m build`  
Run: `python -m twine check dist/*`  
Run: `git diff --check`  
Expected: every command exits 0.

- [ ] **Step 4: Inspect the wheel, install it in an isolated environment, and exercise HTTP/WebSocket/browser flows**

Expected: packaged assets resolve; all three components render; no credentials or raw exception details appear in responses, logs intended for clients, HTML, or browser console.

- [ ] **Step 5: Update the verification report with exact evidence and remaining external Databricks deployment gate**

- [ ] **Step 6: Commit documentation and generated assets**

```powershell
git add docs/STABILITY.md docs/components/catalog.md SKILL.md docs/verification/2026-07-14-agentic-stability-report.md brickflowui/frontend/dist
git commit -m "docs: verify Databricks integration hardening"
```
