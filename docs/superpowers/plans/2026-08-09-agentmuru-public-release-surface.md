# AgentMuru Public Release Surface Implementation Plan

> **For Ajay:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make AgentMuru's exact public identity, installation path, documentation URL, and PyPI publishing contract consistent and verifiable everywhere users encounter the project.

**Architecture:** Treat the public release surface as a tested configuration contract spanning package metadata, documentation configuration, repository community files, and the README. Keep publishing OIDC-based through the existing `publish.yml` workflow and defer the release event until PyPI's matching trusted publisher exists.

**Tech Stack:** Python 3.11+, pytest, `tomllib`, PyYAML, MkDocs Material, Python `build`, Twine, GitHub Actions, PyPI trusted publishing.

---

### Task 1: Establish a clean merged baseline

**Files:**
- Inspect: `AGENTS.md`
- Inspect: `pyproject.toml`

- [ ] Fast-forward `dev` to the merged `origin/main` state.
- [ ] Confirm the worktree is clean and the active branch is not `main`.
- [ ] Run `python -m pytest -q` and record the passing baseline.

### Task 2: Lock the public release contract with tests

**Files:**
- Modify: `tests/test_branding.py`
- Test: `tests/test_branding.py`

- [ ] Add assertions for exact-case GitHub and GitHub Pages URLs in package and MkDocs metadata.
- [ ] Add assertions for the public `pip install agentmuru` and hosted documentation paths in README/support surfaces.
- [ ] Run `python -m pytest tests/test_branding.py -q` and confirm the new contract fails before implementation.

### Task 3: Make exact AgentMuru branding visible everywhere

**Files:**
- Modify: `README.md`
- Modify: `pyproject.toml`
- Modify: `mkdocs.yml`
- Modify: `.github/ISSUE_TEMPLATE/config.yml`
- Modify: `SUPPORT.md`

- [ ] Add public status badges and make PyPI installation the primary README path.
- [ ] Separate contributor/source installation from end-user installation.
- [ ] Change all current public repository and documentation URLs to exact `AgentMuru` casing.
- [ ] Run the focused branding tests and confirm they pass.

### Task 4: Verify documentation and distributions

**Files:**
- Verify: `README.md`
- Verify: `pyproject.toml`
- Verify: `mkdocs.yml`
- Verify: `.github/workflows/publish.yml`

- [ ] Run `python -m mkdocs build --strict`.
- [ ] Run `python -m build` and `python -m twine check dist/*`.
- [ ] Inspect built metadata for package name `agentmuru`, version `0.1.0`, and exact public URLs.
- [ ] Confirm workflow file `publish.yml` uses environment `pypi` and OIDC permission `id-token: write`.

### Task 5: Run the complete repository verification suite

**Files:**
- Verify: `agentmuru/`
- Verify: `tests/`
- Verify: `frontend/`
- Verify: `docs/`

- [ ] Run `python -m pytest -q`.
- [ ] Run `python -m ruff check agentmuru tests`.
- [ ] Run `python -m mypy agentmuru`.
- [ ] Run frontend tests, lint, typecheck, build, and bundle checks.
- [ ] Re-run strict docs and distribution checks after all edits.

### Task 6: Publish the change for review and prepare the release

**Files:**
- Commit: all files above
- Publish: `dev` to GitHub

- [ ] Update the GitHub repository homepage to `https://ajayaj2000.github.io/AgentMuru/`.
- [ ] Commit the verified release-surface changes and push `dev`.
- [ ] Open a ready-for-review PR from `dev` to `main` and confirm CI.
- [ ] After the PR is merged and the PyPI trusted publisher is saved, publish GitHub release `AgentMuru 0.1.0` using tag `agentmuru-v0.1.0`.
- [ ] Confirm the publish workflow succeeds, PyPI exposes `agentmuru==0.1.0`, and a clean `pip install agentmuru` succeeds.
