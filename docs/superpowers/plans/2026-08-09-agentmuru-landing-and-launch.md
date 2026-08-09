# AgentMuru Landing and Launch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task after the persistence/qualification and documentation/release plans. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the BrickFlowUI landing site with the verified AgentMuru Precision Runtime experience, deploy it through Vercel CLI, and align GitHub roadmap and release state.

**Architecture:** A compact Next.js 16 App Router site renders a single content-driven landing page with focused React components, centralized product copy, flat SVG family branding, static metadata, and generated social imagery. Local tests and browser checks gate a Vercel preview, then the same production build is verified before promotion.

**Tech Stack:** Next.js 16.2.6, React 19.2.4, TypeScript 5, CSS, Vitest, Testing Library, Playwright, axe-core, Vercel CLI, GitHub connector, GitHub Projects.

## Global Constraints

- Landing product name is **AgentMuru**; no public BrickFlowUI identity remains.
- Visual direction is **Precision Runtime**, supported by Live Workspace proof and documentation-first onboarding.
- Hero promise is **Build agents you can see, steer, and trust.**
- Use Peacock Teal `#0A7C7F`, Cobalt Wing `#0D5F8A`, Eye Gold `#C48A1F`, Obsidian `#0D0F14`, Mist `#F4F7FB`, and Near Black `#111827`.
- Use Inter, DM Sans, and JetBrains Mono; use flat color with no gradients, glassmorphism, shadows, decorative feathers, or religious illustration.
- Claims must match the latest passing qualification report.
- The page must remain usable at 360px width, 200% zoom, reduced motion, keyboard-only navigation, and high-contrast modes.
- Vercel deployment protection remains enabled; protected previews are checked with `vercel curl`.
- GitHub issues and project changes must target `AjayAJ2000/AgentMuru`.

---

### Task 1: Establish the landing test and CLI toolchain

**Files:**
- Modify: `../BrickFlowUI Landing/brickflowui-landing/package.json`
- Modify: `../BrickFlowUI Landing/brickflowui-landing/package-lock.json`
- Modify: `../BrickFlowUI Landing/brickflowui-landing/next.config.ts`
- Create: `../BrickFlowUI Landing/brickflowui-landing/vitest.config.ts`
- Create: `../BrickFlowUI Landing/brickflowui-landing/src/test/setup.ts`
- Create: `../BrickFlowUI Landing/brickflowui-landing/playwright.config.ts`
- Create: `../BrickFlowUI Landing/brickflowui-landing/e2e/landing.spec.ts`

**Interfaces:**
- Produces scripts `test`, `typecheck`, `test:e2e`, `test:all`, and project-local `vercel` CLI.
- Browser base URL is `http://127.0.0.1:3000`.

- [ ] **Step 1: Read the repository's bundled Next.js 16 App Router, metadata, font, image, and testing guides before editing.**

Read the relevant files under `node_modules/next/dist/docs/` as required by the landing repository's `AGENTS.md`. During execution, also load `design-taste-frontend`, `vercel:nextjs`, `vercel:vercel-cli`, and `vercel:agent-browser-verify` before their corresponding actions.

- [ ] **Step 2: Install and pin the test and Vercel CLI dependencies in the lockfile.**

Run from the landing repository:

```powershell
npm install --save-dev vitest jsdom @vitejs/plugin-react @testing-library/react @testing-library/jest-dom @testing-library/user-event @playwright/test @axe-core/playwright vercel
```

- [ ] **Step 3: Add the Vitest configuration and one intentionally failing identity test.**

```tsx
import { render, screen } from "@testing-library/react";
import Home from "@/app/page";

test("presents AgentMuru as a governed agent runtime", () => {
  render(<Home />);
  expect(screen.getByRole("heading", { name: /build agents you can see, steer, and trust/i })).toBeInTheDocument();
  expect(screen.queryByText(/BrickflowUI/i)).not.toBeInTheDocument();
});
```

- [ ] **Step 4: Run the test and confirm it fails against the legacy BrickFlowUI page.**

Run: `npm test -- --run`

- [ ] **Step 5: Configure scripts and Playwright without changing product components yet.**

```json
{
  "scripts": {
    "dev": "next dev --hostname 127.0.0.1",
    "build": "next build",
    "start": "next start --hostname 127.0.0.1",
    "lint": "eslint .",
    "typecheck": "tsc --noEmit",
    "test": "vitest",
    "test:e2e": "playwright test",
    "test:all": "npm run lint && npm run typecheck && npm test -- --run && npm run build && npm run test:e2e"
  }
}
```

- [ ] **Step 6: Commit the landing verification foundation.**

```powershell
git add package.json package-lock.json next.config.ts vitest.config.ts src/test playwright.config.ts e2e
git commit -m "test: establish AgentMuru landing verification"
```

### Task 2: Build the AgentMuru brand primitives and content contract

**Files:**
- Create: `../BrickFlowUI Landing/brickflowui-landing/src/content/site.ts`
- Create: `../BrickFlowUI Landing/brickflowui-landing/src/components/AgentMuruMark.tsx`
- Create: `../BrickFlowUI Landing/brickflowui-landing/src/components/AgentMuruLogo.tsx`
- Create: `../BrickFlowUI Landing/brickflowui-landing/src/components/AgentMuruLogo.test.tsx`
- Create: `../BrickFlowUI Landing/brickflowui-landing/public/agentmuru-mark.svg`
- Create: `../BrickFlowUI Landing/brickflowui-landing/public/agentmuru-logo.svg`
- Create: `../BrickFlowUI Landing/brickflowui-landing/public/favicon.svg`
- Modify: `../BrickFlowUI Landing/brickflowui-landing/src/app/globals.css`

**Interfaces:**
- Produces `siteContent` with `hero`, `proof`, `capabilities`, `persistence`, `qualification`, `limits`, and `links` records.
- Produces `<AgentMuruMark title?: string />` and `<AgentMuruLogo compact?: boolean />`.

- [ ] **Step 1: Write failing brand-component and content tests.**

```tsx
test("logo exposes the approved accessible product name", () => {
  render(<AgentMuruLogo />);
  expect(screen.getByLabelText("AgentMuru home")).toBeInTheDocument();
  expect(screen.getByText("Agent")).toBeInTheDocument();
  expect(screen.getByText("Muru")).toBeInTheDocument();
});
```

```ts
expect(siteContent.hero.headline).toBe("Build agents you can see, steer, and trust.");
expect(JSON.stringify(siteContent)).not.toMatch(/BrickflowUI/i);
```

- [ ] **Step 2: Run focused tests and confirm missing modules fail.**

Run: `npm test -- --run src/components/AgentMuruLogo.test.tsx`

- [ ] **Step 3: Implement flat Hybrid Vel Eye geometry and wordmark components.**

Use inline SVG paths with a viewBox shared by component and public assets. The mark uses exact solid brand colors and an accessible title when it stands alone. The wordmark renders `Agent` and `Muru` as separate spans so dark/light contexts can switch Near Black or white without changing the teal `Muru` treatment.

- [ ] **Step 4: Centralize verified product content.**

`siteContent` must contain only current claims: typed events, governed tools, approvals, sessions, artifacts, workflows, traces, Muru Workspace, in-memory state, SQLite persistence, deterministic FakeModel, optional Databricks adapters, and explicit planned provider/PostgreSQL work.

- [ ] **Step 5: Replace global tokens and type stacks.**

```css
:root {
  --teal: #0A7C7F;
  --cobalt: #0D5F8A;
  --gold: #C48A1F;
  --obsidian: #0D0F14;
  --mist: #F4F7FB;
  --ink: #111827;
  --muted: #64748B;
  --line: #E2E8F0;
}
```

- [ ] **Step 6: Run component tests, lint, and typecheck.**

Run: `npm test -- --run src/components/AgentMuruLogo.test.tsx`

Run: `npm run lint`

Run: `npm run typecheck`

- [ ] **Step 7: Commit brand primitives and content.**

```powershell
git add src/content src/components/AgentMuruMark.tsx src/components/AgentMuruLogo.tsx src/components/AgentMuruLogo.test.tsx src/app/globals.css public
git commit -m "feat: establish AgentMuru landing identity"
```

### Task 3: Implement the Precision Runtime landing page

**Files:**
- Create: `../BrickFlowUI Landing/brickflowui-landing/src/components/LandingPage.tsx`
- Create: `../BrickFlowUI Landing/brickflowui-landing/src/components/LandingPage.test.tsx`
- Rewrite: `../BrickFlowUI Landing/brickflowui-landing/src/components/Navbar.tsx`
- Rewrite: `../BrickFlowUI Landing/brickflowui-landing/src/components/Hero.tsx`
- Create: `../BrickFlowUI Landing/brickflowui-landing/src/components/RuntimeProof.tsx`
- Create: `../BrickFlowUI Landing/brickflowui-landing/src/components/CapabilityGrid.tsx`
- Create: `../BrickFlowUI Landing/brickflowui-landing/src/components/PersistenceStory.tsx`
- Create: `../BrickFlowUI Landing/brickflowui-landing/src/components/QualificationEvidence.tsx`
- Create: `../BrickFlowUI Landing/brickflowui-landing/src/components/Quickstart.tsx`
- Create: `../BrickFlowUI Landing/brickflowui-landing/src/components/HonestLimits.tsx`
- Rewrite: `../BrickFlowUI Landing/brickflowui-landing/src/components/CTA.tsx`
- Rewrite: `../BrickFlowUI Landing/brickflowui-landing/src/components/Footer.tsx`
- Rewrite: `../BrickFlowUI Landing/brickflowui-landing/src/app/page.tsx`
- Rewrite: `../BrickFlowUI Landing/brickflowui-landing/src/app/components.css`

**Interfaces:**
- `LandingPage` renders sections with IDs `proof`, `capabilities`, `persistence`, `qualification`, `quickstart`, and `limits`.
- Primary links point to `https://ajayaj2000.github.io/AgentMuru/` and `https://github.com/AjayAJ2000/AgentMuru`.

- [ ] **Step 1: Write failing page tests for hierarchy, claims, links, and limitations.**

```tsx
test("renders verified proof and honest limitations", () => {
  render(<LandingPage />);
  expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
    "Build agents you can see, steer, and trust."
  );
  expect(screen.getByText(/SQLite history survives process restart/i)).toBeInTheDocument();
  expect(screen.getByText(/Production model providers are planned/i)).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /read the docs/i })).toHaveAttribute(
    "href", "https://ajayaj2000.github.io/AgentMuru/"
  );
});
```

- [ ] **Step 2: Run the landing tests and confirm missing sections fail.**

Run: `npm test -- --run src/components/LandingPage.test.tsx`

- [ ] **Step 3: Implement the dark Precision Runtime hero and navigation.**

The hero has one headline, one concise supporting paragraph, `Install AgentMuru` and `Read the docs` actions, and a compact proof strip. It uses no floating card constellation, giant product name, excessive pill labels, or decorative animation.

- [ ] **Step 4: Implement Live Workspace proof as a semantic event timeline.**

Render a session rail and ordered events `agent.started`, `model.text.delta`, `approval.requested`, `tool.completed`, and `run.completed`. Use real accessible lists and labels rather than an image of an interface.

- [ ] **Step 5: Implement capabilities, persistence, qualification, quickstart, and limitations.**

Use three or four high-density sections, not a repeated card grid for every idea. The quickstart displays `python -m pip install agentmuru==0.2.0`, `muru doctor`, and `muru init my-agent`. Qualification evidence links to the documentation report.

- [ ] **Step 6: Wire the page and remove legacy page composition.**

```tsx
export default function Home() {
  return <LandingPage />;
}
```

- [ ] **Step 7: Run landing tests, lint, typecheck, and build.**

Run: `npm test -- --run`

Run: `npm run lint`

Run: `npm run typecheck`

Run: `npm run build`

- [ ] **Step 8: Commit the Precision Runtime page.**

```powershell
git add src/components src/app/page.tsx src/app/components.css
git commit -m "feat: launch AgentMuru Precision Runtime landing"
```

### Task 4: Replace metadata, social surfaces, and legacy files

**Files:**
- Rewrite: `../BrickFlowUI Landing/brickflowui-landing/src/app/layout.tsx`
- Rewrite: `../BrickFlowUI Landing/brickflowui-landing/src/app/manifest.ts`
- Rewrite: `../BrickFlowUI Landing/brickflowui-landing/src/app/sitemap.ts`
- Rewrite: `../BrickFlowUI Landing/brickflowui-landing/src/app/robots.ts`
- Create: `../BrickFlowUI Landing/brickflowui-landing/src/app/opengraph-image.tsx`
- Rewrite: `../BrickFlowUI Landing/brickflowui-landing/README.md`
- Delete: obsolete BrickFlowUI-only components and public logo assets after replacement tests pass.
- Test: `../BrickFlowUI Landing/brickflowui-landing/src/app/metadata.test.ts`

**Interfaces:**
- Canonical URL resolves from `NEXT_PUBLIC_SITE_URL` with `https://agentmuru.vercel.app` as production fallback.
- Open Graph image is 1200x630 and uses AgentMuru family tokens.

- [ ] **Step 1: Write failing metadata and legacy-identity tests.**

```ts
test("metadata names AgentMuru and its governed runtime category", () => {
  expect(metadata.applicationName).toBe("AgentMuru");
  expect(metadata.title).toMatch(/AgentMuru/);
  expect(metadata.description).toMatch(/observable, human-governed AI applications/i);
});
```

Add a repository scan assertion that no source, README, manifest, structured data, or public SVG contains `BrickflowUI` after migration.

- [ ] **Step 2: Run metadata tests and confirm legacy values fail.**

Run: `npm test -- --run src/app/metadata.test.ts`

- [ ] **Step 3: Implement metadata, structured data, sitemap, robots, manifest, and generated social image.**

Use `DM_Sans`, `Inter`, and `JetBrains_Mono` from `next/font/google`. Structured data describes a `SoftwareApplication` named AgentMuru and links only to the current GitHub and documentation URLs.

- [ ] **Step 4: Rewrite README with exact local checks and Vercel CLI deployment flow.**

Include `npm ci`, `npm run test:all`, `npx vercel whoami`, preview deployment, protected preview checking with `vercel curl`, production build, and promotion.

- [ ] **Step 5: Delete obsolete legacy components and assets after the new build passes.**

Remove only files no longer imported by `LandingPage`, plus BrickFlowUI logo/mark assets. Preserve generic framework files required by Next.js. Record the removed file list in the commit body.

- [ ] **Step 6: Run the full identity scan and build.**

Run: `rg -n -i "brickflowui|brickflow ui" src public README.md`

Expected: no results.

Run: `npm test -- --run`

Run: `npm run lint`

Run: `npm run typecheck`

Run: `npm run build`

- [ ] **Step 7: Commit metadata and legacy cleanup.**

```powershell
git add src public README.md
git commit -m "refactor: remove legacy BrickFlowUI landing identity"
```

### Task 5: Verify responsive, accessible, and reduced-motion behavior

**Files:**
- Modify: `../BrickFlowUI Landing/brickflowui-landing/e2e/landing.spec.ts`
- Modify: `../BrickFlowUI Landing/brickflowui-landing/src/app/globals.css`
- Modify: `../BrickFlowUI Landing/brickflowui-landing/src/app/components.css`

**Interfaces:**
- Browser suite covers desktop, 360px mobile, keyboard navigation, axe scan, reduced motion, and link integrity.

- [ ] **Step 1: Write failing browser assertions for the complete visitor path.**

```ts
test("landing is accessible and complete on desktop", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Build agents");
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.getByRole("link", { name: "Read the docs" }).focus();
  await expect(page.getByRole("link", { name: "Read the docs" })).toBeFocused();
});
```

- [ ] **Step 2: Start the production build locally and confirm browser tests expose remaining defects.**

Run: `npm run build`

Run: `npm run test:e2e`

- [ ] **Step 3: Fix only witnessed layout, contrast, focus, overflow, and motion defects.**

At 360px there must be no horizontal scroll. At `prefers-reduced-motion: reduce`, reveal and decorative motion are disabled. Focus indicators use a visible teal/cobalt outline with sufficient contrast.

- [ ] **Step 4: Run automated browser verification and inspect desktop/mobile screenshots.**

Run: `npm run test:e2e`

Use the browser verification skill against the local production server and inspect the hero, timeline, persistence section, quickstart, limitations, and footer at desktop and mobile widths.

- [ ] **Step 5: Run the full local landing gate and React best-practices review.**

Run: `npm run test:all`

Load `vercel:react-best-practices` after the multi-component TSX edit and address only findings that apply to this static landing page.

- [ ] **Step 6: Commit verified accessibility and responsiveness fixes.**

```powershell
git add e2e src/app src/components
git commit -m "test: verify AgentMuru landing experience"
```

### Task 6: Link, preview, verify, and promote with Vercel CLI

**Files:**
- Verify: `../BrickFlowUI Landing/brickflowui-landing/.vercel/project.json`
- Verify: `../BrickFlowUI Landing/brickflowui-landing/.vercel/output/`

**Interfaces:**
- Produces one verified preview URL and one verified production URL.

- [ ] **Step 1: Confirm CLI identity and project scope before linking.**

Run: `npx vercel whoami`

Run: `npx vercel teams ls`

Run: `npx vercel project ls`

If authentication is absent, use `npx vercel login`; do not create a duplicate project while identity or team scope is unknown.

- [ ] **Step 2: Link the landing directory to the existing AgentMuru project or create exactly one `agentmuru` project when none exists.**

Run: `npx vercel link --yes --project agentmuru`

Inspect `.vercel/project.json` and confirm the resolved project and organization IDs belong to the intended account.

- [ ] **Step 3: Pull preview configuration, build, and deploy a preview.**

Run: `npx vercel pull --yes --environment=preview`

Run: `npx vercel build`

Run this PowerShell block; Vercel writes the URL to stdout and progress to stderr:

```powershell
$previewDeploymentUrl = npx vercel deploy --prebuilt
npx vercel curl / --deployment $previewDeploymentUrl
Write-Output $previewDeploymentUrl
```

- [ ] **Step 4: Verify the protected preview through CLI and browser.**

Use the exact URL emitted by the preceding deploy block in the browser. Confirm status 200, AgentMuru metadata, no BrickFlowUI text, working docs/GitHub links, and desktop/mobile browser checks.

- [ ] **Step 5: Build the production target without assigning the domain, then verify it.**

Run: `npx vercel pull --yes --environment=production`

Run: `npx vercel build --prod`

Run this PowerShell block:

```powershell
$productionCandidateUrl = npx vercel deploy --prebuilt --prod --skip-domain
npx vercel curl / --deployment $productionCandidateUrl
npx vercel promote $productionCandidateUrl
npx vercel inspect $productionCandidateUrl
Write-Output $productionCandidateUrl
```

- [ ] **Step 6: Promote the verified candidate and inspect production.**

Re-run browser verification on the promoted production domain reported by Vercel and save that exact URL in the launch evidence.

### Task 7: Reset the AgentMuru roadmap and GitHub project

**Files:**
- Create: `docs/product/roadmap.md`
- Modify: `mkdocs.yml`
- External: GitHub issues and project for `AjayAJ2000/AgentMuru`

**Interfaces:**
- Produces outcome epic `Qualify AgentMuru with durable local persistence`.
- Produces queued outcomes `Add a production model-provider adapter` and `Add PostgreSQL persistence for multi-tenant deployments`.

- [ ] **Step 1: Write the repository roadmap from verified release outcomes.**

The roadmap contains Now, Next, and Later. Now is the completed 0.2 qualification/persistence milestone with links to evidence. Next is the production provider adapter. PostgreSQL follows it. Relevant Databricks identity, load, and observability outcomes remain later; component-catalog and VDOM-era outcomes are marked legacy.

- [ ] **Step 2: Create or update the outcome epic and implementation issues through the GitHub connector.**

Use the approved epic title and acceptance signals from the design spec. Add links to the persistence, qualification, documentation, landing, and release commits or pull requests. Close the implementation issues only after their verification evidence exists.

- [ ] **Step 3: Update legacy issues deliberately.**

Rewrite issues 43, 44, and 45 only where their outcomes remain valid for AgentMuru. Remove issues 47 through 52 from the active project view because their BrickFlowUI component/VDOM scope no longer matches the product; add a concise archival note instead of silently relabeling them as completed AgentMuru work.

- [ ] **Step 4: Update the GitHub Project using authenticated Projects tooling or the logged-in browser.**

Place the 0.2 epic in Done after verification, the provider-adapter issue in Next, the PostgreSQL issue behind it, and retained identity/load/observability outcomes in Later. Confirm the board visibly uses AgentMuru terminology.

- [ ] **Step 5: Build docs and commit the repository roadmap.**

Run: `python -m mkdocs build --strict`

```powershell
git add docs/product/roadmap.md mkdocs.yml
git commit -m "docs: reset the AgentMuru product roadmap"
```

### Task 8: Publish repositories, documentation, and release artifacts

**Files:**
- External: core `dev` branch, pull request to `main`, GitHub Pages, GitHub release, PyPI workflow.
- External: landing `main` branch and Vercel production project.

**Interfaces:**
- Produces a reviewed AgentMuru core PR, deployed documentation, a GitHub release tagged `agentmuru-v0.2.0`, and PyPI 0.2.0 only when trusted publishing succeeds.

- [ ] **Step 1: Run fresh final verification in both repositories.**

Core: run the complete commands from Documentation Plan Task 7.

Landing: run `npm run test:all`, confirm Vercel production status is READY, and verify the production URL.

- [ ] **Step 2: Publish the landing repository intentionally.**

Use `github:yeet` to inspect the exact landing diff, push the verified `main` commit to `AjayAJ2000/BrickFlowUI_Landing_Page`, and confirm the pushed SHA matches the deployed Vercel source state.

- [ ] **Step 3: Push core `dev`, open the PR, and wait for required checks.**

Use `github:yeet` to push `dev` and create a ready-for-review PR to `main` summarizing persistence, qualification, documentation, migration, and launch evidence. Confirm CI, CodeQL, docs, browser QA, and qualification checks.

- [ ] **Step 4: Merge the verified core PR and confirm documentation deployment.**

Use the GitHub connector with the expected head SHA and repository merge policy. Confirm the docs workflow publishes `https://ajayaj2000.github.io/AgentMuru/` and that persistence, cookbook, qualification, integration-status, and roadmap pages return successfully.

- [ ] **Step 5: Create the 0.2 GitHub release from the merged commit.**

Tag `agentmuru-v0.2.0`, attach the verified wheel and source distribution, and use release notes drawn from `docs/CHANGELOG.md` plus the qualification limitations.

- [ ] **Step 6: Trigger and verify trusted PyPI publication.**

Confirm the `publish.yml` run uses environment `pypi` and OIDC. If the trusted publisher is configured, verify `agentmuru==0.2.0` on PyPI and perform a fresh public install. If it is not configured, leave GitHub artifacts published, record the exact PyPI configuration blocker, and do not claim PyPI success.

### Task 9: Perform final end-to-end product verification

**Files:**
- Verify: deployed landing page, hosted docs, GitHub roadmap/project, GitHub release, and package installation surface.

**Interfaces:**
- Produces final evidence for every user-requested end goal.

- [ ] **Step 1: Start from the public landing page and follow the primary visitor journey.**

Confirm the production landing loads, installation copy is correct, docs and GitHub links resolve, qualification evidence is reachable, and no BrickFlowUI public identity remains.

- [ ] **Step 2: Install from the strongest available public artifact.**

Use PyPI `agentmuru==0.2.0` when publication succeeded; otherwise download the attached GitHub release wheel. Run `muru doctor`, scaffold an application, execute the durable scenario, stop it, restart it, and confirm history remains visible.

- [ ] **Step 3: Inspect GitHub release and project state.**

Confirm the release tag and assets match the merged commit, the 0.2 epic is Done, the provider adapter is Next, PostgreSQL follows it, and retained Later outcomes use AgentMuru language.

- [ ] **Step 4: Record every external limitation explicitly.**

List credential-dependent Databricks checks, Vercel account/domain constraints, GitHub Project permission limits, GitHub Pages status, release attachment status, and PyPI trusted-publisher status using observed evidence.

- [ ] **Step 5: Stop the brainstorming companion and leave both repositories clean except for intentionally ignored build outputs.**

Run the visual-companion stop script against `.superpowers/brainstorm/1414-1786259940`, then confirm `git status --short` in the core and landing repositories.
