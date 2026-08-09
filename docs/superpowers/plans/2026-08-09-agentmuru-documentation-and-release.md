# AgentMuru Documentation and Release Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task after `2026-08-09-agentmuru-persistence-and-qualification.md`. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the verified 0.2 implementation into precise, comprehensive documentation and reproducible release artifacts.

**Architecture:** MkDocs remains the documentation source of truth. Runnable examples are imported into guides, qualification JSON is rendered into a human-readable evidence report, and CI repeats the build-from-wheel gate before docs or distributions can publish.

**Tech Stack:** MkDocs Material, Markdown, Python 3.10+, Python `build`, Twine, GitHub Actions, GitHub Pages.

## Global Constraints

- Documentation advertises only behavior verified in the fresh qualification report.
- AgentMuru uses the DataMuru family palette, Hybrid Vel Eye geometry, Inter, DM Sans, and JetBrains Mono.
- Copy is precise, quietly confident, culturally grounded, and engineer-first.
- Credential-backed Databricks status is recorded separately from deterministic contract coverage.
- SQLite's one-runtime-per-file and modest-concurrency limits must be prominent.
- Release version is `0.2.0`; tag format is `agentmuru-v0.2.0`.
- PyPI publication requires a successful trusted-publisher workflow; built files alone are not a published release.

---

### Task 1: Apply the AgentMuru product-family documentation identity

**Files:**
- Modify: `mkdocs.yml`
- Create: `docs/assets/agentmuru-mark.svg`
- Create: `docs/stylesheets/agentmuru.css`
- Modify: `docs/index.md`
- Test: `tests/test_branding.py`

**Interfaces:**
- Produces CSS tokens `--muru-teal`, `--muru-cobalt`, `--muru-gold`, `--muru-obsidian`, and `--muru-mist`.
- Produces accessible AgentMuru SVG mark with title `AgentMuru Hybrid Vel Eye mark`.

- [ ] **Step 1: Add failing branding assertions for exact tokens, logo, fonts, and identity.**

```python
def test_docs_use_agentmuru_product_family_identity() -> None:
    config = Path("mkdocs.yml").read_text(encoding="utf-8")
    css = Path("docs/stylesheets/agentmuru.css").read_text(encoding="utf-8")
    logo = Path("docs/assets/agentmuru-mark.svg").read_text(encoding="utf-8")
    assert "docs/assets/agentmuru-mark.svg" in config
    assert "#0A7C7F" in css and "#0D5F8A" in css and "#C48A1F" in css
    assert "AgentMuru Hybrid Vel Eye mark" in logo
    assert "BrickflowUI is" not in Path("docs/index.md").read_text(encoding="utf-8")
```

- [ ] **Step 2: Run the branding test and confirm missing assets and tokens fail.**

Run: `python -m pytest tests/test_branding.py::test_docs_use_agentmuru_product_family_identity -q`

- [ ] **Step 3: Create the flat SVG mark and documentation stylesheet.**

The SVG uses Peacock Teal outer geometry, Cobalt inner eye, Eye Gold focal point, and a white/teal Vel channel. It contains no live text, gradient, filter, shadow, deity, feather illustration, or embedded raster.

```css
:root {
  --muru-teal: #0A7C7F;
  --muru-cobalt: #0D5F8A;
  --muru-gold: #C48A1F;
  --muru-obsidian: #0D0F14;
  --muru-mist: #F4F7FB;
}
```

- [ ] **Step 4: Configure MkDocs logo, favicon, palette, fonts, and restrained homepage styling.**

Add `extra_css: [stylesheets/agentmuru.css]`, use the SVG for `theme.logo` and `theme.favicon`, and preserve high-contrast light reading surfaces with an Obsidian hero.

- [ ] **Step 5: Run branding tests and strict documentation build.**

Run: `python -m pytest tests/test_branding.py -q`

Run: `python -m mkdocs build --strict`

- [ ] **Step 6: Commit the documentation identity.**

```powershell
git add mkdocs.yml docs/assets docs/stylesheets docs/index.md tests/test_branding.py
git commit -m "docs: apply AgentMuru product-family identity"
```

### Task 2: Document installation, public API, and durable persistence

**Files:**
- Modify: `docs/getting-started.md`
- Create: `docs/reference/public-api.md`
- Create: `docs/guides/sqlite-persistence.md`
- Modify: `docs/guides/session-store.md`
- Modify: `docs/guides/security.md`
- Create: `docs/guides/server-and-workspace.md`
- Create: `docs/guides/deployment.md`
- Create: `docs/migration-custom-stores-0.2.md`
- Modify: `mkdocs.yml`
- Test: `tests/test_documentation_contract.py`

**Interfaces:**
- Documents only exports present in `agentmuru.__all__`.
- Documents the exact `SQLitePersistence` constructor and explicit `SessionStore`/`ApprovalStore` methods from Plan 1.

- [ ] **Step 1: Add failing documentation-contract tests for required commands and limitations.**

```python
def test_persistence_guide_contains_verified_contract() -> None:
    guide = Path("docs/guides/sqlite-persistence.md").read_text(encoding="utf-8")
    assert "SQLitePersistence(\"agentmuru.db\")" in guide
    assert "one active AgentMuru runtime process" in guide
    assert "BEGIN IMMEDIATE" in guide
    assert "storage_busy" in guide
    assert "process_interrupted" in guide
```

- [ ] **Step 2: Run the documentation contract and confirm missing pages fail.**

Run: `python -m pytest tests/test_documentation_contract.py -q`

- [ ] **Step 3: Write the clean-install guide and stable public API reference.**

The quickstart begins with `python -m pip install agentmuru==0.2.0`, `muru doctor`, and `muru init`. Source installation appears in a contributor section. Each public API entry contains its import, constructor or signature, behavior, and one executable example.

- [ ] **Step 4: Write the SQLite operator guide, server/Workspace operations guide, deployment checklist, and custom-store migration guide.**

Cover configuration, supported content, schema initialization, WAL, backup using SQLite's backup API, reopen behavior, cross-instance subscriptions, busy retries, corruption handling, permissions, encryption limits, one-runtime ownership, and the exact explicit mutation methods custom stores must add. The server/Workspace guide covers startup, health, authentication, replay, WebSocket reconnect, artifact access, approvals, cancellation, and shutdown. The deployment and security guides provide checklists for trusted hosts, origins, TLS termination, bearer or application authentication, database path permissions, backup, secrets, payload limits, and the absence of built-in SQLite encryption.

- [ ] **Step 5: Add navigation entries and verify every documented import.**

Run: `python -m pytest tests/test_documentation_contract.py tests/test_public_api.py -q`

Run: `python -m mkdocs build --strict`

- [ ] **Step 6: Commit installation, API, and persistence documentation.**

```powershell
git add docs/getting-started.md docs/reference docs/guides docs/migration-custom-stores-0.2.md mkdocs.yml tests/test_documentation_contract.py
git commit -m "docs: add durable runtime operator guide"
```

### Task 3: Build the executable AgentMuru cookbook

**Files:**
- Create: `docs/cookbook/index.md`
- Create: `docs/cookbook/governed-tools.md`
- Create: `docs/cookbook/artifacts.md`
- Create: `docs/cookbook/durable-sessions.md`
- Create: `docs/cookbook/workflows-and-handoffs.md`
- Create: `docs/cookbook/databricks.md`
- Modify: `mkdocs.yml`
- Modify: `tests/test_examples.py`

**Interfaces:**
- Consumes scenario sources from Plan 1.
- Each cookbook page names the exact example module and command used by qualification.

- [ ] **Step 1: Add failing assertions that every scenario has one cookbook page and command.**

```python
@pytest.mark.parametrize(("example", "page"), [
    ("examples/governed_tool_agent.py", "docs/cookbook/governed-tools.md"),
    ("examples/artifact_agent.py", "docs/cookbook/artifacts.md"),
    ("examples/durable_agent.py", "docs/cookbook/durable-sessions.md"),
    ("examples/handoff_agent.py", "docs/cookbook/workflows-and-handoffs.md"),
    ("examples/databricks_agent.py", "docs/cookbook/databricks.md"),
])
def test_scenario_has_cookbook_page(example: str, page: str) -> None:
    text = Path(page).read_text(encoding="utf-8")
    assert example.replace("/", ".").removesuffix(".py") in text
```

- [ ] **Step 2: Run the example tests and confirm missing cookbook files fail.**

Run: `python -m pytest tests/test_examples.py -q`

- [ ] **Step 3: Write task-oriented cookbook pages from the runnable scenarios.**

Each page contains: outcome, complete import path, command, expected terminal result, expected Workspace state, failure modes, and the exact test that qualifies it. Databricks clearly separates contract verification from live credential verification.

- [ ] **Step 4: Add cookbook navigation and verify examples plus docs together.**

Run: `python -m pytest tests/test_examples.py tests/qualification/test_scenarios.py -q`

Run: `python -m mkdocs build --strict`

- [ ] **Step 5: Commit the cookbook.**

```powershell
git add docs/cookbook mkdocs.yml tests/test_examples.py
git commit -m "docs: publish executable AgentMuru cookbook"
```

### Task 4: Generate the qualification and integration-status reports

**Files:**
- Create: `qualification/render_report.py`
- Create: `docs/qualification.md`
- Create: `docs/integration-status.md`
- Modify: `qualification/run_clean_install.py`
- Modify: `mkdocs.yml`
- Test: `tests/qualification/test_report.py`

**Interfaces:**
- Produces `render_report(report: Mapping[str, Any]) -> str`.
- Produces a Markdown table with capability, test command, result, evidence time, and limitation.

- [ ] **Step 1: Write a failing deterministic report-rendering test.**

```python
def test_report_distinguishes_contract_and_live_verification() -> None:
    markdown = render_report({
        "environment": {"python": "3.11"},
        "scenarios": [{"name": "sqlite_restart", "status": "passed"}],
        "databricks_live": {"status": "not_executed", "reason": "credentials unavailable"},
        "failures": [],
    })
    assert "SQLite restart | Passed" in markdown
    assert "Databricks live | Not executed" in markdown
    assert "credentials unavailable" in markdown
```

- [ ] **Step 2: Run the report test and confirm the renderer is missing.**

Run: `python -m pytest tests/qualification/test_report.py -q`

- [ ] **Step 3: Implement deterministic Markdown rendering and attach it to the harness.**

The clean-install runner writes JSON first and only replaces `docs/qualification.md` after every required check passes. A failed run preserves the last passing report and writes failure evidence under `.tmp`.

- [ ] **Step 4: Write the integration-status page using four exact states.**

Use `Implemented`, `Contract tested`, `Credential verified`, and `Planned`. FakeModel, SQLite, and in-memory stores are implemented. Databricks receives the state demonstrated by the latest report. Production model providers and PostgreSQL are planned.

- [ ] **Step 5: Run qualification to regenerate the report, then build docs.**

Run: `python qualification/run_clean_install.py --wheel dist/agentmuru-0.2.0-py3-none-any.whl --report .tmp/qualification.json --markdown docs/qualification.md`

Run: `python -m pytest tests/qualification/test_report.py -q`

Run: `python -m mkdocs build --strict`

- [ ] **Step 6: Commit qualification evidence and status.**

```powershell
git add qualification/render_report.py qualification/run_clean_install.py docs/qualification.md docs/integration-status.md mkdocs.yml tests/qualification/test_report.py
git commit -m "docs: publish AgentMuru qualification evidence"
```

### Task 5: Update release surfaces and migration records

**Files:**
- Modify: `README.md`
- Modify: `docs/CHANGELOG.md`
- Modify: `docs/architecture/decisions.md`
- Modify: `docs/architecture/target-state.md`
- Modify: `docs/architecture/ai-native-transformation.md`
- Modify: `docs/migration-from-legacy-ui.md`
- Modify: `agentmuru/version.py`
- Modify: `pyproject.toml`
- Test: `tests/test_branding.py`
- Test: `tests/test_packaging.py`

**Interfaces:**
- Public version is exactly `0.2.0` in package metadata and `agentmuru.version.__version__`.
- README primary path is PyPI install; source install remains contributor-only.

- [ ] **Step 1: Add failing release-copy and changelog assertions while retaining the version consistency check from Plan 1.**

```python
def test_release_version_is_consistent() -> None:
    assert __version__ == "0.2.0"
    assert tomllib.loads(Path("pyproject.toml").read_text())["project"]["version"] == "0.2.0"
    assert "SQLitePersistence" in Path("README.md").read_text(encoding="utf-8")
    assert "## 0.2.0" in Path("docs/CHANGELOG.md").read_text(encoding="utf-8")
```

- [ ] **Step 2: Run branding and packaging tests and confirm missing 0.2 release copy or changelog evidence fails.**

Run: `python -m pytest tests/test_branding.py tests/test_packaging.py -q`

- [ ] **Step 3: Update README, changelog, architecture decisions, and migration records.**

Document the explicit-store decision, SQLite scope, recovery behavior, qualification method, custom-store migration, and honest limitations. Remove the obsolete claim that durable stores are only extension interfaces.

- [ ] **Step 4: Run release-surface tests and strict docs.**

Run: `python -m pytest tests/test_branding.py tests/test_packaging.py tests/test_documentation_contract.py -q`

Run: `python -m mkdocs build --strict`

- [ ] **Step 5: Commit the 0.2 release surface.**

```powershell
git add README.md docs agentmuru/version.py pyproject.toml tests/test_branding.py tests/test_packaging.py
git commit -m "release: prepare AgentMuru 0.2 documentation"
```

### Task 6: Make qualification a CI publication gate

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `.github/workflows/docs.yml`
- Modify: `.github/workflows/publish.yml`
- Test: `tests/test_packaging.py`

**Interfaces:**
- CI produces wheel and sdist, then runs the installed-wheel smoke test on Python 3.11.
- Docs and publish workflows depend on required verification jobs.

- [ ] **Step 1: Add failing workflow contract assertions.**

```python
def test_publish_workflow_requires_qualification() -> None:
    workflow = yaml.safe_load(Path(".github/workflows/publish.yml").read_text())
    assert "qualification" in workflow["jobs"]
    assert workflow["jobs"]["publish"]["needs"] == ["qualification"]
```

- [ ] **Step 2: Run the packaging test and confirm workflow requirements fail.**

Run: `python -m pytest tests/test_packaging.py -q`

- [ ] **Step 3: Update workflows with build-once and installed-wheel qualification.**

The qualification job downloads the built artifact, installs it into a fresh runner environment, executes `qualification/installed_smoke.py`, checks distributions with Twine, and uploads the report. `publish` retains `id-token: write` and environment `pypi`.

- [ ] **Step 4: Validate workflow YAML and packaging contracts.**

Run: `python -m pytest tests/test_packaging.py -q`

Run: `python -m mkdocs build --strict`

- [ ] **Step 5: Commit CI publication gates.**

```powershell
git add .github/workflows tests/test_packaging.py
git commit -m "ci: gate AgentMuru releases on qualification"
```

### Task 7: Build and inspect final documentation and distributions

**Files:**
- Verify: `docs/`
- Verify: `dist/`
- Verify: `site/`
- Verify: `.tmp/qualification.json`

**Interfaces:**
- Produces verified `agentmuru-0.2.0-py3-none-any.whl`, `agentmuru-0.2.0.tar.gz`, MkDocs site, and qualification report.

- [ ] **Step 1: Run the full repository verification suite.**

Run: `python -m pytest -q`

Run: `python -m ruff check agentmuru tests qualification`

Run: `python -m mypy agentmuru`

Run from `frontend`: `npm test -- --run`

Run from `frontend`: `npm run lint`

Run from `frontend`: `npm run typecheck`

Run from `frontend`: `npm run build`

Run from `frontend`: `npm run check:bundle`

Run from `frontend`: `npm run test:e2e`

- [ ] **Step 2: Build strict documentation and distributions.**

Run: `python -m mkdocs build --strict`

Run: `python -m build`

Run: `python -m twine check dist/*`

- [ ] **Step 3: Inspect wheel and sdist contents and metadata.**

Run: `python -m zipfile -l dist/agentmuru-0.2.0-py3-none-any.whl`

Run: `tar -tf dist/agentmuru-0.2.0.tar.gz`

Confirm package name `agentmuru`, version `0.2.0`, bundled Workspace assets, documentation sources in sdist, and no `.superpowers`, local databases, secrets, caches, or temporary qualification environments.

- [ ] **Step 4: Rerun clean-wheel qualification against the exact final wheel.**

Run: `python qualification/run_clean_install.py --wheel dist/agentmuru-0.2.0-py3-none-any.whl --report .tmp/qualification.json --markdown docs/qualification.md`

- [ ] **Step 5: Check the final diff and record fresh evidence for launch operations.**

Run: `git diff --check`

Run: `git status --short`
