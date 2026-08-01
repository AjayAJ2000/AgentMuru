# BrickflowUI Databricks Delivery

## Use this skill when

Use this skill when preparing a BrickflowUI app for Databricks Apps, internal
managed deployment, packaging review, or enterprise handoff.

Read the repo-root [SKILL.md](D:\Projects\brickflowUI\brickflowUI\SKILL.md)
first. This file is the deployment and delivery overlay.

## Mission

Make the agent think like a platform engineer who is responsible for both:

- developer ergonomics
- deployment trust

The app should behave like a Python service with a packaged frontend, not a
local-only toy.

## Delivery priorities

- packaged frontend assets must exist and be current
- the example must boot from `python app.py`
- version, docs, templates, and examples must stay aligned
- loading, branding, and media behavior must survive packaging
- auth assumptions must be explicit
- the app should remain demoable with mock data if live infra is unavailable

## Required preload

Before working, inspect:

1. repo-root `SKILL.md`
2. `docs/DATABRICKS_APPS.md`
3. `docs/TROUBLESHOOTING.md`
4. the target example's `app.py`, `requirements.txt`, and any `app.yaml`

## Delivery workflow

1. Start from the closest deployment-ready example.
2. Verify `app.py`, `requirements.txt`, and deployment files are coherent.
3. Check that packaged frontend assets exist under `brickflowui/frontend/dist/`.
4. Review loading, logo, media, and asset paths.
5. Confirm port handling is runtime-aware, not hardcoded.
6. Document auth and governance assumptions clearly.
7. Run validation before claiming readiness.

## Packaging rules

- Treat the packaged frontend as part of the product contract.
- Rebuild frontend assets when frontend source changes.
- Keep version references aligned across package, docs, examples, and scaffolds.
- Do not claim packaging success based only on editable install behavior.

## Databricks-aware rules

- Use `DATABRICKS_APP_PORT` or runtime-resolved ports, never fixed local ports.
- Prefer mock-to-live handoff patterns for examples.
- Keep secrets out of repo examples.
- Be explicit about CSP, iframe, and auth-header assumptions.
- If an example cannot run honestly in a public or marketing surface, say so.

## Auth and governance rules

- If the app expects auth headers, document them.
- If the app is role-aware, describe what roles or scopes are required.
- Do not promote governed examples as "works anywhere" examples without caveats.
- Keep secure examples honest even when using demo data.

## Validation path

Preferred full path:

```bash
python -m build
python scripts/smoke_examples.py
python -m pytest -q tests/test_examples.py tests/test_app_server.py
python -m mkdocs build --strict -d .site_validation_local
cd frontend
npm run build
```

Bounded fallback when the machine blocks full builds:

```bash
python scripts/smoke_examples.py
python -m pytest -q tests/test_examples.py tests/test_app_server.py
python -m mkdocs build --strict -d .site_validation_local
cd frontend
npx tsc --noEmit
```

If using the fallback, say clearly that it is bounded validation, not a full
release build.

## Anti-patterns

- do not assume packaged assets are current without checking
- do not ship examples with hardcoded ports
- do not hide auth requirements
- do not rely on local-only paths or media without checking how BrickflowUI serves them
- do not claim enterprise readiness without validation evidence

## Prompt shapes

- "Use the BrickflowUI Databricks delivery skill and prepare this example for Databricks Apps with mock fallback, packaged assets, and explicit auth/runtime assumptions."
- "Review this BrickflowUI portal like a platform team would before allowing it into a managed environment."
- "Turn this local BrickflowUI app into a deployable surface without drifting away from the packaged runtime."

## Done means

- the app boots locally
- packaging assumptions are explicit
- assets and loading survive packaging
- versioning is aligned
- the platform team would not be surprised by hidden runtime constraints
