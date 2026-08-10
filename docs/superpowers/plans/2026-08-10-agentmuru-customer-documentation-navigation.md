# AgentMuru Customer Documentation Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure AgentMuru documentation around customer goals, using DataMuru's product-documentation information architecture as the reference.

**Architecture:** MkDocs remains the source of truth. The public navigation leads with Start, Tutorials, How-to guides, Concepts, and Reference; existing qualification and contributor architecture pages remain buildable and linkable but do not compete with customer tasks in the public nav. The current getting-started page becomes a path selector, with installation and the verified local quickstart separated into focused pages.

**Tech Stack:** MkDocs Material, Markdown, YAML, pytest.

## Global Constraints

- Preserve every existing documentation page unless a replacement provides the same customer outcome.
- Advertise only AgentMuru 0.2 behavior supported by existing qualification evidence.
- Keep public navigation labels task-oriented and customer-facing.
- Preserve exact public API, SQLite, security, migration, and release claims.
- Keep qualification evidence and contributor architecture reachable through contextual links, not primary navigation.

---

### Task 1: Lock the customer-facing navigation contract

**Files:**
- Modify: `tests/test_documentation_contract.py`
- Modify: `mkdocs.yml`

**Interfaces:**
- Consumes: the existing MkDocs `nav` configuration.
- Produces: top-level public sections `Home`, `Start`, `Tutorials`, `How-to guides`, `Concepts`, and `Reference`.

- [x] **Step 1: Add a failing test for public navigation labels and internal-page exclusions.**

The test loads `mkdocs.yml`, asserts the six customer-facing top-level labels in order, asserts Start contains `Choose a path`, `Installation`, and `Five-minute local quickstart`, and rejects `Qualification`, `Integration status`, `Architecture`, `Current state`, `Target state`, `Transformation log`, and `Decisions` from serialized public navigation.

- [x] **Step 2: Run the focused test and verify the existing product/internal mix fails.**

Run: `python -m pytest tests/test_documentation_contract.py::test_public_navigation_follows_customer_tasks -q`

Expected: FAIL because the current top-level navigation starts with `Overview`, `Getting started`, `Public API`, `Qualification`, and `Integration status`.

- [x] **Step 3: Replace the MkDocs navigation with the customer journey.**

Map the executable cookbook pages under Tutorials, the operational guides under How-to guides, the existing mental-model pages under Concepts, and API/capability/release/migration/roadmap pages under Reference. Leave generated qualification evidence and contributor architecture pages outside `nav` so MkDocs still builds and validates them.

- [x] **Step 4: Run the focused contract test.**

Run: `python -m pytest tests/test_documentation_contract.py::test_public_navigation_follows_customer_tasks -q`

Expected: PASS.

### Task 2: Split onboarding into path selection, installation, and a verified quickstart

**Files:**
- Modify: `docs/getting-started.md`
- Create: `docs/getting-started/installation.md`
- Create: `docs/getting-started/quickstart.md`
- Modify: `docs/index.md`
- Modify: `tests/test_documentation_contract.py`

**Interfaces:**
- Consumes: the verified `agentmuru==0.2.0`, `muru doctor`, `muru init`, and `muru run app:application` commands.
- Produces: one decision page, one installation reference, and one end-to-end local tutorial.

- [x] **Step 1: Update the quickstart contract test to target the new page and add assertions for the three distinct onboarding outcomes.**

The path-selection page must route readers by goal. The installation page must contain the pinned PyPI command and contributor-only editable installation. The quickstart page must contain doctor, init, run, the local URL, expected outcome, and next steps.

- [x] **Step 2: Run the onboarding tests and verify the missing pages fail.**

Run: `python -m pytest tests/test_documentation_contract.py -q`

Expected: FAIL because `docs/getting-started/installation.md` and `docs/getting-started/quickstart.md` do not exist.

- [x] **Step 3: Write the three focused onboarding pages and update homepage links.**

Follow DataMuru's pattern: state the outcome first, show prerequisites before steps, use customer goals to route readers, and keep contributor setup separate from the product installation path.

- [x] **Step 4: Run documentation tests and strict MkDocs validation.**

Run: `python -m pytest tests/test_documentation_contract.py tests/test_branding.py -q`

Run: `python -m mkdocs build --strict`

Expected: both commands PASS with no broken links or unlisted-page warnings.

### Task 3: Make the homepage explain the documentation journey

**Files:**
- Modify: `docs/index.md`
- Test: `tests/test_documentation_contract.py`

**Interfaces:**
- Consumes: the new Start, Tutorials, How-to guides, Concepts, and Reference routes.
- Produces: customer-goal and documentation-organization tables on the AgentMuru home page.

- [x] **Step 1: Add a failing homepage discovery test.**

Assert that the homepage contains `Choose your goal`, `How the docs are organized`, and links to the local quickstart, SQLite guide, governed-tools tutorial, public API, and current capabilities.

- [x] **Step 2: Run the test and verify the discovery sections are missing.**

Run: `python -m pytest tests/test_documentation_contract.py::test_homepage_routes_readers_by_goal -q`

Expected: FAIL because the current homepage ends after the hero and feature grid.

- [x] **Step 3: Add the concise goal map and documentation-organization section.**

Use factual, customer-facing copy. Keep qualification implementation details out of the primary path and link capability claims to `integration-status.md`.

- [x] **Step 4: Run focused and full documentation verification.**

Run: `python -m pytest tests/test_documentation_contract.py tests/test_branding.py -q`

Run: `python -m mkdocs build --strict`

Run: `git diff --check`

Expected: all commands PASS.
