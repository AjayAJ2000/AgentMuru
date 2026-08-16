# AgentMuru Secure Effects and Feedback Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute approved local actions through complete capability mediation, add sandboxed WASI tools and optional read-only web evidence, qualify the named low-end Windows target, and publish a signed feedback release with the terminal workspace as its primary experience.

**Architecture:** Put authorization, approvals, execution adapters, WASI, MCP import, and web retrieval behind separate interfaces. The orchestrator can request effects but only the capability broker can authorize them. Security and resource qualification run from clean release artifacts before documentation or package publication.

**Tech Stack:** Go standard library, wazero, Windows Job Objects, restricted subprocess environments, HTTP/DNS validation, existing event/TUI/runtime contracts, GitHub Actions, WinGet.

## Global Constraints

- Every effect is authorized immediately before execution; prior model or routing decisions are not authorization.
- Filesystem read and write, process execution, web read, MCP connection, secret use, and cloud inference are distinct capabilities.
- `offline` is the default network mode; first release web access is read-only.
- Web evidence is untrusted data and cannot modify policy or directly invoke actions.
- Docker is optional and never required for the 8 GB target.
- Sensitive arguments, credentials, raw exceptions, and unbounded web content are never persisted.

---

### Task 1: Implement the capability broker

**Files:**
- Create: `edge/internal/policy/capability.go`
- Create: `edge/internal/policy/policy.go`
- Create: `edge/internal/policy/broker.go`
- Create: `edge/internal/policy/broker_test.go`
- Create: `edge/internal/contracts/policy.go`

**Interfaces:**
- Produces: `Broker.Decide(ctx, Principal, Effect) Decision` with `allow`, `deny`, or `require_approval`.

- [ ] **Step 1: Write complete-mediation tests**

```go
func TestModelMetadataCannotGrantFilesystemWrite(t *testing.T) {
    broker := policy.NewBroker(readOnlyPolicy())
    effect := fixtureEffect("fs.write", map[string]any{"model_granted": true})
    assert.Equal(t, policy.Deny, broker.Decide(context.Background(), agent(), effect).Kind)
}
```

- [ ] **Step 2: Run and verify failure**

Run: `cd edge; go test ./internal/policy`

Expected: FAIL.

- [ ] **Step 3: Implement exact-scope decisions**

Normalize paths before comparison, reject traversal and device paths, compare executable
identity separately from arguments, require HTTPS except loopback development fixtures,
and treat unknown capabilities as denied. Decisions include stable reason codes and a
sanitized summary for the TUI.

- [ ] **Step 4: Integrate with the orchestrator**

Every proposed action becomes an `Effect`; the engine calls the broker immediately before
the adapter. Emit requested, allowed, denied, and approval-required events. Add a test
adapter that fails if invoked after denial.

- [ ] **Step 5: Run and commit**

Run: `cd edge; go test ./internal/policy ./internal/orchestrator`

```powershell
git add edge/internal/policy edge/internal/contracts edge/internal/orchestrator
git commit -m "feat: mediate every agent effect"
```

### Task 2: Add durable approvals and terminal approval overlays

**Files:**
- Create: `edge/internal/approval/service.go`
- Create: `edge/internal/approval/store.go`
- Create: `edge/internal/approval/approval_test.go`
- Create: `edge/internal/ui/overlay/approval.go`
- Create: `edge/internal/ui/overlay/approval_test.go`
- Create: `edge/internal/cli/approve.go`

**Interfaces:**
- Produces: `Service.Request(ctx, Effect, PolicyDecision) (Request, error)` and `Service.Decide(id, actor, outcome, persistence) error`.

- [ ] **Step 1: Write expiry, replay, and scope tests**

```go
func TestApprovalForOnePathDoesNotAuthorizeSiblingPath(t *testing.T) {
    service := fixtureApprovalService()
    approveOnce(t, service, writeEffect(`C:\Invoices\a.csv`))
    assert.False(t, service.IsApproved(writeEffect(`C:\Invoices\b.csv`)))
}
```

- [ ] **Step 2: Run and verify failure**

Run: `cd edge; go test ./internal/approval ./internal/ui/overlay -run Approval`

Expected: FAIL.

- [ ] **Step 3: Implement append-only approval state**

Persist request, exact sanitized effect fingerprint, expiry, actor, decision, reason, and
persistence scope (`once`, `session`, or `pack-policy-draft`). A persistent choice creates
a reviewable policy draft; it never edits an active policy during a run.

- [ ] **Step 4: Implement the approval overlay**

Show agent, action, effect, exact path/domain/executable, redacted arguments, risk, expiry,
and keys for deny/once/session/draft. Default focus is deny. Plain mode prints the request
and accepts a separate `muru approve` command rather than reading an ambiguous stdin line.

- [ ] **Step 5: Run and commit**

Run: `cd edge; go test ./internal/approval ./internal/ui/overlay ./internal/cli`

```powershell
git add edge/internal/approval edge/internal/ui/overlay edge/internal/cli
git commit -m "feat: govern effects with durable approvals"
```

### Task 3: Execute built-in, native, and WASI tools safely

**Files:**
- Create: `edge/internal/tools/executor.go`
- Create: `edge/internal/tools/builtin.go`
- Create: `edge/internal/tools/process_windows.go`
- Create: `edge/internal/tools/process_other.go`
- Create: `edge/internal/tools/executor_test.go`
- Create: `edge/internal/sandbox/wasi.go`
- Create: `edge/internal/sandbox/wasi_test.go`

**Interfaces:**
- Produces: `tools.Executor.Invoke(ctx, ActionDescriptor, arguments) (Result, error)`.
- Produces: `sandbox.Run(ctx, Module, Capabilities, input) (output, error)`.

- [ ] **Step 1: Write timeout, output, environment, and preopen tests**

```go
func TestWASIModuleCannotReadUnopenedDirectory(t *testing.T) {
    _, err := sandbox.Run(ctx, fixtureReaderModule(), capsWithRoot(tempAllowed), inputFor(tempDenied))
    assert.ErrorIs(t, err, sandbox.ErrCapabilityDenied)
}
```

- [ ] **Step 2: Run and verify failure**

Run: `cd edge; go test ./internal/tools ./internal/sandbox`

Expected: FAIL.

- [ ] **Step 3: Implement bounded adapters**

Built-ins receive typed arguments only. Native processes use an exact executable, argument
template expansion without shell parsing, restricted working directory, environment
allowlist, Windows Job Object, deadline, stdout/stderr byte ceilings, and ANSI sanitization.
WASI modules receive only declared preopened directories, stdin bytes, and bounded output;
network remains disabled in the first release.

- [ ] **Step 4: Integrate execution results and redaction**

Validate adapter output against the action output schema before persistence. Store digest,
duration, exit category, and redacted result. Never store inherited environment values or
raw stderr.

- [ ] **Step 5: Run and commit**

Run: `cd edge; go test ./internal/tools ./internal/sandbox ./internal/orchestrator`

```powershell
git add edge/internal/tools edge/internal/sandbox edge/internal/orchestrator
git commit -m "feat: execute capability-scoped tools"
```

### Task 4: Import MCP tools without implicit trust

**Files:**
- Create: `edge/internal/tools/mcp/import.go`
- Create: `edge/internal/tools/mcp/client.go`
- Create: `edge/internal/tools/mcp/mcp_test.go`
- Create: `docs/guides/mcp-import.md`

**Interfaces:**
- Produces: `mcp.Import(ServerDescriptor) ([]ActionDraft, ConsentSummary, error)`.

- [ ] **Step 1: Write consent and command-display tests**

```go
func TestImportDisplaysCompleteStartupCommandAndGrantsNothing(t *testing.T) {
    drafts, consent, err := mcp.Import(fixtureServer())
    require.NoError(t, err)
    assert.Equal(t, fixtureServer().Command, consent.ExactCommand)
    assert.Empty(t, drafts[0].GrantedCapabilities)
}
```

- [ ] **Step 2: Run and verify failure**

Run: `cd edge; go test ./internal/tools/mcp`

Expected: FAIL.

- [ ] **Step 3: Implement stdio-only first-release import**

Display the exact executable and arguments, reject shell command strings, enumerate tool
schemas, prefix IDs with the server ID, and produce action drafts. Start the server only
after explicit consent and run it through the native process adapter. HTTP MCP is excluded
from the first release.

- [ ] **Step 4: Document permission separation**

The guide demonstrates import, review, policy grant, simulation, and activation. State that
MCP annotations are untrusted and that one-click configuration still requires consent.

- [ ] **Step 5: Run and commit**

Run: `cd edge; go test ./internal/tools/mcp; cd ..; python -m mkdocs build --strict`

```powershell
git add edge/internal/tools/mcp docs/guides/mcp-import.md mkdocs.yml
git commit -m "feat: import MCP tools with explicit consent"
```

### Task 5: Add read-only web retrieval and evidence records

**Files:**
- Create: `edge/internal/contracts/evidence.go`
- Create: `edge/internal/web/request.go`
- Create: `edge/internal/web/broker.go`
- Create: `edge/internal/web/extract.go`
- Create: `edge/internal/web/web_test.go`
- Create: `edge/internal/ui/panes/evidence.go`
- Create: `edge/internal/cli/web.go`

**Interfaces:**
- Produces: `web.Broker.Fetch(ctx, principal, RetrievalRequest) (Evidence, error)`.

- [ ] **Step 1: Write SSRF, redirect, size, and injection-label tests**

```go
func TestBrokerRejectsRedirectToPrivateAddress(t *testing.T) {
    broker := fixtureBrokerRedirectingTo("http://127.0.0.1/secret")
    _, err := broker.Fetch(ctx, agent(), httpsRequest("https://example.test"))
    assert.ErrorIs(t, err, web.ErrPrivateAddress)
}
```

- [ ] **Step 2: Run and verify failure**

Run: `cd edge; go test ./internal/web`

Expected: FAIL.

- [ ] **Step 3: Implement policy-bound retrieval**

Support `offline`, `ask`, `allowlist`, and `research`. Accept HTTPS only, resolve and reject
loopback/private/link-local addresses, repeat checks after every redirect, cap redirects,
time, compressed and decompressed bytes, and content types. Strip scripts/styles/forms,
extract bounded plain text, and record URL, retrieval time, content digest, title, and
excerpt. Do not execute JavaScript or retain cookies.

- [ ] **Step 4: Mark and render evidence as untrusted**

Wrap agent-visible evidence in a typed data boundary, never concatenate it into trusted
instructions, and require downstream action validation and authorization. The evidence
pane shows source, time, domain permission, digest prefix, and an `UNTRUSTED WEB DATA`
label.

- [ ] **Step 5: Run and commit**

Run: `cd edge; go test ./internal/web ./internal/policy ./internal/ui`

```powershell
git add edge/internal/contracts edge/internal/web edge/internal/ui edge/internal/cli
git commit -m "feat: add controlled web evidence"
```

### Task 6: Add adversarial security qualification

**Files:**
- Create: `qualification/edge/security_cases.jsonl`
- Create: `qualification/edge/run_security.ps1`
- Create: `qualification/edge/fixtures/malicious_page.html`
- Create: `qualification/edge/fixtures/ansi_tool.ps1`
- Create: `qualification/edge/fixtures/oversize_server.ps1`
- Modify: `SECURITY.md`
- Create: `docs/guides/edge-security.md`

**Interfaces:**
- Produces: a machine-readable report with case ID, threat category, expected decision, actual decision, effect count, and pass/fail.

- [ ] **Step 1: Add required adversarial cases**

Cover direct and indirect prompt injection, private-IP redirect, DNS rebinding simulation,
path traversal, Windows device paths, wildcard executables, argument injection, environment
secret access, oversized output, timeout, malicious ANSI/OSC, catalog mutation, pack
checksum mutation, approval replay, and unauthorized peer-agent handoff.

- [ ] **Step 2: Run the suite and verify failures before integration is complete**

Run: `powershell -ExecutionPolicy Bypass -File qualification/edge/run_security.ps1`

Expected: non-zero until every expected denial and sanitization is implemented.

- [ ] **Step 3: Connect cases to public threat-model documentation**

For each capability state assets, trust boundary, attacker, prevention, residual risk,
logged evidence, and recovery. Explicitly state that prompt injection cannot be eliminated
and that permissions limit impact.

- [ ] **Step 4: Run security and regression suites**

Run: `powershell -ExecutionPolicy Bypass -File qualification/edge/run_security.ps1; cd edge; go test ./...; cd ..; python -m pytest -q; python -m mkdocs build --strict`

Expected: PASS with zero effects for every denied case.

- [ ] **Step 5: Commit**

```powershell
git add qualification/edge SECURITY.md docs/guides/edge-security.md mkdocs.yml
git commit -m "test: qualify edge agent security"
```

### Task 7: Qualify the named low-end reference machine

**Files:**
- Create: `qualification/edge/reference_device.ps1`
- Create: `qualification/edge/reference-report.schema.json`
- Create: `qualification/edge/reports/README.md`
- Modify: `docs/qualification.md`

**Interfaces:**
- Produces: signed/redacted report fields for hardware, OS, runtime/model hashes, context, case metrics, load time, warm p50/p95, peak working set, and safety totals.

- [ ] **Step 1: Implement fail-closed measurement script**

The script starts from an unpacked release candidate, runs doctor, validates the flagship
pack, installs its selected model, runs all evals three times after one cold run, samples
the process tree working set, runs security cases, restarts, replays the last session, and
validates the report schema. It exits non-zero for any missing measurement or failed gate.

- [ ] **Step 2: Run on a development machine to validate report plumbing**

Run: `powershell -ExecutionPolicy Bypass -File qualification/edge/reference_device.ps1 -Mode Development`

Expected: a schema-valid report labeled `development`, never `reference-qualified`.

- [ ] **Step 3: Select and record the physical reference machine**

Record manufacturer/model, CPU, instruction flags, installed RAM, storage, Windows edition
and build, power mode, and terminal. Run the script without `-Mode Development`. Commit the
redacted report only when all gates pass; otherwise document the exact failed gate and do
not advertise support.

- [ ] **Step 4: Update qualification documentation from the report**

Generate tables from report JSON rather than copying measurements manually. Link the
runtime, catalog, model, pack, and source commit digests.

- [ ] **Step 5: Commit**

```powershell
git add qualification/edge docs/qualification.md
git commit -m "test: record low-end edge qualification"
```

### Task 8: Package, document, and publish the feedback release

**Files:**
- Create: `.github/workflows/edge-release.yml`
- Create: `packaging/winget/AgentMuru.Muru.yaml`
- Create: `packaging/winget/AgentMuru.Muru.installer.yaml`
- Create: `packaging/winget/AgentMuru.Muru.locale.en-US.yaml`
- Modify: `README.md`
- Modify: `docs/index.md`
- Modify: `docs/getting-started/installation.md`
- Modify: `docs/product/roadmap.md`
- Modify: `docs/CHANGELOG.md`
- Modify: `docs/architecture/target-state.md`
- Modify: `docs/architecture/ai-native-transformation.md`

**Interfaces:**
- Produces: signed Windows x64 archive, SHA-256 checksum file, SBOM, GitHub release, and WinGet submission artifacts.

- [ ] **Step 1: Write release-surface documentation tests**

Assert that installation leads with `winget install AgentMuru.Muru`, the PyPI SDK is labeled
as the Python authoring/server surface, read-only web is opt-in, cloud inference is not
listed as shipped, Android is future work, and low-end claims link to a passing report.

- [ ] **Step 2: Run and verify failure**

Run: `python -m pytest tests/test_documentation_contract.py tests/test_packaging.py -q`

Expected: FAIL until release metadata and documentation are updated.

- [ ] **Step 3: Implement gated release workflow**

Build from a pinned Go toolchain, run Python/Go/frontend/docs suites, run clean native
qualification, generate SBOM and checksums, sign artifacts, and create the GitHub release.
Fail before publication if the reference report is absent or its source/catalog/runtime
digests do not match the release inputs. Generate WinGet manifests from the final asset URL
and checksum; submission remains a separate reviewed job.

- [ ] **Step 4: Update customer-facing documentation and feedback command**

Lead with install, `muru`, create, benchmark, permissions, run, and explain. Add
`muru feedback export` that previews and writes a local redacted archive; it never sends
data. Document model licenses, cache removal, offline mode, resource limits, and how to
report unsupported hardware.

- [ ] **Step 5: Run Gate D verification**

Run: `python -m pytest -q; python -m ruff check agentmuru tests; python -m mypy agentmuru; cd edge; go test ./...; go vet ./...; go build ./cmd/muru; cd ../frontend; npm test -- --run; npm run lint; npm run typecheck; npm run build; npm run check:bundle; cd ..; python -m mkdocs build --strict; python -m build`

Expected: every command exits zero and the release workflow dry run produces unsigned
local artifacts without publishing.

- [ ] **Step 6: Commit**

```powershell
git add .github/workflows/edge-release.yml packaging README.md docs tests/test_documentation_contract.py tests/test_packaging.py edge
git commit -m "release: prepare adaptive edge feedback build"
```
