# AgentMuru AI-Native Rearchitecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Re-found the repository as AgentMuru, a Python-first agent runtime that projects sessions, streaming, tools, approvals, artifacts, workflows, usage, and traces into Muru Workspace.

**Architecture:** Domain types and protocols form a dependency-free core. Runtime services append typed events to explicit sessions and publish them to subscribers; model, storage, server, CLI, and browser workspace adapters depend inward on those contracts. The React frontend consumes a versioned runtime protocol rather than Python VDOM patches.

**Tech Stack:** Python 3.10+, dataclasses, asyncio, FastAPI, WebSockets, Typer, React 18, TypeScript, Vite, Vitest, pytest, Ruff, mypy, MkDocs.

## Global Constraints

- Product name is **AgentMuru**; framework is **AgentMuru Runtime**; workspace is **Muru Workspace**.
- Distribution and import package are `agentmuru`; CLI is `muru`.
- This is a clean break: no `brickflowui` package, CLI alias, protocol compatibility layer, or public copy remains.
- Core domain and runtime code must not depend on FastAPI, React, Databricks, or a model-vendor SDK.
- Runtime events are typed, serializable, ordered per session, persisted before publication, and safe to expose after redaction.
- Memory retention is explicit; dangerous tool execution is denied or approval-gated by default.
- External providers and durable stores remain optional adapters; deterministic local tests use `FakeModel` and in-memory stores.
- Do not advertise an integration or durability guarantee that is not implemented and verified.

---

## File Map

The implementation creates focused packages under `agentmuru/`: `core` for events/runtime,
`sessions`, `models`, `agents`, `tools`, `approvals`, `artifacts`, `observability`, `workflows`,
`memory`, `knowledge`, `guardrails`, `protocols`, `server`, `integrations`, and `cli`. Frontend
runtime protocol/reducer files live under `frontend/src/runtime`; workspace views live under
`frontend/src/workspace`. Old UI-centric Python code and documentation are removed only after
the new package, server, CLI, frontend, examples, and tests are green.

### Task 1: Establish AgentMuru Package, Events, and Sessions

**Files:**
- Create: `agentmuru/__init__.py`, `agentmuru/version.py`
- Create: `agentmuru/core/events.py`, `agentmuru/core/errors.py`, `agentmuru/core/bus.py`
- Create: `agentmuru/sessions/models.py`, `agentmuru/sessions/store.py`, package `__init__.py` files
- Test: `tests/core/test_events.py`, `tests/sessions/test_store.py`, `tests/test_public_api.py`

**Interfaces:**
- Produces: `EventType`, `RuntimeEvent`, `EventBus`, `Message`, `RunRecord`, `Session`, `SessionStore`, `InMemorySessionStore`.
- `RuntimeEvent.new(type, *, session_id, run_id=None, trace_id=None, parent_id=None, payload=None) -> RuntimeEvent`.
- `SessionStore.append_event(session_id: str, event: RuntimeEvent) -> RuntimeEvent` assigns the next sequence atomically.

- [ ] **Step 1: Write event and session tests**

```python
def test_event_round_trip_and_ordered_append():
    store = InMemorySessionStore()
    session = store.create()
    first = store.append_event(session.id, RuntimeEvent.new(EventType.SESSION_STARTED, session_id=session.id))
    second = store.append_event(session.id, RuntimeEvent.new(EventType.USER_MESSAGE_RECEIVED, session_id=session.id, payload={"content": "hello"}))
    assert [first.sequence, second.sequence] == [1, 2]
    assert RuntimeEvent.from_dict(second.to_dict()) == second
```

- [ ] **Step 2: Run `python -m pytest tests/core/test_events.py tests/sessions/test_store.py tests/test_public_api.py -q` and confirm imports fail.**

- [ ] **Step 3: Implement frozen event envelopes, JSON-safe serialization, explicit session models, a lock-protected in-memory store, and bounded async subscriber queues.**

```python
@dataclass(frozen=True, slots=True)
class RuntimeEvent:
    id: str
    type: EventType
    timestamp: datetime
    session_id: str
    sequence: int = 0
    run_id: str | None = None
    trace_id: str | None = None
    parent_id: str | None = None
    payload: Mapping[str, JsonValue] = field(default_factory=dict)
```

- [ ] **Step 4: Run the task tests, Ruff on `agentmuru/core agentmuru/sessions`, and mypy on those packages.**
- [ ] **Step 5: Commit with `feat: establish AgentMuru event and session core`.**

### Task 2: Add Provider-Neutral Models, Agents, and Tools

**Files:**
- Create: `agentmuru/models/base.py`, `fake.py`, `registry.py`
- Create: `agentmuru/agents/agent.py`
- Create: `agentmuru/tools/base.py`, `schema.py`, `permissions.py`, `registry.py`
- Test: `tests/models/test_fake_model.py`, `tests/agents/test_agent.py`, `tests/tools/test_tools.py`

**Interfaces:**
- Consumes: `Message`, JSON-safe event payload types.
- Produces: `ModelProvider.stream(request) -> AsyncIterator[ModelEvent]`, `FakeModel`, `ModelRegistry`, `Agent`, `Tool`, `tool`, `PermissionPolicy`.
- Model events are `TextDelta`, `ToolCall`, `ModelCompleted`, and `ModelFailed`; usage is represented by `Usage(input_tokens, output_tokens, cost=None)`.

- [ ] **Step 1: Write tests for deterministic streaming, capability validation, schema derivation, async/sync execution, sensitive-field redaction, and policy decisions.**

```python
@tool(permission="database.write", approval="required")
def update_customer(customer_id: str, status: str = "active") -> dict[str, str]:
    return {"customer_id": customer_id, "status": status}

assert update_customer.input_schema["required"] == ["customer_id"]
assert update_customer.permission == "database.write"
assert update_customer.approval == ApprovalMode.REQUIRED
```

- [ ] **Step 2: Run the three test files and confirm missing-module failures.**
- [ ] **Step 3: Implement model request/event dataclasses, registry factories, deterministic `FakeModel.responses(...)`, immutable `Agent`, type-hint JSON Schema conversion, tool decorator, timeout/retry metadata, and default-deny permission policy.**
- [ ] **Step 4: Run targeted tests plus Ruff and mypy for `models`, `agents`, and `tools`.**
- [ ] **Step 5: Commit with `feat: add provider-neutral agents models and tools`.**

### Task 3: Build Runtime Execution, Artifacts, Approvals, and Tracing

**Files:**
- Create: `agentmuru/artifacts/models.py`, `store.py`
- Create: `agentmuru/approvals/models.py`, `service.py`
- Create: `agentmuru/observability/models.py`, `tracer.py`
- Create: `agentmuru/core/context.py`, `runtime.py`, `application.py`
- Test: `tests/runtime/test_agent_run.py`, `test_tool_execution.py`, `test_approval_resume.py`, `test_cancellation.py`, `test_concurrency.py`

**Interfaces:**
- Consumes: events/sessions, `Agent`, normalized model events, tools/policy.
- Produces: `Artifact`, `ArtifactStore`, `ApprovalRequest`, `ApprovalDecision`, `Tracer`, `RunContext`, `Runtime`, `Application`.
- `await Runtime.submit(session_id, content, *, idempotency_key=None) -> RunRecord` starts a tracked task.
- `await Runtime.decide_approval(approval_id, decision, *, actor, reason=None) -> ApprovalRequest` resumes a waiting run.
- `Runtime.events(session_id, after_sequence=0) -> AsyncIterator[RuntimeEvent]` replays then follows live events.

- [ ] **Step 1: Write end-to-end runtime tests**

```python
async def test_risky_tool_pauses_and_resumes():
    model = FakeModel.script([ToolCall("drop_table", {"name": "customers"}), TextDelta("done"), ModelCompleted()])
    runtime = Runtime(Application(agent=Agent(name="ops", instructions="", model=model, tools=[drop_table])))
    run = await runtime.submit(runtime.create_session().id, "clean up")
    approval = await runtime.wait_for_approval(run.id)
    assert approval.status is ApprovalStatus.PENDING
    await runtime.decide_approval(approval.id, ApprovalDecision.APPROVE, actor="tester")
    assert (await runtime.wait(run.id)).status is RunStatus.COMPLETED
```

- [ ] **Step 2: Run runtime tests and confirm missing implementations.**
- [ ] **Step 3: Implement event-first orchestration, task ownership, idempotent submission, model/tool loop, argument validation, thread offloading for sync tools, retries, approval futures, cancellation, artifacts, trace/span timing, usage aggregation, and redaction.**
- [ ] **Step 4: Verify that events are appended before bus publication and that concurrent sessions do not share messages, approvals, artifacts, tasks, or sequence counters.**
- [ ] **Step 5: Run targeted tests, Ruff, mypy, and `python examples/hello_agent.py` once Task 7 creates it.**
- [ ] **Step 6: Commit with `feat: implement observable governed agent runtime`.**

### Task 4: Add Workflows, Explicit Memory, Knowledge, Guardrails, and Handoffs

**Files:**
- Create: `agentmuru/workflows/models.py`, `runner.py`
- Create: `agentmuru/memory/base.py`, `conversation.py`
- Create: `agentmuru/knowledge/base.py`
- Create: `agentmuru/guardrails/base.py`
- Create: `agentmuru/agents/handoff.py`
- Create: `agentmuru/protocols/mcp.py`, `interoperability.py`
- Test: `tests/workflows/test_workflow.py`, `tests/test_extension_protocols.py`, `tests/agents/test_handoff.py`

**Interfaces:**
- Produces: `Workflow`, `Step`, `WorkflowRunner`, `Memory`, `ConversationMemory`, `Document`, `Retriever`, `Guardrail`, `Handoff`, `MCPToolSource` protocols.
- Workflow state is a `Mapping[str, JsonValue]`; step handlers return `StepResult(state, next_step=None, artifacts=())`.

- [ ] **Step 1: Write tests for ordered steps, conditional next step, retry exhaustion, checkpoint events, explicit memory opt-in, guardrail rejection, and typed handoff.**
- [ ] **Step 2: Run tests and confirm failures.**
- [ ] **Step 3: Implement the minimal deterministic workflow runner and structural protocols without vendor imports, network clients, background schedulers, or distributed-worker claims.**
- [ ] **Step 4: Run targeted tests, Ruff, and mypy.**
- [ ] **Step 5: Commit with `feat: add workflows handoffs and extension protocols`.**

### Task 5: Replace the Server and Wire Protocol

**Files:**
- Create: `agentmuru/server/protocol.py`, `auth.py`, `app.py`
- Create: `agentmuru/integrations/databricks/` by adapting only useful code from `brickflowui/databricks/`
- Test: `tests/server/test_http_api.py`, `test_websocket.py`, `test_security.py`

**Interfaces:**
- Consumes: `Application`, `Runtime`, session/event/artifact/approval domain APIs.
- Produces: `create_asgi_app(application, *, runtime=None) -> FastAPI`, protocol version `1` action/event envelopes.
- HTTP: `/health`, `/api/v1/app`, `/api/v1/sessions`, `/api/v1/sessions/{id}`, `/events`, `/messages`, `/runs/{id}/cancel`, `/approvals/{id}`, `/artifacts/{id}`.
- WebSocket: `/api/v1/sessions/{id}/stream?after=<sequence>` with `ping`, `submit_message`, `cancel_run`, and `decide_approval` actions.

- [ ] **Step 1: Write contract tests for metadata, validation errors, auth/role checks, payload limits, trusted origins, replay ordering, reconnect cursor, idempotency, and redacted public failures.**
- [ ] **Step 2: Run server tests and confirm missing routes.**
- [ ] **Step 3: Implement Pydantic request models at the adapter boundary, versioned envelopes, runtime action mapping, bounded WebSocket sends, heartbeat, cleanup, safe errors, retained host/origin/CSRF/auth controls, and allowlisted artifact downloads.**
- [ ] **Step 4: Adapt Databricks environment, SQL, Unity Catalog, and services modules beneath `agentmuru.integrations.databricks` without importing runtime internals.**
- [ ] **Step 5: Run server, security, and Databricks adapter tests plus Ruff/mypy.**
- [ ] **Step 6: Commit with `feat: expose AgentMuru runtime protocol`.**

### Task 6: Rebuild the Frontend as Muru Workspace

**Files:**
- Replace: `frontend/src/App.tsx`, `frontend/src/types.ts`, `frontend/src/theme.css`
- Create: `frontend/src/runtime/protocol.ts`, `reducer.ts`, `client.ts`
- Create: `frontend/src/workspace/Workspace.tsx`, `SessionRail.tsx`, `Conversation.tsx`, `ActivityCard.tsx`, `ApprovalCard.tsx`, `ArtifactPanel.tsx`, `TracePanel.tsx`, `RunComposer.tsx`
- Test: colocated `*.test.ts` and `*.test.tsx` files plus `frontend/e2e/workspace.spec.ts`

**Interfaces:**
- Consumes: server protocol version 1 envelopes.
- Produces: accessible session/run workspace and a pure `reduceWorkspace(state, event)` projection.

- [ ] **Step 1: Write reducer tests for snapshot/replay, token accumulation, tool lifecycle, approval state, artifacts, trace nesting, terminal errors, usage, deduplication, and out-of-order rejection.**
- [ ] **Step 2: Write component tests for empty, connecting, streaming, tool, approval, artifact, error, cancelled, and completed states.**
- [ ] **Step 3: Run `npm test -- --run` and confirm failures.**
- [ ] **Step 4: Implement the typed protocol, reconnecting client with last-sequence cursor, pure reducer, and Muru Workspace components using semantic HTML, keyboard-visible actions, responsive panels, safe markdown-as-text initially, and lazy artifact/trace panels.**
- [ ] **Step 5: Replace BrickflowUI names/assets/colors with AgentMuru/Muru Workspace and remove the generic VDOM renderer and component switch.**
- [ ] **Step 6: Run frontend tests, lint, typecheck, production build, bundle budget, and Playwright smoke test.**
- [ ] **Step 7: Commit with `feat: build Muru Workspace runtime projection`.**

### Task 7: Replace Packaging, CLI, Examples, Documentation, and Repository Guidance

**Files:**
- Modify: `pyproject.toml`, `mkdocs.yml`, `README.md`, `DEVELOPMENT.md`, `CONTRIBUTING.md`, `SECURITY.md`
- Create: `AGENTS.md`, `agentmuru/cli/main.py`, `agentmuru/cli/templates/default/`
- Create: `examples/hello_agent.py`, `examples/governed_data_agent.py`, `examples/workflow_agent.py`
- Create: `docs/architecture/current-state.md`, `target-state.md`, `ai-native-transformation.md`, `decisions.md`
- Create: `docs/getting-started.md`, `docs/concepts/*.md`, `docs/guides/*.md`, `docs/migration-from-brickflowui.md`
- Replace tests: `tests/test_cli.py`, `tests/test_packaging.py`, `tests/test_examples.py`, `tests/test_branding.py`

**Interfaces:**
- Produces: distribution `agentmuru`, console script `muru`, commands `init`, `dev`, `run`, `doctor`, `version`.

- [ ] **Step 1: Write packaging/branding tests that reject public `brickflowui` imports, console scripts, default copy, package artifacts, and documentation navigation while permitting the migration/history documents to name the former project.**
- [ ] **Step 2: Run the tests and confirm the old package metadata fails them.**
- [ ] **Step 3: Update metadata, entry points, build includes, version, URLs, keywords, frontend package name, MkDocs identity/navigation, and CI paths.**
- [ ] **Step 4: Implement CLI commands using explicit app targets (`module:attribute`), safe project creation, environment diagnostics, and Uvicorn startup.**
- [ ] **Step 5: Add three deterministic runnable examples and rewrite the README/docs around runtime-first concepts, security boundaries, extension interfaces, migration matrix, exact commands, and verified limitations.**
- [ ] **Step 6: Add repository-specific `AGENTS.md` rules covering dependency direction, event append-before-publish, public API stability, redaction, tests, frontend protocol versioning, and verification commands.**
- [ ] **Step 7: Run CLI, example, packaging, branding, and strict MkDocs tests.**
- [ ] **Step 8: Commit with `docs: complete AgentMuru developer experience`.**

### Task 8: Remove Obsolete Architecture and Complete Release Verification

**Files:**
- Remove: `brickflowui/`, obsolete UI-centric examples, component catalog/reference docs, old branding assets, old repository-local skills tied to BrickflowUI, superseded tests
- Modify: `.github/workflows/*`, `.gitignore`, transformation log and changelog
- Test: entire Python/frontend/docs/package suite

**Interfaces:**
- Consumes: every new package and verification command.
- Produces: a clean AgentMuru source tree and truthful release report.

- [ ] **Step 1: Confirm `rg -l "from brickflowui|import brickflowui|brickflowui =|BrickflowUI"` only returns migration/history records before deleting the old package.**
- [ ] **Step 2: Remove the obsolete package, VDOM renderer, component tests/docs/examples/assets, generated site/dist artifacts, and stale temporary directories; preserve license and relevant git history.**
- [ ] **Step 3: Run `python -m pytest -q`, `ruff check .`, `mypy agentmuru`, frontend test/lint/typecheck/build/bundle checks, strict MkDocs build, `python -m build`, wheel-content inspection, `muru doctor`, all examples, and the local server smoke test.**
- [ ] **Step 4: Search for `TODO|FIXME|pass|NotImplementedError`, classify intentional protocol methods, and remove accidental placeholders or dead compatibility paths.**
- [ ] **Step 5: Inspect `git diff --check`, `git diff --stat`, `git status --short`, public imports, event schemas, permission defaults, logs, and browser payloads; repair every in-scope failure.**
- [ ] **Step 6: Update `docs/architecture/ai-native-transformation.md` and `docs/CHANGELOG.md` with exact verification results, removed APIs, external checks not run, and remaining product opportunities.**
- [ ] **Step 7: Commit with `release: re-found framework as AgentMuru`.**
