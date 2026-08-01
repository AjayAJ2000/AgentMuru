# BrickFlowUI End-User Framework QA

## Verdict

```text
Verdict: LOCAL RELEASE GATES PASS; LIVE DATABRICKS VALIDATION STILL REQUIRED
Date: 2026-08-01 (hardening follow-up)
Branch: dev
Environment: Windows, Python 3.13.1, Node 24.18.0, npm 11.16.0
Local critical defects remaining: 0 known reproducible defects
Local high defects remaining: 0 known reproducible defects
```

BrickFlowUI was tested as both a maintainer and a first-time user. The source suites, frontend build, strict documentation, generated component references, package artifacts, isolated wheel install, CLI scaffolding, generated application runtime, browser interaction, accessibility checks, responsive layout, bounded concurrency, and all repository examples passed.

The original CLI presentation defect and the hardening defects described below were repaired test-first.

## User journey exercised

1. Built the production React runtime.
2. Built the `0.1.13` wheel and source distribution.
3. Installed the wheel into an isolated virtual environment.
4. Ran the installed `brickflowui --help` command.
5. Scaffolded a new project with the installed `brickflowui new` command.
6. Started the generated app from the isolated environment.
7. Loaded it in the in-app browser.
8. Used the counter and observed `Current count: 0` change to `Current count: 1`.
9. Reloaded at `390x844` and verified the document remained exactly 390 pixels wide.
10. Inspected native button semantics, browser warnings/errors, and the live server-driven update path.

Accepted browser captures are stored in:

- `.tmp/end-user-qa/02-counter-incremented.png`
- `.tmp/end-user-qa/03-scaffold-mobile.png`

The initial full-page capture was rejected because the browser capture itself distorted the image. Live DOM measurements and a normal viewport capture confirmed that the page, card, row, and alert all used their expected full widths.

## Defect repaired

### CLI-001: renderer markup leaked into terminal output

**Severity:** Low

**Reproduction:**

```text
brickflowui new scaffold
brickflowui dev --no-reload
```

**Before:** The commands printed literal strings including `[bold]`, `[/bold]`, `[bold green]`, and `[/bold green]`.

**Root cause:** The Typer application enabled Rich markup for its help renderer, while the application messages were passed through `typer.echo`, which emits plain text and does not interpret Rich markup.

**Repair:** The two plain terminal messages now contain clean text while preserving their existing guidance and URLs.

**Regression coverage:**

- `test_new_command_renders_success_message_without_markup`
- `test_dev_command_renders_banner_without_markup`

The tests were observed failing for the literal tags before the implementation changed, then passed after the minimal repair.

## Hardening follow-up

The 2026-08-01 follow-up added permanent release gates and repaired defects they exposed:

- Python CI now runs on 3.10, 3.11, 3.12, and 3.13.
- Browser reconnect retries use one cancellable exponential-backoff controller.
- WebSocket cleanup, repeated reconnects, state isolation, and concurrent authenticated principals have regression coverage.
- A bounded real-runtime campaign completes 60 state-changing events across 20 sessions and 40 reconnects.
- Production chunks have enforced byte budgets in CI and the publish workflow.
- Playwright and Axe exercise the packaged counter and component studio on desktop and mobile Chromium.
- Input, Select, DateRangePicker, and Slider labels are programmatically associated; dialogs and tabs expose native accessibility semantics; badge and active-chip contrast meets the tested Axe thresholds.
- Incremental patches now serialize VNodes nested in changed props before JSON encoding.
- Browser QA pins Python imports to the checkout, preventing an older global installation from masking source changes.
- A read-only two-profile Databricks evidence harness and operator runbook are available for the remaining external gate.

## Verification results

| Gate | Result |
| --- | --- |
| Python | 110 passed |
| Frontend unit tests | 18 passed across 7 files |
| Bundle-gate unit tests | 2 passed |
| Playwright end-user tests | 3 passed |
| Frontend lint | passed |
| TypeScript | passed |
| npm audit | 0 vulnerabilities |
| Vite production build | passed; 2,194 modules transformed |
| Runtime resilience | 20 sessions, 60 events, 40 reconnects, 0 failures |
| Bundle budgets | index 793,641; charts 1,043,247; Plotly 7,213,372; vendor 227,749 bytes |
| Automated accessibility | 0 serious/critical Axe violations in tested flows |
| Strict MkDocs build | passed |
| Generated component reference drift | no drift |
| Example startup sweep | 17 of 17 passed |
| Wheel and source distribution | built successfully |
| Twine metadata check | wheel and source distribution passed |
| Wheel/frontend consistency | 10 source assets; 0 wheel mismatches |
| Installed CLI output | clean; no literal Rich tags |
| Browser console | 0 warning/error entries |
| Desktop interaction | counter changed from 0 to 1 |
| Mobile viewport | 390 client width; 390 scroll width |

## Exact release checks

```text
python -m pytest -q -p no:cacheprovider
npm --prefix frontend test -- --run
npm --prefix frontend run lint
npm --prefix frontend run typecheck
npm --prefix frontend audit --audit-level=high
npm --prefix frontend run build
npm --prefix frontend run test:bundle
npm --prefix frontend run check:bundle
npm --prefix frontend run test:e2e
python scripts/runtime_resilience.py
python scripts/generate_component_reference.py
git diff --exit-code -- docs/components/reference
python -m mkdocs build --strict -d .tmp/end-user-qa/final-site
python scripts/smoke_examples.py
python -m build --outdir .tmp/end-user-qa/dist
python -m twine check .tmp/end-user-qa/dist/*
```

## Preserved pre-existing work

The uncommitted changes already present in these files were not overwritten:

- `brickflowui/vdom.py`
- `tests/test_vdom.py`

They were preserved and included in the passing 110-test result.

## Remaining evidence limits

- No authenticated Databricks Apps workspace was available. OAuth consent, app/user authorization, requested scopes, resource permissions, Unity Catalog policies, SQL warehouse access, Jobs execution, and platform routing remain external checks.
- Only Python 3.13.1 was available locally. Python 3.10, 3.11, and 3.12 remain CI-matrix responsibilities.
- A bounded concurrency/reconnect campaign passed, but no sustained load, multi-process, WebSocket backpressure, or long-session memory campaign was run.
- All 17 examples were boot-checked; automated browser interaction focuses on the counter and component studio rather than every example.
- Keyboard focus and serious/critical Axe findings were checked in Chromium. This is not a formal WCAG conformance audit and does not cover Firefox or WebKit.
- The optional Plotly chunk remains approximately 7.2 MB uncompressed. It is below the enforced 7.5 MB ceiling but remains a performance watch item.

## Recommended next actions

1. Deploy this exact artifact to a non-production Databricks Apps workspace and test two simultaneous users with different permissions.
2. Keep Python 3.10–3.13, frontend tests, strict docs, package build, and generated-reference drift as required CI checks.
3. Run a sustained, multi-process load and long-session memory campaign before claiming high-concurrency production readiness.
4. Add Firefox/WebKit coverage when cross-browser support becomes part of the release contract.

No package was published, no release was created, no commit was pushed, and no deployment was performed.
