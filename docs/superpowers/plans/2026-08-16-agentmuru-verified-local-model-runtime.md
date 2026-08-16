# AgentMuru Verified Local Model Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the native `muru` binary verify a signed catalog, download compatible GGUF artifacts atomically, supervise a pinned llama.cpp server, and return constrained action decisions with visible model lifecycle events.

**Architecture:** Keep catalog trust, downloads, runtime selection, process supervision, and inference normalization in separate packages. Run llama.cpp as a loopback-only authenticated child process. Use fake HTTP servers and fixture executables for deterministic tests; credentialed or large-model checks remain explicit qualification jobs.

**Tech Stack:** Go standard-library Ed25519, SHA-256, HTTP and `os/exec`; pinned llama.cpp release; JSON Schema-constrained responses; existing Bubble Tea workspace.

## Global Constraints

- Only signed catalog entries with immutable revisions, declared byte sizes, and SHA-256 digests may install.
- Pickle formats are rejected; the initial model format is GGUF.
- Gated licenses require an explicit recorded acceptance and are never bypassed.
- Inference binds to loopback with an ephemeral token and terminates with AgentMuru.
- Hardware compatibility filters candidates before any runtime binary executes.
- Model files for the flagship pack remain at or below 700 MB.

---

### Task 1: Implement signed catalog loading

**Files:**
- Create: `schemas/catalog/v1/catalog.schema.json`
- Create: `edge/internal/contracts/catalog.go`
- Create: `edge/internal/catalog/verify.go`
- Create: `edge/internal/catalog/verify_test.go`
- Create: `edge/internal/catalog/testdata/catalog.json`
- Create: `edge/internal/catalog/testdata/catalog.sig`
- Create: `catalog/bootstrap-v1.json`

**Interfaces:**
- Produces: `catalog.Verify(data, signature []byte, publicKey ed25519.PublicKey) (contracts.Catalog, error)`
- Produces: `contracts.Catalog.Compatible(profile contracts.HardwareProfile) []contracts.Artifact`.

- [ ] **Step 1: Write signature, mutation, and compatibility tests**

```go
func TestVerifyRejectsMutatedCatalog(t *testing.T) {
    data, sig, key := fixtureCatalog(t)
    data[len(data)-2] ^= 1
    _, err := catalog.Verify(data, sig, key)
    assert.ErrorIs(t, err, catalog.ErrInvalidSignature)
}
```

- [ ] **Step 2: Run and confirm failure**

Run: `cd edge; go test ./internal/catalog`

Expected: FAIL because verification is undefined.

- [ ] **Step 3: Implement canonical signed bytes and semantic validation**

Verify the signature over the exact catalog bytes before decoding. Reject duplicate IDs,
non-HTTPS upstream URLs, non-GGUF artifacts, invalid digests, size above the catalog
ceiling, unknown runtime variants, and gated entries without a license URL.

- [ ] **Step 4: Run tests**

Run: `cd edge; go test ./internal/catalog`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add schemas/catalog edge/internal/contracts edge/internal/catalog catalog
git commit -m "feat: verify signed model catalog"
```

### Task 2: Add verified atomic downloads and cache inventory

**Files:**
- Create: `edge/internal/download/fetch.go`
- Create: `edge/internal/download/fetch_test.go`
- Create: `edge/internal/catalog/cache.go`
- Create: `edge/internal/catalog/cache_test.go`
- Create: `edge/internal/cli/models.go`

**Interfaces:**
- Produces: `download.Fetch(ctx, client, Artifact, destination, progress) error`
- Produces: `Cache.Inventory() ([]InstalledArtifact, error)` and `Cache.Remove(id string) error`.

- [ ] **Step 1: Write size, checksum, cancellation, and promotion tests**

```go
func TestFetchNeverPromotesWrongDigest(t *testing.T) {
    artifact := fixtureArtifactWithDigest(strings.Repeat("0", 64))
    err := download.Fetch(context.Background(), fixtureClient("model"), artifact, target, nil)
    assert.ErrorIs(t, err, download.ErrDigestMismatch)
    assert.NoFileExists(t, target)
}
```

- [ ] **Step 2: Run and confirm failure**

Run: `cd edge; go test ./internal/download ./internal/catalog -run 'Fetch|Cache'`

Expected: FAIL.

- [ ] **Step 3: Implement streaming download**

Write to `<digest>.partial`, reject responses without success status, stop after declared
size plus one byte, hash while streaming, sync, then atomically rename to the digest path.
On cancellation remove the partial file. The progress callback receives downloaded and
declared bytes but cannot affect validation.

- [ ] **Step 4: Add `muru models list|install|remove`**

`install` shows license metadata before download and requires `--accept-license <id>` for
gated artifacts. JSON mode never prompts and fails with a stable `license_required` code.

- [ ] **Step 5: Run tests and commit**

Run: `cd edge; go test ./internal/download ./internal/catalog ./internal/cli`

```powershell
git add edge/internal/download edge/internal/catalog edge/internal/cli
git commit -m "feat: install verified model artifacts"
```

### Task 3: Select and package compatible llama.cpp variants

**Files:**
- Create: `edge/internal/inference/variant.go`
- Create: `edge/internal/inference/variant_test.go`
- Create: `tools/build-llama-windows.ps1`
- Create: `qualification/edge/verify_runtime_variant.ps1`
- Modify: `.github/workflows/edge-ci.yml`

**Interfaces:**
- Produces: `inference.SelectVariant(profile contracts.HardwareProfile, available []contracts.RuntimeVariant) (contracts.RuntimeVariant, error)`.

- [ ] **Step 1: Write selection tests**

```go
func TestSelectVariantNeverChoosesAVX2ForAVXCPU(t *testing.T) {
    got, err := inference.SelectVariant(avxOnlyProfile(), fixtureVariants())
    require.NoError(t, err)
    assert.Equal(t, "windows-x64-avx", got.ID)
}
```

- [ ] **Step 2: Run and confirm failure**

Run: `cd edge; go test ./internal/inference -run Variant`

Expected: FAIL.

- [ ] **Step 3: Implement feature-subset selection**

Treat required CPU flags as a set and choose the highest-ranked variant whose requirements
are a subset of the profile. Never probe compatibility by executing an unknown binary.

- [ ] **Step 4: Add reproducible Windows build script**

Pin a llama.cpp commit in the script. Build baseline with `GGML_NATIVE=OFF` and unsupported
instruction options disabled, plus AVX and AVX2 variants with explicit CMake flags. Emit a
manifest containing commit, flags, filenames, sizes, and SHA-256 digests. CI uploads
artifacts but does not add them to the public catalog automatically.

- [ ] **Step 5: Verify and commit**

Run: `cd edge; go test ./internal/inference`

```powershell
git add edge/internal/inference tools/build-llama-windows.ps1 qualification/edge .github/workflows/edge-ci.yml
git commit -m "build: produce compatible llama runtimes"
```

### Task 4: Supervise the local inference process

**Files:**
- Create: `edge/internal/inference/supervisor.go`
- Create: `edge/internal/inference/supervisor_test.go`
- Create: `edge/internal/inference/health.go`
- Create: `edge/internal/inference/testdata/fake-server.ps1`

**Interfaces:**
- Produces: `Supervisor.Start(ctx, RuntimeConfig) (Endpoint, error)`, `Supervisor.Stop(ctx) error`, and `Supervisor.Status() Status`.

- [ ] **Step 1: Write lifecycle tests with a fixture child process**

```go
func TestSupervisorUsesLoopbackAndEphemeralToken(t *testing.T) {
    endpoint := startFixture(t)
    assert.Equal(t, "127.0.0.1", endpoint.URL.Hostname())
    assert.NotEmpty(t, endpoint.Token)
    assert.NotContains(t, endpoint.CommandLine, endpoint.Token)
}
```

- [ ] **Step 2: Run and confirm failure**

Run: `cd edge; go test ./internal/inference -run Supervisor`

Expected: FAIL.

- [ ] **Step 3: Implement safe process startup and shutdown**

Reserve a loopback port, generate a 32-byte random bearer token, pass secrets through a
restricted environment variable, wait for authenticated health, enforce a startup
deadline, sanitize captured output, and place the Windows child in a Job Object so it dies
with the parent. Stop gracefully, then terminate after the configured deadline.

- [ ] **Step 4: Emit lifecycle events and test cancellation**

Emit `model.load.started`, `model.loaded`, `model.unload.started`, `model.unloaded`, and
`model.process.failed` through the native event bus. Tests assert the persisted order.

- [ ] **Step 5: Run and commit**

Run: `cd edge; go test ./internal/inference ./internal/events`

```powershell
git add edge/internal/inference
git commit -m "feat: supervise local llama runtime"
```

### Task 5: Normalize constrained action inference

**Files:**
- Create: `edge/internal/inference/client.go`
- Create: `edge/internal/inference/client_test.go`
- Create: `edge/internal/contracts/action.go`
- Create: `edge/internal/inference/grammar.go`
- Create: `edge/internal/inference/grammar_test.go`

**Interfaces:**
- Produces: `Client.Decide(ctx, DecisionRequest) (ActionDecision, Usage, error)`.
- Produces: `GrammarFor(actions []ActionDescriptor) (string, error)`.

- [ ] **Step 1: Write response and grammar tests**

```go
func TestDecideRejectsUnknownAction(t *testing.T) {
    client := fixtureClientReturning(`{"action":"delete_all","arguments":{}}`)
    _, _, err := client.Decide(context.Background(), requestWithAction("search_files"))
    assert.ErrorIs(t, err, inference.ErrUnknownAction)
}
```

- [ ] **Step 2: Run and confirm failure**

Run: `cd edge; go test ./internal/inference -run 'Decide|Grammar'`

Expected: FAIL.

- [ ] **Step 3: Implement strict request and response normalization**

Send bounded messages, temperature zero, max output tokens, and the generated grammar.
Accept exactly one JSON object with `action`, `arguments`, and optional `abstain_reason`.
Validate action name and argument shape after decoding even when the backend reports
grammar support. Do not parse Markdown fences or repair malformed JSON.

- [ ] **Step 4: Emit safe inference events**

Persist model ID, artifact digest, timing, token counts, and decision status. Do not persist
the bearer token, full prompt, raw server error, or unredacted arguments.

- [ ] **Step 5: Run and commit**

Run: `cd edge; go test ./internal/inference`

```powershell
git add edge/internal/contracts edge/internal/inference
git commit -m "feat: constrain local action decisions"
```

### Task 6: Add memory-aware model management and TUI lifecycle views

**Files:**
- Create: `edge/internal/inference/manager.go`
- Create: `edge/internal/inference/manager_test.go`
- Create: `edge/internal/ui/panes/models.go`
- Modify: `edge/internal/ui/panes/resources.go`
- Modify: `edge/internal/ui/overlay/palette.go`
- Test: `edge/internal/ui/workspace_test.go`

**Interfaces:**
- Produces: `Manager.Acquire(ctx, ModelID, Budget) (Lease, error)` and `Lease.Release()`.

- [ ] **Step 1: Write residency tests**

```go
func TestLowMemoryBudgetUnloadsBeforeLoadingSpecialist(t *testing.T) {
    manager := fixtureManager(Budget{MaxResidentModels: 1})
    first := acquire(t, manager, "router")
    first.Release()
    acquire(t, manager, "extractor")
    assert.Equal(t, []string{"load:router", "unload:router", "load:extractor"}, manager.Log())
}
```

- [ ] **Step 2: Run and confirm failure**

Run: `cd edge; go test ./internal/inference ./internal/ui -run 'Resident|Model'`

Expected: FAIL.

- [ ] **Step 3: Implement leases and budget checks**

Allow one active lease per loaded model, reject an acquisition whose estimated load memory
exceeds the budget, evict least-recently-used idle models before loading, and never evict a
leased model. Default the 8 GB profile to one resident model.

- [ ] **Step 4: Add model pane and resource dock state**

Show installed, loading, loaded, sleeping, incompatible, and gated states. Display model
digest prefix, measured or estimated RAM, and why a model cannot run. Palette actions call
the same services as non-interactive commands.

- [ ] **Step 5: Run and commit**

Run: `cd edge; go test ./internal/inference ./internal/ui`

```powershell
git add edge/internal/inference edge/internal/ui
git commit -m "feat: manage edge model residency"
```

### Task 7: Complete Gate B qualification

**Files:**
- Create: `qualification/edge/model_runtime_smoke.ps1`
- Create: `qualification/edge/catalog_tamper.ps1`
- Create: `qualification/edge/report_schema.json`
- Create: `docs/guides/local-model-runtime.md`
- Modify: `docs/integration-status.md`
- Modify: `mkdocs.yml`

**Interfaces:**
- Produces: a redacted JSON qualification report with hardware, runtime, artifact digest, load time, decision latency, and peak working set.

- [ ] **Step 1: Add documentation assertions**

Require the integration status to distinguish fixture-qualified, clean-machine-qualified,
and reference-device-qualified behavior. It must not call a catalog model supported until
the corresponding report exists.

- [ ] **Step 2: Run the assertion and verify failure**

Run: `python -m pytest tests/test_documentation_contract.py -q`

Expected: FAIL until the status language is added.

- [ ] **Step 3: Add clean-machine and tamper qualification scripts**

The smoke script installs the native archive into a temporary directory, serves a small
test GGUF from a local fixture endpoint, verifies it, starts the pinned runtime, performs a
constrained decision, stops it, and records resource data. The tamper script mutates
catalog bytes and model bytes separately and asserts both are rejected before execution.

- [ ] **Step 4: Run Gate B verification**

Run: `cd edge; go test ./...; go vet ./...; go build ./cmd/muru; cd ..; powershell -ExecutionPolicy Bypass -File qualification/edge/catalog_tamper.ps1; python -m pytest -q; python -m mkdocs build --strict`

Expected: PASS. The large-model clean-machine script runs only when its fixture artifact is
explicitly supplied.

- [ ] **Step 5: Commit**

```powershell
git add qualification/edge docs mkdocs.yml tests/test_documentation_contract.py
git commit -m "test: qualify verified local inference"
```
