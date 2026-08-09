# AgentMuru Exact Brand Propagation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace every approximated AgentMuru mark with the owner-approved DataMuru Hybrid Vel Eye master and publish the same identity across product, documentation, and landing surfaces.

**Architecture:** Treat the approved transparent PNG as an immutable brand input. Each repository carries a local copy so package builds and static deployments remain deterministic; tests verify the approved SHA-256 and consumer-visible image references. Text lockups continue to say AgentMuru while using the exact shared mark.

**Tech Stack:** PNG assets, React, Next.js 16, Vite, Vitest, Pytest, MkDocs Material, Playwright, Vercel.

## Global Constraints

- Canonical source: `D:\Projects\DataMuru\DataMuru Docs\Brand\Logo Exploration\datamuru-approved-vel-eye-master-512.png`.
- Canonical SHA-256: `44DC00F0415775733B6A3AEF3DD0F037C9666AFBCED6D6676552B76B2F54C5A2`.
- Do not redraw, trace, recolor, or generate the mark.
- Preserve AgentMuru product naming and the approved palette: `#0A7C7F`, `#0D5F8A`, `#C48A1F`, `#0D0F14`, `#F4F7FB`.
- Publish only after focused tests and each repository's full verification gate pass.

---

### Task 1: Exact asset contract

**Files:**
- Modify: `tests/test_branding.py`
- Modify: landing `src/components/AgentMuruLogo.test.tsx`
- Modify: `frontend/src/workspace/Workspace.test.tsx`

**Interfaces:**
- Consumes: the canonical SHA-256 above.
- Produces: regression coverage for documentation, landing, and packaged Workspace brand assets.

- [x] **Step 1: Write failing tests for the approved hash and rendered asset paths.**
- [x] **Step 2: Run each focused test and confirm it fails because the PNG or reference is absent.**
- [x] **Step 3: Keep the assertions consumer-visible: emitted image `src`, accessible product lockup, and immutable asset bytes.**

### Task 2: Documentation and Workspace propagation

**Files:**
- Create: `docs/assets/agentmuru-mark.png`
- Create: `docs/assets/BRAND.md`
- Create: `frontend/public/agentmuru-mark.png`
- Modify: `mkdocs.yml`
- Modify: `frontend/src/workspace/SessionRail.tsx`
- Modify: `frontend/src/theme.css`
- Regenerate: `agentmuru/frontend/dist/`
- Delete: `docs/assets/agentmuru-mark.svg`

**Interfaces:**
- Consumes: the canonical master and Task 1 tests.
- Produces: exact docs navigation/favicon and Workspace header mark in source and wheel assets.

- [x] **Step 1: Copy the canonical PNG without modification and verify its hash.**
- [x] **Step 2: Replace the generic Workspace bot glyph with the PNG and preserve adjacent AgentMuru text.**
- [x] **Step 3: Point MkDocs logo and favicon configuration to the PNG.**
- [x] **Step 4: Build Workspace so the packaged distribution contains the same file.**
- [x] **Step 5: Run focused tests, frontend build/bundle checks, and strict docs build.**

### Task 3: Landing, metadata, and social propagation

**Files:**
- Create: landing `public/brand/agentmuru-mark.png`
- Modify: landing `src/components/AgentMuruMark.tsx`
- Modify: landing `src/components/AgentMuruLogo.tsx`
- Modify: landing `src/app/layout.tsx`
- Modify: landing `src/app/manifest.ts`
- Modify: landing `src/app/opengraph-image.tsx`
- Modify: landing `src/app/components.css`
- Delete: landing approximated SVG assets.

**Interfaces:**
- Consumes: the canonical master and Task 1 tests.
- Produces: exact navigation, footer, CTA, metadata icon, install icon, and Open Graph identity.

- [x] **Step 1: Copy and hash-verify the canonical PNG.**
- [x] **Step 2: Render the mark with a normal image element and correct decorative/accessibility semantics.**
- [x] **Step 3: Use the PNG in metadata, manifest, and generated Open Graph output.**
- [x] **Step 4: Run focused unit tests and inspect the rendered page at desktop, mobile, favicon, and social-image surfaces.**

### Task 4: Release and local transformation

**Files:**
- Commit the exact-brand changes in each repository.
- Rename the local workspace and legacy-named child folders only after repositories are clean.

**Interfaces:**
- Consumes: fully verified commits.
- Produces: pushed branches, reviewable pull requests or production artifact, verified Vercel deployment, and an AgentMuru-named local workspace.

- [x] **Step 1: Run full Python, frontend, docs, package, landing, and browser gates.**
- [ ] **Step 2: Review diffs, stage only intentional files, commit, and push.**
- [ ] **Step 3: create the GitHub review artifact and update the roadmap status.**
- [ ] **Step 4: deploy the verified landing artifact to Vercel production and recheck the live logo.**
- [ ] **Step 5: verify every move target is absent, rename the local workspace, and confirm clean Git state at the new paths.**
