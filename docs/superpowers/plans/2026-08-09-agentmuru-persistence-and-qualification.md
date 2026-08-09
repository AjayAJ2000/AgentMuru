# AgentMuru Persistence and Qualification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add durable SQLite state to AgentMuru and prove every supported framework path through clean-install and runtime qualification.

**Architecture:** Keep the runtime dependent on store protocols and put SQLite behind focused adapters sharing a `SQLiteDatabase`. Replace reference mutation with explicit store methods, use `BEGIN IMMEDIATE` for event counters, and apply the same behavioral contracts to in-memory and SQLite implementations.

**Tech Stack:** Python 3.10+, standard-library `sqlite3`, asyncio, pytest, pytest-asyncio, FastAPI, Typer, React/Vite, Vitest, Playwright.

## Global Constraints

- Product name is **AgentMuru**; package is `agentmuru`; CLI is `muru`; browser is **Muru Workspace**.
- SQLite uses only Python's standard library; no new production dependency is allowed.
- Events are appended before publication and use monotonic per-session sequences.
- SQLite is for one active AgentMuru runtime process with modest concurrent store clients.
- Public errors never expose SQL, filesystem paths, secrets, raw tool exceptions, or stored content.
- New behavior and defect fixes follow a witnessed red-green-refactor cycle.
- Existing in-memory defaults remain the zero-configuration experience.
- Python 3.10 through 3.13 remain supported.

---

### Task 1: Define storage errors and persistent value codecs

**Files:**
- Modify: `agentmuru/core/errors.py`
- Create: `agentmuru/persistence/__init__.py`
- Create: `agentmuru/persistence/codecs.py`
- Test: `tests/persistence/test_codecs.py`

**Interfaces:**
- Produces: `StorageError`, `StorageBusyError`, `StorageSerializationError`, `StorageCorruptError`, and `StorageMigrationError`.
- Produces: `encode_json(value: Any) -> str`, `decode_json(value: str) -> Any`, `encode_content(value: Any) -> tuple[str, bytes]`, and `decode_content(encoding: str, payload: bytes) -> Any`.

- [ ] **Step 1: Write failing codec and error tests.**

```python
def test_content_codec_round_trips_supported_values() -> None:
    values = ["hello", b"binary", {"rows": [1, 2]}, [True, None, 3.5]]
    for value in values:
        encoding, payload = encode_content(value)
        assert decode_content(encoding, payload) == value


def test_content_codec_rejects_non_finite_or_custom_values() -> None:
    with pytest.raises(StorageSerializationError) as exc_info:
        encode_content({"value": float("nan")})
    assert exc_info.value.code == "storage_serialization"
```

- [ ] **Step 2: Run the focused tests and confirm they fail because the persistence package and errors do not exist.**

Run: `python -m pytest tests/persistence/test_codecs.py -q`

- [ ] **Step 3: Implement the storage error hierarchy and deterministic codecs.**

```python
class StorageError(AgentMuruError):
    code = "storage_error"


class StorageSerializationError(StorageError):
    code = "storage_serialization"
```

```python
def encode_content(value: Any) -> tuple[str, bytes]:
    if isinstance(value, str):
        return "text", value.encode("utf-8")
    if isinstance(value, bytes):
        return "bytes", value
    return "json", encode_json(value).encode("utf-8")
```

- [ ] **Step 4: Run codec tests, Ruff, and MyPy for the new module.**

Run: `python -m pytest tests/persistence/test_codecs.py -q`

Run: `python -m ruff check agentmuru/persistence agentmuru/core/errors.py tests/persistence/test_codecs.py`

Run: `python -m mypy agentmuru/persistence agentmuru/core/errors.py`

- [ ] **Step 5: Commit the codec boundary.**

```powershell
git add agentmuru/core/errors.py agentmuru/persistence tests/persistence/test_codecs.py
git commit -m "feat: define durable storage codecs"
```

### Task 2: Replace reference mutation with explicit session operations

**Files:**
- Modify: `agentmuru/sessions/store.py`
- Modify: `agentmuru/sessions/__init__.py`
- Test: `tests/sessions/test_store_contract.py`
- Modify: `tests/sessions/test_store.py`

**Interfaces:**
- Produces `SessionStore.append_message(session_id: str, message: Message) -> Message`.
- Produces `SessionStore.create_run(run: RunRecord) -> RunRecord`.
- Produces `SessionStore.update_run(run: RunRecord) -> RunRecord`.
- Produces `SessionStore.get_run(run_id: str) -> RunRecord`.
- Produces `SessionStore.get_idempotent_run(session_id: str, key: str) -> RunRecord | None`.
- Produces `SessionStore.bind_idempotency_key(session_id: str, key: str, run_id: str) -> None`.
- Produces `SessionStore.recover_interrupted_runs() -> list[RunRecord]`.

- [ ] **Step 1: Create a reusable contract function and failing explicit-mutation tests.**

```python
def assert_session_store_contract(store: SessionStore) -> None:
    session = store.create(user_id="user-1", title="Durable")
    message = store.append_message(session.id, Message(role=MessageRole.USER, content="hello"))
    run = store.create_run(RunRecord(session_id=session.id, agent_name="assistant"))
    run.status = RunStatus.RUNNING
    store.update_run(run)
    store.bind_idempotency_key(session.id, "request-1", run.id)

    loaded = store.get(session.id)
    assert loaded.messages == [message]
    assert store.get_run(run.id).status is RunStatus.RUNNING
    assert store.get_idempotent_run(session.id, "request-1") == store.get_run(run.id)
```

- [ ] **Step 2: Run the contract against `InMemorySessionStore` and confirm missing-method failure.**

Run: `python -m pytest tests/sessions/test_store_contract.py -q`

- [ ] **Step 3: Implement explicit in-memory operations with copies of mutable records at the storage boundary.**

```python
def append_message(self, session_id: str, message: Message) -> Message:
    with self._lock:
        session = self.get(session_id)
        session.messages.append(message)
        session.updated_at = message.created_at
    return message
```

Use a run index keyed by run ID and an idempotency index keyed by `(session_id, key)`. Recovery changes queued, running, and waiting-approval runs to `FAILED`, sets `error_code="process_interrupted"`, and returns the recovered records.

- [ ] **Step 4: Run all session tests and type checks.**

Run: `python -m pytest tests/sessions -q`

Run: `python -m mypy agentmuru/sessions`

- [ ] **Step 5: Commit the explicit session contract.**

```powershell
git add agentmuru/sessions tests/sessions
git commit -m "refactor: make session mutations explicit"
```

### Task 3: Build the SQLite database and versioned schema

**Files:**
- Create: `agentmuru/persistence/schema.py`
- Create: `agentmuru/persistence/database.py`
- Test: `tests/persistence/test_database.py`

**Interfaces:**
- Produces `SCHEMA_VERSION = 1` and `MIGRATION_1: tuple[str, ...]`.
- Produces `SQLiteDatabase(path: str | Path, busy_timeout_ms: int = 5000, max_retries: int = 4)` with public read-only `.path: Path`.
- Produces `SQLiteDatabase.connect() -> sqlite3.Connection` and `SQLiteDatabase.write(operation: Callable[[sqlite3.Connection], T], *, immediate: bool = False) -> T`.

- [ ] **Step 1: Write failing schema, pragma, transaction, and incompatible-version tests.**

```python
def test_database_initializes_schema_and_pragmas(tmp_path: Path) -> None:
    database = SQLiteDatabase(tmp_path / "agentmuru.db")
    with database.connect() as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
        assert connection.execute("SELECT version FROM schema_metadata").fetchone()[0] == 1


def test_database_rejects_newer_schema(tmp_path: Path) -> None:
    path = tmp_path / "newer.db"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE schema_metadata(version INTEGER NOT NULL)")
        connection.execute("INSERT INTO schema_metadata VALUES (999)")
    with pytest.raises(StorageMigrationError):
        SQLiteDatabase(path)
```

- [ ] **Step 2: Run the database tests and confirm imports or schema assertions fail.**

Run: `python -m pytest tests/persistence/test_database.py -q`

- [ ] **Step 3: Implement the schema and retrying write wrapper.**

The schema must create the nine approved tables and `UNIQUE(session_id, sequence)`. `write(..., immediate=True)` must execute `BEGIN IMMEDIATE`, commit on success, roll back on failure, and retry only `locked` or `busy` operational errors with delays of 25, 50, 100, and 200 milliseconds before raising `StorageBusyError`.

```python
def write(self, operation: Callable[[sqlite3.Connection], T], *, immediate: bool = False) -> T:
    for attempt in range(self.max_retries + 1):
        try:
            with self.connect() as connection:
                connection.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
                value = operation(connection)
                connection.commit()
                return value
        except sqlite3.OperationalError as exc:
            if not _is_busy(exc) or attempt == self.max_retries:
                raise _public_storage_error(exc) from exc
            time.sleep(0.025 * (2**attempt))
    raise AssertionError("unreachable")
```

- [ ] **Step 4: Run database tests, inspect the schema, and run static checks.**

Run: `python -m pytest tests/persistence/test_database.py -q`

Run: `python -m ruff check agentmuru/persistence tests/persistence`

Run: `python -m mypy agentmuru/persistence`

- [ ] **Step 5: Commit the SQLite database foundation.**

```powershell
git add agentmuru/persistence/schema.py agentmuru/persistence/database.py tests/persistence/test_database.py
git commit -m "feat: add versioned SQLite database"
```

### Task 4: Implement SQLite sessions, ordering, recovery, and subscriptions

**Files:**
- Create: `agentmuru/persistence/session_store.py`
- Test: `tests/persistence/test_sqlite_sessions.py`
- Modify: `tests/sessions/test_store_contract.py`

**Interfaces:**
- Produces `SQLiteSessionStore(database: SQLiteDatabase, poll_interval: float = 0.05)` implementing `SessionStore` and `subscribe()`.
- Consumes the explicit mutation contract from Task 2 and database transaction API from Task 3.

- [ ] **Step 1: Apply the shared session contract to a reopened SQLite store.**

```python
def test_sqlite_store_survives_reopen(tmp_path: Path) -> None:
    path = tmp_path / "agentmuru.db"
    first = SQLiteSessionStore(SQLiteDatabase(path))
    assert_session_store_contract(first)
    second = SQLiteSessionStore(SQLiteDatabase(path))
    assert len(second.list(user_id="user-1")) == 1
```

- [ ] **Step 2: Run the reopen contract and confirm it fails because `SQLiteSessionStore` is missing.**

Run: `python -m pytest tests/persistence/test_sqlite_sessions.py::test_sqlite_store_survives_reopen -q`

- [ ] **Step 3: Implement session, message, run, event, and idempotency row mapping.**

`get()` reconstructs one `Session` with ordered messages, runs, and events. `list()` returns lightweight sessions ordered by `updated_at DESC`. Every timestamp uses ISO-8601 UTC. Metadata and event payloads use the Task 1 JSON codec.

- [ ] **Step 4: Add and witness failing concurrent sequence tests.**

```python
def test_two_store_instances_allocate_unique_sequences(tmp_path: Path) -> None:
    database = SQLiteDatabase(tmp_path / "agentmuru.db")
    first = SQLiteSessionStore(database)
    second = SQLiteSessionStore(SQLiteDatabase(database.path))
    session = first.create()
    with ThreadPoolExecutor(max_workers=8) as pool:
        events = list(pool.map(
            lambda index: (first if index % 2 else second).append_event(
                session.id,
                RuntimeEvent.new(EventType.USER_MESSAGE_RECEIVED, session_id=session.id),
            ),
            range(40),
        ))
    assert sorted(event.sequence for event in events) == list(range(1, 41))
```

Run: `python -m pytest tests/persistence/test_sqlite_sessions.py::test_two_store_instances_allocate_unique_sequences -q`

- [ ] **Step 5: Implement counter allocation inside `BEGIN IMMEDIATE` and publish only after commit.**

Use `UPDATE event_counters SET next_sequence = next_sequence + 1 ... RETURNING next_sequence - 1`; initialize the counter during session creation. Do not publish if insertion or commit fails.

- [ ] **Step 6: Add and witness failing cross-instance subscription and recovery tests.**

```python
@pytest.mark.asyncio
async def test_subscription_observes_another_store_instance(tmp_path: Path) -> None:
    path = tmp_path / "agentmuru.db"
    subscriber = SQLiteSessionStore(SQLiteDatabase(path), poll_interval=0.01)
    writer = SQLiteSessionStore(SQLiteDatabase(path))
    session = subscriber.create()
    stream = subscriber.subscribe(session.id)
    writer.append_event(session.id, RuntimeEvent.new(EventType.SESSION_STARTED, session_id=session.id))
    assert (await asyncio.wait_for(anext(stream), 0.5)).sequence == 1
    await stream.aclose()
```

- [ ] **Step 7: Implement polling subscriptions and `process_interrupted` recovery.**

Polling queries `events(after_sequence=cursor)` after an in-process wake or poll timeout. Recovery updates nonterminal runs in one transaction and returns reconstructed failed records; it does not delete tasks, messages, approvals, or events.

- [ ] **Step 8: Run session contracts, persistence tests, and static checks.**

Run: `python -m pytest tests/sessions tests/persistence/test_sqlite_sessions.py -q`

Run: `python -m ruff check agentmuru/persistence/session_store.py tests/persistence/test_sqlite_sessions.py`

Run: `python -m mypy agentmuru/persistence/session_store.py`

- [ ] **Step 9: Commit durable sessions.**

```powershell
git add agentmuru/persistence/session_store.py tests/persistence/test_sqlite_sessions.py tests/sessions/test_store_contract.py
git commit -m "feat: persist sessions and ordered events in SQLite"
```

### Task 5: Implement SQLite artifacts with adapter-independent validation

**Files:**
- Modify: `agentmuru/artifacts/store.py`
- Create: `agentmuru/persistence/artifact_store.py`
- Test: `tests/artifacts/test_store_contract.py`
- Test: `tests/persistence/test_sqlite_artifacts.py`

**Interfaces:**
- Produces `validate_artifact_content(value: Any) -> None` used by both stores.
- Produces `SQLiteArtifactStore(database: SQLiteDatabase)` implementing `ArtifactStore`.

- [ ] **Step 1: Write a shared artifact contract covering text, bytes, JSON, filtering, and rejection.**

```python
def assert_artifact_store_contract(store: ArtifactStore, session_id: str) -> None:
    text = store.create(session_id=session_id, kind=ArtifactKind.MARKDOWN, name="report.md",
                        content="# Report", mime_type="text/markdown", creator="analyst")
    binary = store.create(session_id=session_id, kind=ArtifactKind.FILE, name="data.bin",
                          content=b"\x00\x01", mime_type="application/octet-stream", creator="analyst")
    assert store.get(text.id).content == "# Report"
    assert store.get(binary.id).content == b"\x00\x01"
    assert [item.id for item in store.list(session_id=session_id)] == [text.id, binary.id]
```

- [ ] **Step 2: Run contracts against both stores and confirm the SQLite import fails.**

Run: `python -m pytest tests/artifacts/test_store_contract.py tests/persistence/test_sqlite_artifacts.py -q`

- [ ] **Step 3: Implement shared validation and SQLite row mapping with `content_encoding`.**

The in-memory adapter calls `encode_content` for validation but retains the original supported value. The SQLite adapter stores the encoding and bytes and restores the exact public value.

- [ ] **Step 4: Reopen the database and verify every `ArtifactKind` round-trips.**

Run: `python -m pytest tests/artifacts tests/persistence/test_sqlite_artifacts.py -q`

- [ ] **Step 5: Commit durable artifacts.**

```powershell
git add agentmuru/artifacts/store.py agentmuru/persistence/artifact_store.py tests/artifacts tests/persistence/test_sqlite_artifacts.py
git commit -m "feat: persist validated artifacts in SQLite"
```

### Task 6: Add a durable approval store and service integration

**Files:**
- Create: `agentmuru/approvals/store.py`
- Modify: `agentmuru/approvals/service.py`
- Modify: `agentmuru/approvals/__init__.py`
- Create: `agentmuru/persistence/approval_store.py`
- Test: `tests/approvals/test_store_contract.py`
- Test: `tests/persistence/test_sqlite_approvals.py`
- Modify: `tests/runtime/test_approval_resume.py`

**Interfaces:**
- Produces `ApprovalStore.create(request)`, `get(approval_id)`, `list(session_id=None)`, and `save(request)`.
- Produces `InMemoryApprovalStore` and `SQLiteApprovalStore`.
- Changes `ApprovalService.__init__(store: ApprovalStore | None = None)` while keeping the in-memory default.

- [ ] **Step 1: Write failing approval-store and service tests.**

```python
@pytest.mark.asyncio
async def test_approval_service_persists_decision(tmp_path: Path) -> None:
    database = SQLiteDatabase(tmp_path / "agentmuru.db")
    service = ApprovalService(SQLiteApprovalStore(database))
    request = await service.create(session_id="s", run_id="r", tool_call_id="c",
                                   tool_name="publish", arguments={"token": "[redacted]"},
                                   permission="network", risk="high")
    await service.decide(request.id, ApprovalDecision.APPROVE, actor="reviewer")
    reopened = SQLiteApprovalStore(SQLiteDatabase(database.path))
    assert reopened.get(request.id).status is ApprovalStatus.APPROVED
```

- [ ] **Step 2: Run the focused test and confirm the new store types are missing.**

Run: `python -m pytest tests/approvals/test_store_contract.py tests/persistence/test_sqlite_approvals.py -q`

- [ ] **Step 3: Implement the in-memory and SQLite stores and delegate service state to them.**

Async waiter futures remain process-local. Durable records hold requests and decisions; a pending request loaded after restart is audit history and is resolved by runtime interruption recovery, not attached to a resurrected future.

- [ ] **Step 4: Run approval and runtime approval tests.**

Run: `python -m pytest tests/approvals tests/persistence/test_sqlite_approvals.py tests/runtime/test_approval_resume.py -q`

- [ ] **Step 5: Commit durable approvals.**

```powershell
git add agentmuru/approvals agentmuru/persistence/approval_store.py tests/approvals tests/persistence/test_sqlite_approvals.py tests/runtime/test_approval_resume.py
git commit -m "feat: persist approval audit records"
```

### Task 7: Compose SQLite persistence and refactor Runtime to use it

**Files:**
- Create: `agentmuru/persistence/sqlite.py`
- Modify: `agentmuru/persistence/__init__.py`
- Modify: `agentmuru/core/runtime.py`
- Modify: `agentmuru/core/application.py`
- Modify: `agentmuru/__init__.py`
- Modify: `tests/runtime/test_agent_run.py`
- Create: `tests/runtime/test_sqlite_runtime.py`
- Modify: `tests/test_public_api.py`

**Interfaces:**
- Produces `SQLitePersistence(path, busy_timeout_ms=5000, max_retries=4, poll_interval=0.05)` with `.sessions`, `.artifacts`, and `.approval_service()`.
- Runtime uses the Task 2 explicit session operations and no longer owns a separate idempotency dictionary.

- [ ] **Step 1: Write failing public-composition and restart-history tests.**

```python
@pytest.mark.asyncio
async def test_runtime_history_survives_reopen(tmp_path: Path) -> None:
    path = tmp_path / "agentmuru.db"
    first_persistence = SQLitePersistence(path)
    first = Runtime(Application(agent=_agent(), session_store=first_persistence.sessions,
                                artifact_store=first_persistence.artifacts),
                    approvals=first_persistence.approval_service())
    session = first.create_session(title="durable")
    run = await first.submit(session.id, "hello", idempotency_key="one")
    assert (await first.wait(run.id)).status is RunStatus.COMPLETED

    second_persistence = SQLitePersistence(path)
    second = Runtime(Application(agent=_agent(), session_store=second_persistence.sessions,
                                 artifact_store=second_persistence.artifacts),
                     approvals=second_persistence.approval_service())
    assert second.sessions.get(session.id).messages[-1].content
    assert second.get_run(run.id).status is RunStatus.COMPLETED
```

- [ ] **Step 2: Run the new runtime tests and confirm persistence composition is missing.**

Run: `python -m pytest tests/runtime/test_sqlite_runtime.py tests/test_public_api.py -q`

- [ ] **Step 3: Implement `SQLitePersistence` and export it from the stable public API.**

```python
class SQLitePersistence:
    def __init__(self, path: str | Path, **options: Any) -> None:
        self.database = SQLiteDatabase(
            path,
            busy_timeout_ms=int(options.get("busy_timeout_ms", 5000)),
            max_retries=int(options.get("max_retries", 4)),
        )
        self.sessions = SQLiteSessionStore(self.database, poll_interval=options.get("poll_interval", 0.05))
        self.artifacts = SQLiteArtifactStore(self.database)
        self.approvals = SQLiteApprovalStore(self.database)

    def approval_service(self) -> ApprovalService:
        return ApprovalService(self.approvals)
```

- [ ] **Step 4: Refactor Runtime mutations test-first.**

Replace direct `session.messages.append`, `session.runs.append`, `_runs` lookup, and `_idempotency` lookup with store calls. After every run-status transition call `update_run`. Keep `_tasks` only for active coroutine control. On initialization, emit `run.failed` events for records returned by `recover_interrupted_runs()`.

- [ ] **Step 5: Verify idempotency, cancellation, approval, handoff, and SQLite recovery together.**

Run: `python -m pytest tests/runtime tests/agents/test_handoff.py tests/persistence -q`

- [ ] **Step 6: Run all Python tests and static checks before committing.**

Run: `python -m pytest -q`

Run: `python -m ruff check agentmuru tests`

Run: `python -m mypy agentmuru`

- [ ] **Step 7: Commit runtime persistence integration.**

```powershell
git add agentmuru tests/runtime tests/test_public_api.py
git commit -m "feat: compose durable AgentMuru runtimes"
```

### Task 8: Expand server and Muru Workspace qualification

**Files:**
- Create: `tests/server/test_sqlite_api.py`
- Modify: `tests/server/test_http_api.py`
- Modify: `tests/server/test_websocket.py`
- Modify: `frontend/src/runtime/reducer.test.ts`
- Modify: `frontend/src/workspace/Workspace.test.tsx`
- Create: `frontend/e2e/workspace-durable.spec.ts`

**Interfaces:**
- Verifies every public HTTP route and WebSocket action with SQLite-backed application state.
- Verifies loading, empty, streaming, tool, approval, artifact, trace, cancellation, failure, reconnect, and mobile Workspace states.

- [ ] **Step 1: Write failing SQLite server restart and replay tests.**

```python
def test_sqlite_backed_api_restores_session_history(tmp_path: Path) -> None:
    path = tmp_path / "agentmuru.db"
    first = _client_with_sqlite(path)
    created = first.post("/api/v1/sessions", json={"title": "durable"}).json()
    first.post(
        f"/api/v1/sessions/{created['id']}/messages",
        json={"content": "hello", "idempotency_key": "request-1"},
    )
    second = _client_with_sqlite(path)
    restored = second.get(f"/api/v1/sessions/{created['id']}")
    assert restored.status_code == 200
    assert restored.json()["session"]["messages"][0]["content"] == "hello"
```

- [ ] **Step 2: Run the SQLite server test and confirm restart behavior fails before server integration is corrected.**

Run: `python -m pytest tests/server/test_sqlite_api.py -q`

- [ ] **Step 3: Make the server consume reconstructed session/run/artifact/approval records without adapter assumptions.**

Keep route signatures unchanged. `GET /api/v1/runs/{run_id}` uses `Runtime.get_run()`, session detail uses store-reconstructed ordered collections, and WebSocket replay uses `subscribe(after_sequence=...)`.

- [ ] **Step 4: Add failing reducer and component cases for every documented Workspace state.**

```tsx
it("renders durable reconnect and interrupted-run state", () => {
  render(<Workspace initialState={stateWithInterruptedRun()} />);
  expect(screen.getByText(/previous process was interrupted/i)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /start a new run/i })).toBeEnabled();
});
```

- [ ] **Step 5: Run frontend tests and confirm the new interrupted/reconnect expectations fail.**

Run from `frontend`: `npm test -- --run`

- [ ] **Step 6: Implement only the missing projection and accessible status copy required by the failing tests.**

The frontend remains a projection: it derives `process_interrupted` from runtime events and does not own recovery logic. Approval, cancellation, error, and reconnect controls retain keyboard and screen-reader labels.

- [ ] **Step 7: Add a browser flow that creates history, restarts the server fixture, reconnects, and verifies replay.**

Run from `frontend`: `npm run test:e2e -- workspace-durable.spec.ts`

- [ ] **Step 8: Run the complete server and frontend qualification subset.**

Run: `python -m pytest tests/server -q`

Run from `frontend`: `npm test -- --run`

Run from `frontend`: `npm run lint`

Run from `frontend`: `npm run typecheck`

Run from `frontend`: `npm run test:e2e`

- [ ] **Step 9: Commit server and Workspace qualification.**

```powershell
git add tests/server frontend/src frontend/e2e/workspace-durable.spec.ts
git commit -m "test: qualify durable Muru Workspace flows"
```

### Task 9: Add the complete runnable scenario gallery

**Files:**
- Create: `examples/governed_tool_agent.py`
- Create: `examples/artifact_agent.py`
- Create: `examples/durable_agent.py`
- Create: `examples/handoff_agent.py`
- Create: `examples/databricks_agent.py`
- Modify: `examples/workflow_agent.py`
- Modify: `tests/test_examples.py`
- Create: `tests/qualification/test_scenarios.py`

**Interfaces:**
- Each module exports `application: Application` or a deterministic `main() -> dict[str, Any]`.
- `durable_agent.create_application(database_path: Path) -> tuple[Application, SQLitePersistence]` demonstrates reopening.

- [ ] **Step 1: Add failing imports and deterministic scenario assertions.**

```python
@pytest.mark.parametrize("module_name", [
    "examples.governed_tool_agent",
    "examples.artifact_agent",
    "examples.durable_agent",
    "examples.handoff_agent",
    "examples.databricks_agent",
])
def test_scenario_module_imports_without_credentials(module_name: str) -> None:
    module = importlib.import_module(module_name)
    assert module is not None
```

- [ ] **Step 2: Run the scenario tests and confirm missing-module failures.**

Run: `python -m pytest tests/test_examples.py tests/qualification/test_scenarios.py -q`

- [ ] **Step 3: Implement minimal examples using only stable public APIs.**

The governed example demonstrates allow, deny, approve, reject, and expiry using deterministic fake-model turns. The artifact example creates markdown, JSON, table, code, and file artifacts. The durable example completes a run, closes references, reopens the same database, and prints restored session/run counts. The Databricks example imports safely and checks configuration before any network action.

- [ ] **Step 4: Execute every scenario test and public example.**

Run: `python -m pytest tests/test_examples.py tests/qualification/test_scenarios.py -q`

Run: `python examples/workflow_agent.py`

Run: `python examples/durable_agent.py`

- [ ] **Step 5: Commit the qualification scenarios.**

```powershell
git add examples tests/test_examples.py tests/qualification/test_scenarios.py
git commit -m "test: add complete AgentMuru scenario gallery"
```

### Task 10: Qualify the built wheel outside the checkout

**Files:**
- Create: `qualification/run_clean_install.py`
- Create: `qualification/installed_smoke.py`
- Create: `qualification/README.md`
- Create: `tests/qualification/test_clean_install_harness.py`
- Modify: `.gitignore`
- Modify: `pyproject.toml`
- Modify: `agentmuru/version.py`
- Modify: `tests/test_packaging.py`

**Interfaces:**
- Produces `python qualification/run_clean_install.py --wheel dist/agentmuru-0.2.0-py3-none-any.whl --report .tmp/qualification.json`.
- The report is JSON with `environment`, `commands`, `scenarios`, `databricks_live`, and `failures` keys.

- [ ] **Step 1: Write a failing harness test for command construction and source-tree isolation.**

```python
def test_harness_runs_smoke_from_outside_repository(tmp_path: Path) -> None:
    command = build_smoke_command(tmp_path / "venv", tmp_path / "installed_smoke.py")
    assert command.cwd == tmp_path
    assert "PYTHONPATH" not in command.environment
```

- [ ] **Step 2: Run the harness unit test and confirm the qualification module is missing.**

Run: `python -m pytest tests/qualification/test_clean_install_harness.py -q`

- [ ] **Step 3: Implement the clean-environment runner.**

It creates a version-specific folder beneath `.tmp`, builds a venv with `venv`, installs the exact local wheel and its declared dependencies with pip, installs the wheel's `databricks` extra for optional-adapter imports, runs all CLI commands, scaffolds an application, executes installed smoke scenarios from the temporary directory, starts the installed server on a free loopback port, and records exit codes and durations. It must fail the process when any required check fails. Add `.superpowers/` and qualification environments/reports under `.tmp/` to `.gitignore`.

- [ ] **Step 4: Add package version `0.2.0` and ensure qualification files are included only in the source distribution.**

Update both `pyproject.toml` and `agentmuru/version.py` to `0.2.0`; add a packaging assertion for exact equality; keep the wheel limited to `agentmuru` plus bundled frontend assets.

- [ ] **Step 5: Build and run the actual clean-install qualification.**

Run: `python -m build`

Run: `python qualification/run_clean_install.py --wheel dist/agentmuru-0.2.0-py3-none-any.whl --report .tmp/qualification.json`

Expected: exit code 0, import origin inside the temporary environment, every required CLI/scenario check marked passed.

- [ ] **Step 6: Commit the reproducible qualification harness.**

```powershell
git add qualification tests/qualification tests/test_packaging.py .gitignore pyproject.toml agentmuru/version.py
git commit -m "test: qualify the installed AgentMuru wheel"
```

### Task 11: Run the complete core verification gate

**Files:**
- Verify: `agentmuru/`
- Verify: `tests/`
- Verify: `examples/`
- Verify: `frontend/`
- Verify: `qualification/`

**Interfaces:**
- Produces fresh evidence consumed by the documentation and release plan.

- [ ] **Step 1: Run the complete Python suite.**

Run: `python -m pytest -q`

- [ ] **Step 2: Run Python lint and type checks.**

Run: `python -m ruff check agentmuru tests qualification`

Run: `python -m mypy agentmuru`

- [ ] **Step 3: Run frontend tests, lint, typecheck, build, bundle, and browser checks.**

Run from `frontend`: `npm test -- --run`

Run from `frontend`: `npm run lint`

Run from `frontend`: `npm run typecheck`

Run from `frontend`: `npm run build`

Run from `frontend`: `npm run check:bundle`

Run from `frontend`: `npm run test:e2e`

- [ ] **Step 4: Rebuild and rerun clean-install qualification after the frontend bundle is embedded.**

Run: `python -m build`

Run: `python qualification/run_clean_install.py --wheel dist/agentmuru-0.2.0-py3-none-any.whl --report .tmp/qualification.json`

- [ ] **Step 5: Inspect the final diff and commit only any verification-driven fixes with their regression tests.**

Run: `git diff --check`

Run: `git status --short`
