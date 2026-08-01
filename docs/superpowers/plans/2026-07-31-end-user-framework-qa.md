# BrickFlowUI End-User Framework QA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove that a new user can install, scaffold, run, interact with, and package a BrickFlowUI application without encountering a known reproducible local defect.

**Architecture:** Validate the framework at four boundaries: Python API/server behavior, React runtime behavior, the generated-project CLI journey, and the installed distribution artifact. Use the repository's existing automated suites first, then run a real scaffolded application and inspect it in a browser. Any reproducible defect must receive a focused regression test before its minimal repair.

**Tech Stack:** Python 3.13, FastAPI, pytest, React 18, TypeScript, Vitest, Vite, MkDocs, Hatchling, Playwright-compatible browser automation.

## Global Constraints

- Preserve the existing uncommitted changes in `brickflowui/vdom.py` and `tests/test_vdom.py`.
- Do not publish packages, push commits, create releases, or deploy to Databricks.
- Keep generated user-journey artifacts under `.tmp/end-user-qa/`.
- Treat live Databricks OAuth, workspace permissions, SQL warehouses, Unity Catalog, and Jobs as externally unverified when credentials are unavailable.
- Run each release gate from `D:\Projects\brickflowUI\brickflowUI`.

---

### Task 1: Baseline repository gates

**Files:**
- Verify: `tests/`
- Verify: `frontend/src/**/*.test.ts`
- Verify: `frontend/src/**/*.test.tsx`
- Verify: `docs/`
- Verify: `brickflowui/frontend/dist/`

**Interfaces:**
- Consumes: checked-out Python source, frontend source, installed local dependencies.
- Produces: pass/fail evidence for every documented local release gate.

- [ ] **Step 1: Run the Python suite**

Run: `python -m pytest -q -p no:cacheprovider`

Expected: all tests pass with no unhandled warning or collection error.

- [ ] **Step 2: Run frontend unit tests, lint, and type checking**

Run: `npm --prefix frontend test -- --run`

Run: `npm --prefix frontend run lint`

Run: `npm --prefix frontend run typecheck`

Expected: every command exits successfully.

- [ ] **Step 3: Build the frontend and verify dependencies**

Run: `npm --prefix frontend audit --audit-level=high`

Run: `npm --prefix frontend run build`

Expected: no high-severity vulnerability and a successful production build in `brickflowui/frontend/dist/`.

- [ ] **Step 4: Build strict documentation and distributions**

Run: `python -m mkdocs build --strict -d .tmp/end-user-qa/site`

Run: `python -m build --outdir .tmp/end-user-qa/dist`

Run: `python -m twine check .tmp/end-user-qa/dist/*`

Expected: strict docs, wheel, source distribution, and metadata validation all pass.

### Task 2: New-user CLI and installed-artifact journey

**Files:**
- Exercise: `brickflowui/cli/main.py`
- Exercise: `brickflowui/cli/templates/default/`
- Generate: `.tmp/end-user-qa/scaffold/`
- Generate: `.tmp/end-user-qa/venv/`

**Interfaces:**
- Consumes: the wheel produced by Task 1 and the public `brickflowui` console command.
- Produces: an isolated generated app that imports only the built distribution.

- [ ] **Step 1: Create and populate an isolated virtual environment**

Run: `python -m venv .tmp/end-user-qa/venv`

Run: `.tmp/end-user-qa/venv/Scripts/python -m pip install .tmp/end-user-qa/dist/brickflowui-0.1.13-py3-none-any.whl`

Expected: BrickFlowUI and its runtime dependencies install successfully.

- [ ] **Step 2: Verify the installed CLI**

Run: `.tmp/end-user-qa/venv/Scripts/brickflowui --help`

Run from `.tmp/end-user-qa/`: `venv/Scripts/brickflowui new scaffold`

Expected: help renders without a traceback and the scaffold contains `app.py`, `app.yaml`, `requirements.txt`, and `.env.example`.

- [ ] **Step 3: Start the generated application**

Run from `.tmp/end-user-qa/scaffold`: `..\venv\Scripts\brickflowui dev --host 127.0.0.1 --port 8065`

Expected: the app serves HTML at `http://127.0.0.1:8065` and establishes its event WebSocket.

### Task 3: Browser end-user acceptance

**Files:**
- Exercise: `.tmp/end-user-qa/scaffold/app.py`
- Exercise: packaged assets in `.tmp/end-user-qa/venv/Lib/site-packages/brickflowui/frontend/dist/`

**Interfaces:**
- Consumes: the running isolated scaffold from Task 2.
- Produces: interaction, accessibility, responsiveness, network, and console evidence.

- [ ] **Step 1: Load the app at a desktop viewport**

Open: `http://127.0.0.1:8065`

Expected: branded content is visible, loading state resolves, and the browser console contains no errors.

- [ ] **Step 2: Exercise the primary interaction**

Click the scaffold's primary button and observe the changed count or state text.

Expected: exactly one user action produces exactly one visible state transition without a page reload.

- [ ] **Step 3: Exercise responsive layout**

Set the viewport to `390x844`, reload, and inspect document width and primary controls.

Expected: no horizontal document overflow, clipped control, or unreachable action.

- [ ] **Step 4: Inspect accessibility and transport**

Inspect headings, button accessible names, focusability, HTTP asset failures, WebSocket state, and browser console errors.

Expected: the page has a named primary heading and button, all packaged assets load, and the WebSocket remains connected.

### Task 4: Defect repair protocol

**Files:**
- Modify: `brickflowui/cli/main.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: a deterministic failure from Tasks 1–3.
- Produces: clean terminal text without leaking renderer-specific markup.

- [ ] **Step 1: Reproduce and isolate each failure**

Record the shortest deterministic command or browser action, expected result, actual result, affected boundary, and evidence excluding credentials.

- [ ] **Step 2: Add focused CLI output regressions**

Add `test_new_command_renders_success_message_without_markup` and `test_dev_command_renders_banner_without_markup` to `tests/test_cli.py`.

Run: `python -m pytest -q -p no:cacheprovider tests/test_cli.py -k "without_markup"`

Expected before repair: both tests fail because `result.output` contains literal Rich tags.

- [ ] **Step 3: Remove markup from plain echo calls**

Change the `new` success message and `dev` startup banner in `brickflowui/cli/main.py` to clean plain terminal text while retaining all existing guidance and URLs.

Run: `python -m pytest -q -p no:cacheprovider tests/test_cli.py`

Expected after repair: all CLI tests pass.

- [ ] **Step 4: Re-run the affected end-user path**

Repeat the exact release command or browser interaction that exposed the defect and retain the result in the final report.

### Task 5: Final release-confidence verification

**Files:**
- Verify: all files changed during this QA pass.
- Report: `docs/verification/2026-07-31-end-user-framework-qa.md`

**Interfaces:**
- Consumes: completed baseline, isolated-user journey, browser evidence, and repairs.
- Produces: a concise reproducible QA report and an explicit list of external residual risks.

- [ ] **Step 1: Run the complete relevant gate set again**

Run all commands from Task 1 plus `python scripts/smoke_examples.py`.

Expected: all local gates and example startup checks pass.

- [ ] **Step 2: Inspect repository changes**

Run: `git diff --check`

Run: `git status --short`

Expected: no whitespace error and no unexplained tracked or generated artifact.

- [ ] **Step 3: Write the evidence report**

Document environment versions, exact commands, test counts, browser results, defects and repairs, preserved pre-existing edits, and remaining Databricks/load/platform risks in `docs/verification/2026-07-31-end-user-framework-qa.md`.

- [ ] **Step 4: Self-review against the user goal**

Confirm the report distinguishes proven local behavior from assumptions, avoids production-readiness claims for untested external services, and gives the maintainer a prioritized next action for every residual risk.
