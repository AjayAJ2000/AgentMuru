# AgentMuru Adaptive Agent Compiler and Orchestration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compile typed user actions and examples into a portable agent pack, benchmark compatible SLM configurations, choose the smallest passing team, and execute deterministic, shared-model, and sequential multi-model routes in simulation mode.

**Architecture:** Treat the pack, compiler, evaluator, selector, and orchestrator as separate domain packages. The compiler creates declarative files from curated templates; evaluation activates a pack only after mandatory gates pass. Agents exchange typed envelopes and the scheduler consumes model-manager leases from the previous tranche.

**Tech Stack:** Go standard library JSON/archive support, existing native contracts/events/inference manager, JSONL evaluation cases, Bubble Tea creation and benchmark views, Python conformance tests.

## Global Constraints

- Agent composition creates declarative packages, never automatically executed generated code.
- Every action has strict input and output schemas and an explicit capability list.
- Every active pack contains accepted, ambiguous, rejected, and unsafe evaluation cases.
- Hardware compatibility only creates candidates; task evaluation chooses the model.
- Failing candidates can run only in development simulation mode.
- The 8 GB profile defaults to one resident local model.

---

### Task 1: Load and validate agent-pack v1

**Files:**
- Create: `schemas/agent-pack/v1/agents.schema.json`
- Create: `schemas/agent-pack/v1/actions.schema.json`
- Create: `schemas/agent-pack/v1/policy.schema.json`
- Create: `schemas/agent-pack/v1/eval.schema.json`
- Create: `edge/internal/contracts/pack.go`
- Create: `edge/internal/pack/load.go`
- Create: `edge/internal/pack/validate.go`
- Create: `edge/internal/pack/pack_test.go`
- Create: `tests/contracts/test_agent_pack_fixtures.py`

**Interfaces:**
- Produces: `pack.Load(path string) (contracts.AgentPack, error)` and `pack.Validate(contracts.AgentPack) []pack.Violation`.

- [ ] **Step 1: Write malformed-pack and cross-runtime tests**

```go
func TestValidateRejectsCapabilityMissingFromPolicy(t *testing.T) {
    p := fixturePackWithActionCapability("fs.write")
    got := pack.Validate(p)
    assert.Contains(t, violationCodes(got), "undeclared_capability")
}
```

- [ ] **Step 2: Run tests and verify failure**

Run: `cd edge; go test ./internal/pack; cd ..; python -m pytest tests/contracts/test_agent_pack_fixtures.py -q`

Expected: FAIL.

- [ ] **Step 3: Implement strict loading and referential validation**

Reject archive traversal, symlinks, duplicate JSON keys, unknown major versions, duplicate
agent/action IDs, missing entry agent, broken handoff targets, actions not assigned to an
agent, capabilities absent from policy, empty eval categories, plaintext secret fields,
and checksum mismatches.

- [ ] **Step 4: Add deterministic canonical serialization**

Sort object keys, agents, actions, and checksums when exporting. Preserve eval case order.
Python tests validate the same fixture field names and version values.

- [ ] **Step 5: Run and commit**

Run: `cd edge; go test ./internal/pack; cd ..; python -m pytest tests/contracts -q`

```powershell
git add schemas/agent-pack edge/internal/contracts edge/internal/pack tests/contracts
git commit -m "feat: validate portable agent packs"
```

### Task 2: Define typed action descriptors and safe imports

**Files:**
- Create: `edge/internal/actions/descriptor.go`
- Create: `edge/internal/actions/registry.go`
- Create: `edge/internal/actions/import_script.go`
- Create: `edge/internal/actions/import_skill.go`
- Create: `edge/internal/actions/actions_test.go`
- Create: `docs/reference/action-descriptor.md`

**Interfaces:**
- Produces: `Registry.Register(ActionDescriptor) error`, `Registry.Match(name string) (ActionDescriptor, bool)`, and importers returning drafts without permissions.

- [ ] **Step 1: Write duplicate, shell, and Agent Skill import tests**

```go
func TestScriptImportRequiresExactExecutableAndArgumentTemplate(t *testing.T) {
    _, err := actions.ImportScript(map[string]any{"command": "powershell *"})
    assert.ErrorIs(t, err, actions.ErrUnboundedCommand)
}
```

- [ ] **Step 2: Run tests and verify failure**

Run: `cd edge; go test ./internal/actions`

Expected: FAIL.

- [ ] **Step 3: Implement action registry and draft importers**

Require lowercase stable IDs, descriptions, strict JSON input/output schemas, effect class,
timeout, output byte ceiling, and requested capabilities. Script imports accept one exact
executable path plus named argument placeholders. Agent Skill imports read metadata and
instructions as resources but create no executable action unless a separate descriptor is
present and valid.

- [ ] **Step 4: Document the descriptor with a complete example**

Use a read-only `search_files` action whose executable and root are explicit. State that
descriptors request capabilities while `policy.json` grants them.

- [ ] **Step 5: Run and commit**

Run: `cd edge; go test ./internal/actions; cd ..; python -m mkdocs build --strict`

```powershell
git add edge/internal/actions docs/reference/action-descriptor.md mkdocs.yml
git commit -m "feat: import typed action descriptors"
```

### Task 3: Build the guided pack compiler and creation UI

**Files:**
- Create: `edge/internal/compiler/draft.go`
- Create: `edge/internal/compiler/templates.go`
- Create: `edge/internal/compiler/compile.go`
- Create: `edge/internal/compiler/compiler_test.go`
- Create: `edge/internal/ui/create/model.go`
- Create: `edge/internal/ui/create/view.go`
- Create: `edge/internal/ui/create/create_test.go`
- Create: `edge/internal/cli/create.go`

**Interfaces:**
- Produces: `compiler.Compile(compiler.Draft) (contracts.AgentPack, []compiler.Question, error)`.
- Produces stages `goal`, `actions`, `examples`, `team`, `models`, `permissions`, `benchmark`, `activate`.

- [ ] **Step 1: Write minimum-team and unanswered-question tests**

```go
func TestActionRouterUsesOneLogicalAgentUntilSpecializationIsRequired(t *testing.T) {
    got, questions, err := compiler.Compile(simpleRouterDraft())
    require.NoError(t, err)
    assert.Empty(t, questions)
    assert.Len(t, got.Agents, 1)
}
```

- [ ] **Step 2: Run and verify failure**

Run: `cd edge; go test ./internal/compiler ./internal/ui/create`

Expected: FAIL.

- [ ] **Step 3: Implement curated composition rules**

Create one router agent by default. Add an extractor specialist only when an action declares
a distinct structured extraction requirement; add a web verifier only when `web.read` is
requested; add no model-backed safety agent because authorization is deterministic. Return
questions when the goal is unbounded, action schemas are missing, examples are too few, or
requested capabilities have no scope.

- [ ] **Step 4: Implement the eight-stage TUI flow and plain mode**

Each stage renders completed decisions, current input, validation errors, and next action.
`muru create --from draft.json --output pack-dir --plain` supports automation and fails
instead of prompting when required answers are absent.

- [ ] **Step 5: Run and commit**

Run: `cd edge; go test ./internal/compiler ./internal/ui/create ./internal/cli`

```powershell
git add edge/internal/compiler edge/internal/ui/create edge/internal/cli
git commit -m "feat: compile guided agent packs"
```

### Task 4: Implement evaluation metrics and activation gates

**Files:**
- Create: `edge/internal/eval/case.go`
- Create: `edge/internal/eval/runner.go`
- Create: `edge/internal/eval/metrics.go`
- Create: `edge/internal/eval/gates.go`
- Create: `edge/internal/eval/eval_test.go`
- Create: `edge/internal/cli/benchmark.go`
- Create: `edge/internal/ui/benchmark/model.go`

**Interfaces:**
- Produces: `Runner.Run(ctx, Pack, Candidate) Report` and `gates.Evaluate(Report, Thresholds) GateResult`.

- [ ] **Step 1: Write metric and fail-closed tests**

```go
func TestUnsafeExecutionFailsCandidateEvenWhenAccuracyPasses(t *testing.T) {
    report := fixtureReport(0.98, 1)
    result := gates.Evaluate(report, defaultThresholds())
    assert.False(t, result.Passed)
    assert.Contains(t, result.Failures, "unsafe_execution")
}
```

- [ ] **Step 2: Run and verify failure**

Run: `cd edge; go test ./internal/eval`

Expected: FAIL.

- [ ] **Step 3: Implement deterministic metrics**

Calculate action accuracy, argument exact match, field accuracy, schema validity, false
execution rate, abstention precision/recall, cold load, warm p50/p95, peak working set, and
failure counts. Store case-level results with expected and actual action IDs but redact
sensitive arguments.

- [ ] **Step 4: Implement mandatory gates and progress UI**

Default thresholds are 1.0 schema validity, 0.95 action accuracy, zero unsafe executions,
model artifact no more than 700 MB, and measured peak working set below 2 GB. The UI shows
completed/total cases and partial category metrics; cancellation leaves a non-activatable
partial report.

- [ ] **Step 5: Run and commit**

Run: `cd edge; go test ./internal/eval ./internal/ui/benchmark ./internal/cli`

```powershell
git add edge/internal/eval edge/internal/ui/benchmark edge/internal/cli
git commit -m "feat: evaluate edge agent candidates"
```

### Task 5: Select the smallest passing model team

**Files:**
- Create: `edge/internal/eval/selector.go`
- Create: `edge/internal/eval/selector_test.go`
- Modify: `edge/internal/ui/benchmark/model.go`
- Create: `edge/internal/cli/activate.go`

**Interfaces:**
- Produces: `selector.Select(reports []Report) (Selection, error)` using the design's lexicographic rule.

- [ ] **Step 1: Write selection-order tests**

```go
func TestSelectChoosesSmallestPassingArtifactBeforeLatency(t *testing.T) {
    slowSmall := passing("small", 350<<20, 2200*time.Millisecond)
    fastLarge := passing("large", 620<<20, 900*time.Millisecond)
    got, err := selector.Select([]eval.Report{fastLarge, slowSmall})
    require.NoError(t, err)
    assert.Equal(t, "small", got.CandidateID)
}
```

- [ ] **Step 2: Run and verify failure**

Run: `cd edge; go test ./internal/eval -run Select`

Expected: FAIL.

- [ ] **Step 3: Implement lexicographic selection and overrides**

Filter failing reports, sort by total artifact bytes then warm p95 latency then stable
candidate ID. Allow user override only among passing reports. Development-mode activation
of a failing candidate sets `effects: simulate` and cannot be changed without a new passing
report.

- [ ] **Step 4: Implement atomic activation**

Write the selected candidate ID, artifact digests, report digest, and activation timestamp
to a new manifest revision; validate and atomically replace the active pack directory.

- [ ] **Step 5: Run and commit**

Run: `cd edge; go test ./internal/eval ./internal/cli ./internal/ui/benchmark`

```powershell
git add edge/internal/eval edge/internal/cli edge/internal/ui/benchmark
git commit -m "feat: activate smallest passing model team"
```

### Task 6: Add typed routing and resource-aware scheduling

**Files:**
- Create: `edge/internal/contracts/task.go`
- Create: `edge/internal/orchestrator/graph.go`
- Create: `edge/internal/orchestrator/router.go`
- Create: `edge/internal/orchestrator/scheduler.go`
- Create: `edge/internal/orchestrator/orchestrator_test.go`

**Interfaces:**
- Produces: `contracts.TaskEnvelope`, `Router.Next(contracts.AgentPack, contracts.TaskEnvelope) orchestrator.Route`, and `Scheduler.Lease(ctx, contracts.AgentSpec) (inference.Lease, error)`.

- [ ] **Step 1: Write deterministic, shared-model, and sequential-model tests**

```go
func TestDeterministicEdgeDoesNotCallRoutingModel(t *testing.T) {
    router := fixtureRouterWithFailingModel()
    got, err := router.Next(packWithExactEdge("extract"), envelope("extract"))
    require.NoError(t, err)
    assert.Equal(t, "extractor", got.AgentID)
}
```

- [ ] **Step 2: Run and verify failure**

Run: `cd edge; go test ./internal/orchestrator`

Expected: FAIL.

- [ ] **Step 3: Implement typed envelopes and deterministic-first routing**

Validate source, destination, input schema, capability subset, deadline, hop count, and
trace parent. Resolve exact graph edges and action ownership before invoking a routing
model. Reject cycles beyond the pack's hop limit and emit a typed abstention.

- [ ] **Step 4: Implement scheduler integration**

Agents with the same resolved model ID reuse the current lease. Different specialists
release the prior lease before acquisition when `MaxResidentModels` is one. Record queue,
load, inference, and unload durations separately.

- [ ] **Step 5: Run and commit**

Run: `cd edge; go test ./internal/orchestrator ./internal/inference`

```powershell
git add edge/internal/contracts edge/internal/orchestrator
git commit -m "feat: route resource-aware agent teams"
```

### Task 7: Execute packs in simulation and explain runs

**Files:**
- Create: `edge/internal/orchestrator/engine.go`
- Create: `edge/internal/orchestrator/engine_test.go`
- Create: `edge/internal/cli/run.go`
- Create: `edge/internal/cli/explain.go`
- Modify: `edge/internal/ui/panes/agentmap.go`
- Modify: `edge/internal/ui/panes/runstream.go`
- Modify: `edge/internal/ui/panes/inspector.go`

**Interfaces:**
- Produces: `Engine.Submit(ctx, packID, input) (RunID, error)` and deterministic `Explain(runID) Explanation`.

- [ ] **Step 1: Write run and explanation tests**

```go
func TestExplainUsesRecordedDecisionsWithoutModelCall(t *testing.T) {
    engine := fixtureEngineWithFailingExplanationModel()
    runID := runSimulated(t, engine, "find invoices")
    got, err := engine.Explain(runID)
    require.NoError(t, err)
    assert.Equal(t, []string{"router", "search_files"}, got.Path)
}
```

- [ ] **Step 2: Run and verify failure**

Run: `cd edge; go test ./internal/orchestrator ./internal/cli -run 'Run|Explain'`

Expected: FAIL.

- [ ] **Step 3: Implement simulated execution**

Persist input receipt, route decisions, model leases, agent starts/completions, proposed
actions, schema validation, abstentions, and terminal state. In simulation mode, return
the validated proposed action without invoking it. `Explain` folds these events into a
stable account with path, model IDs, reasons, timings, and denied capabilities.

- [ ] **Step 4: Project live state into the workspace**

Agent map highlights the active node and completed edges. Run stream groups model and route
events beneath the user request. Inspector exposes the exact evaluation report and route
reason without showing raw prompts or sensitive arguments.

- [ ] **Step 5: Run and commit**

Run: `cd edge; go test ./internal/orchestrator ./internal/cli ./internal/ui`

```powershell
git add edge/internal/orchestrator edge/internal/cli edge/internal/ui
git commit -m "feat: simulate and explain agent packs"
```

### Task 8: Create and qualify the flagship action-router pack

**Files:**
- Create: `packs/action-router/manifest.json`
- Create: `packs/action-router/agents.json`
- Create: `packs/action-router/actions.json`
- Create: `packs/action-router/policy.json`
- Create: `packs/action-router/evals.jsonl`
- Create: `packs/action-router/prompts/router.txt`
- Create: `packs/action-router/checksums.txt`
- Create: `qualification/edge/action_router_simulation.ps1`
- Create: `docs/getting-started/action-router.md`

**Interfaces:**
- Produces: a model-independent sample pack with `search_files`, `classify_document`, and `summarize_text` simulated actions.

- [ ] **Step 1: Write the qualification assertion**

The script must compile or load the pack, validate all files, execute every eval in
simulation, assert zero unsafe effects, produce an evaluation table, choose a passing
fixture candidate, and replay explanations after process restart.

- [ ] **Step 2: Run and verify failure**

Run: `powershell -ExecutionPolicy Bypass -File qualification/edge/action_router_simulation.ps1`

Expected: FAIL because the pack is absent.

- [ ] **Step 3: Add complete pack and user guide**

Include at least 20 accepted, 5 ambiguous, 5 rejected, and 10 unsafe cases. The guide walks
through create, benchmark, activate, run, and explain, and labels all actions as simulated
until the security tranche lands.

- [ ] **Step 4: Run Gate C suite**

Run: `cd edge; go test ./...; cd ..; powershell -ExecutionPolicy Bypass -File qualification/edge/action_router_simulation.ps1; python -m pytest -q; python -m mkdocs build --strict`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add packs/action-router qualification/edge docs/getting-started/action-router.md mkdocs.yml
git commit -m "feat: qualify adaptive action router"
```
