# BrickflowUI AI Skill Pack

This folder is not the primary source of truth.

The canonical, high-context reference for AI coding tools is:

- [SKILL.md](D:\Projects\brickflowUI\brickflowUI\SKILL.md)

That root file explains:
- the BrickflowUI runtime model
- state and event rules
- component usage patterns
- dashboard and portal composition
- data, auth, theming, loading, and deployment expectations

The skill files in `skills/` should be treated as **specialized overlays** on
top of that root guide.

## How to use this skill pack correctly

For any serious BrickflowUI work:

1. Read the repo-root `SKILL.md` first.
2. Choose the closest real example from `examples/`.
3. Load the most relevant focused skill from this folder.
4. Build or refactor the app.
5. Finish with the polish and validation skill.

If an AI agent skips step 1, it will usually drift into generic UI advice,
weak state handling, or example-incompatible structure.

## End users to optimize for

The priority order is:

1. data platform teams
2. AI application teams
3. analytics engineering teams
4. internal tools teams
5. enterprise evaluators

This matters because BrickflowUI should not default to toy demos, notebook
layouts, or frontend-framework cargo culting. It should default to product
surfaces that a serious team can extend and deploy.

## Included skills

| Skill | Folder | Use it when |
|---|---|---|
| BrickflowUI App Starter | `skills/brickflowui-app-starter/` | Starting or restructuring an app and choosing the right example, shell, and workflow shape |
| BrickflowUI Data + AI Portal | `skills/brickflowui-data-ai-portal/` | Building data/AI workspaces, command centers, analytics portals, copilots, and ops surfaces |
| BrickflowUI Geometric UI | `skills/brickflowui-geometric-ui/` | Building premium geometric, glassmorphism, editorial, and image-led surfaces |
| BrickflowUI Polish + QA | `skills/brickflowui-polish-and-qa/` | Tightening responsiveness, interaction quality, loading, theming, and release polish |
| BrickflowUI Databricks Delivery | `skills/brickflowui-databricks-delivery/` | Preparing apps for packaging, managed deployment, Databricks Apps, and enterprise handoff |

## Recommended skill order

For most application work:

1. `brickflowui-app-starter`
2. `brickflowui-data-ai-portal`
3. `brickflowui-geometric-ui` only if the surface is highly design-led
4. `brickflowui-polish-and-qa`
5. `brickflowui-databricks-delivery` before release, demo, or platform handoff

## What a strong BrickflowUI agent should do

- start from a real example, not a blank file, unless there is a good reason not to
- build the shell and interaction model before filling the page with visuals
- ensure every control changes visible state
- keep loading, empty, error, and success feedback explicit
- preserve a clean path to auth, governance, and deployment
- verify examples locally before promoting them
- update docs when the implementation meaningfully changes what the framework can prove
- document missing framework primitives honestly instead of hiding limitations in brittle hacks

## What a weak BrickflowUI agent tends to do

- stack cards and charts without establishing a real page shell
- create fake interactivity
- ignore loading behavior
- treat dark mode, mobile, and operator workflows as afterthoughts
- use charts decoratively
- generate new examples that look worse than the repo examples already available
- present landing-page visuals or concept pages as if they were the best proof of framework capability

## Validation baseline

For non-trivial BrickflowUI work, an AI tool should usually finish with:

```bash
python scripts/smoke_examples.py
python -m pytest -q tests/test_examples.py tests/test_app_server.py
python -m mkdocs build --strict -d .site_validation_local
cd frontend
npx tsc --noEmit
```

If the environment blocks full packaging or frontend build steps, the agent
should say so clearly and use the bounded validation path instead of pretending
the build passed.
