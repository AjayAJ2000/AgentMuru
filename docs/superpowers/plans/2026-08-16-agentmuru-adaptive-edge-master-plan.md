# AgentMuru Adaptive Edge Agents Master Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a Windows-first `muru` product that profiles constrained hardware, presents a TUIOS-inspired terminal workspace, installs verified local models, compiles bounded multi-agent packages, selects the smallest passing model team, and executes approved actions with optional read-only web evidence.

**Architecture:** Add a native Go edge runtime under `edge/` while retaining the Python package as the SDK and browser/server compatibility layer. Both runtimes consume versioned JSON contracts and golden fixtures. Execute the four tranche plans in order; each ends in working, independently testable software and a go/no-go gate.

**Tech Stack:** Go 1.25.9, Bubble Tea v2, Lipgloss v2, Cobra, standard-library Ed25519/SHA-256/HTTP/JSON, llama.cpp server, wazero for WASI tools, existing Python 3.10+ SDK, pytest, GitHub Actions, WinGet.

## Global Constraints

- The primary target is Windows 10/11 x64, CPU-only, 8 GB total RAM, with a named Pentium-class reference machine before compatibility is advertised.
- Bootstrap working set must remain below 150 MB before inference starts.
- The flagship pack must keep combined AgentMuru and inference peak working set below 2 GB and installed model artifacts at or below 700 MB.
- The default context is 512-2,048 tokens.
- Model decisions must be 100% schema-valid, accepted action accuracy must be at least 95%, and all versioned unsafe-action cases must be denied.
- Capabilities are denied unless granted; model output, web content, and imported tool metadata can never grant permissions.
- The native binary must not require Python, Node.js, Docker, WSL2, or a background web server.
- Events are appended before publication and remain monotonic and replayable per session.
- Essential terminal information cannot depend on kitty graphics or sixel; narrow terminals and plain/JSON output are mandatory.
- Android work starts only after Windows pack conformance, reference-device qualification, measured model switching, and security review pass.

---

## Delivery Order

1. [Native Foundation and Terminal Workspace](2026-08-16-agentmuru-native-foundation-and-tui.md)
2. [Verified Local Model Runtime](2026-08-16-agentmuru-verified-local-model-runtime.md)
3. [Adaptive Agent Compiler and Orchestration](2026-08-16-agentmuru-adaptive-agent-compiler.md)
4. [Secure Effects, Web Evidence, and Feedback Release](2026-08-16-agentmuru-secure-effects-and-release.md)

The plans are sequential because later tranches consume stable interfaces and measured
limits from earlier tranches. Do not start the compiler against a mocked hardware contract,
and do not add web access before the capability broker exists.

## Repository Ownership Map

```text
schemas/                         language-neutral contracts and golden fixtures
edge/cmd/muru/                   native executable entry point
edge/internal/platform/         hardware and terminal discovery
edge/internal/contracts/        Go contract types and validation
edge/internal/events/           append-before-publish native events
edge/internal/ui/               Bubble Tea workspace and product-specific panes
edge/internal/catalog/          signed model/runtime catalog
edge/internal/download/         verified atomic downloads and cache
edge/internal/inference/        llama.cpp supervision and normalized inference
edge/internal/pack/             agent-pack loading, validation, and archive handling
edge/internal/compiler/         guided requirement-to-pack compiler
edge/internal/eval/             task evaluation, metrics, and selection
edge/internal/orchestrator/     typed handoffs, routing, scheduling, execution
edge/internal/policy/           capabilities and authorization decisions
edge/internal/approval/         human approval lifecycle
edge/internal/tools/            built-in, native, MCP, and WASI action adapters
edge/internal/web/              read-only retrieval and evidence records
packs/action-router/            first supported and qualified product pack
qualification/edge/             clean install, benchmark, safety, and UX evidence
packaging/winget/               release manifests and installer metadata
agentmuru/                      existing Python SDK and contract compatibility
frontend/                       existing browser projection; no edge runtime ownership
```

## Gate A: Native Shell Ready

Proceed to local model execution only when:

- `muru doctor --json` passes golden tests on Windows and reports support reasons;
- the full-screen workspace handles 60, 80, 100, and 160 column snapshots;
- redirected output never enters alternate-screen mode;
- fake runtime events appear without polling and idle CPU is recorded;
- sessions replay after process restart; and
- Go and Python conformance fixtures agree.

## Gate B: Local Model Runtime Ready

Proceed to adaptive compilation only when:

- catalog signatures, revisions, sizes, hashes, and license gates are enforced;
- interrupted downloads resume or clean up without exposing partial models;
- incompatible runtime binaries are rejected before execution;
- llama.cpp binds only to loopback with an ephemeral token;
- constrained action responses parse deterministically;
- load, inference, idle sleep, unload, cancellation, and crash recovery are traced; and
- at least one ungated model runs from a clean Windows installation.

## Gate C: Adaptive Team Ready

Proceed to secure effects and public qualification only when:

- the guided compiler produces a valid action-router pack without editing JSON;
- evaluation includes accepted, ambiguous, rejected, and unsafe cases;
- model selection rejects every candidate that violates a mandatory gate;
- multiple logical agents can share one model;
- sequential specialist models never exceed the configured residency budget;
- deterministic routes bypass model calls; and
- simulated execution can explain every route and abstention from recorded events.

## Gate D: Feedback Release Ready

Publish only when:

- the capability broker mediates every effect immediately before execution;
- approvals display exact sanitized arguments, scope, and persistence choice;
- web access is read-only, private-network safe, size/time bounded, and visibly untrusted;
- security qualification covers prompt injection, path traversal, argument injection,
  malicious ANSI, catalog tampering, and process escape attempts;
- the named Pentium-class report meets every advertised release gate;
- a clean user can install, create, benchmark, activate, run, inspect, and remove a pack;
- GitHub and WinGet artifacts are signed and reproducible; and
- public documentation describes only verified behavior.

## Product Feedback Loop

Every run report categorizes failure as one of: hardware incompatibility, model load,
model quality, schema validation, routing, permission, action execution, network evidence,
or interface usability. The feedback command exports a redacted diagnostic bundle only
after showing its file list. It never uploads automatically.

The first feedback cohort is intentionally small:

1. recruit 10 Windows developers or power users with varied CPU generations;
2. observe onboarding and require them to create a pack from their own typed actions;
3. measure completion without documentation, time to first successful action, abstention
   behavior, correction frequency, and peak memory;
4. publish anonymized compatibility and failure distributions; and
5. prioritize the next milestone from observed failures, not feature requests alone.

## Android Entry Decision

After Gate D, create a separate Android design and implementation plan only if the same
flagship pack can be reproduced without Python and the pack has external usage. The first
Android artifact is a native viewer/runner for existing packs, not an on-phone pack
compiler. Termux remains an explicitly unsupported developer experiment until that plan is
approved.

## Master Verification

Run after every tranche:

```powershell
python -m pytest -q
python -m ruff check agentmuru tests
python -m mypy agentmuru
Push-Location edge
go test ./...
go vet ./...
go build ./cmd/muru
Pop-Location
Push-Location frontend
npm test -- --run
npm run lint
npm run typecheck
npm run build
npm run check:bundle
Pop-Location
python -m mkdocs build --strict
python -m build
```

Expected: every command exits zero; the Go commands begin only after the native module is
created in tranche one.
