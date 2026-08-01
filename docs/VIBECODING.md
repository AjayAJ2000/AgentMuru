# Vibe Coding Skills

BrickflowUI works especially well with modern AI coding tools when the assistant is given a clear product shape and a few framework-specific guardrails.

This page collects the repo-local skill files we ship for that purpose.

## Start here first

The canonical high-context guide for AI tools is:

- [`SKILL.md`](https://github.com/AjayAJ2000/brickflowUI/blob/main/SKILL.md) at the repo root

That file is the authoritative reference for:

- the runtime mental model
- state and event handling
- component usage
- page composition
- loading, theming, and deployment expectations

The smaller skill files under `skills/` should be treated as focused overlays,
not replacements for the root guide.

## Why this matters

Generic "build me a dashboard" prompts often produce one of two bad outcomes:

- notebook-style pages with weak product structure
- generic frontend advice that ignores BrickflowUI's Python-first runtime

The skills in `skills/` keep the assistant closer to the framework's real strengths: data and AI portals, internal tools, branded shells, smoother controls, and Databricks-aware delivery.

## Included skills

| Skill | Path | Best for |
|---|---|---|
| BrickflowUI App Starter | [`skills/brickflowui-app-starter/SKILL.md`](https://github.com/AjayAJ2000/brickflowUI/blob/main/skills/brickflowui-app-starter/SKILL.md) | Starting new apps from the right example and keeping structure clean |
| BrickflowUI Data + AI Portal | [`skills/brickflowui-data-ai-portal/SKILL.md`](https://github.com/AjayAJ2000/brickflowUI/blob/main/skills/brickflowui-data-ai-portal/SKILL.md) | Dashboards, copilots, pipeline command centers, and analytics workspaces |
| BrickflowUI Geometric UI | [`skills/brickflowui-geometric-ui/SKILL.md`](https://github.com/AjayAJ2000/brickflowUI/blob/main/skills/brickflowui-geometric-ui/SKILL.md) | Glassmorphism, geometric product layouts, visual showcases, and image-led premium surfaces |
| BrickflowUI Polish + QA | [`skills/brickflowui-polish-and-qa/SKILL.md`](https://github.com/AjayAJ2000/brickflowUI/blob/main/skills/brickflowui-polish-and-qa/SKILL.md) | Responsiveness, loading, spacing, interaction quality, and release polish |
| BrickflowUI Databricks Delivery | [`skills/brickflowui-databricks-delivery/SKILL.md`](https://github.com/AjayAJ2000/brickflowUI/blob/main/skills/brickflowui-databricks-delivery/SKILL.md) | Packaging, deployment, managed-platform handoff, and enterprise delivery review |

## Recommended workflow

1. Read the repo-root `SKILL.md`.
2. Pick the closest real example from `examples/`.
3. Start with `skills/brickflowui-app-starter/SKILL.md`.
4. Move to the domain skill that fits the app shape.
5. If the app is highly design-led, add `skills/brickflowui-geometric-ui/SKILL.md`.
6. Finish with `skills/brickflowui-polish-and-qa/SKILL.md`.
7. Use `skills/brickflowui-databricks-delivery/SKILL.md` before shipping or demoing to a platform team.

## End-user priority

When you ask an AI tool to work inside BrickflowUI, it should optimize for these people first:

1. data platform teams
2. AI application teams
3. analytics engineers
4. internal tools teams
5. enterprise evaluators deciding whether the framework can support a real rollout

That priority matters because it changes the kind of app the assistant should build:

- less widget collage
- more operator clarity
- stronger shell and workflow structure
- honest loading and governance behavior
- more realistic examples and demos

## What a strong BrickflowUI agent should know

A strong BrickflowUI-oriented AI assistant should understand:

- the root `SKILL.md` is the main source of truth
- the app shell comes before the chart set
- controls must change visible state
- images and media are legitimate first-class surfaces, not decoration
- loading and empty states are part of the product contract
- examples are part of the framework quality bar
- dark and light modes both matter
- geometry-heavy or editorial designs should still remain maintainable and state-safe

## BrickflowUI-specific design rules

### For dashboard and portal work

- Start with `Hero`, `SectionHeader`, `Sidebar`, `TopNav`, `Card`, `Grid`, and `Table`.
- Use `StatusStrip`, `GaugeChart`, `Timeline`, and `PipelineGraph` when the page needs operator understanding, not just KPI display.
- Keep the fold readable in under five seconds.

### For visual showcase or geometry-heavy work

- Prefer image-led composition over trying to fake premium art with plain boxes.
- Use rounded shells, pill actions, and calm gradients deliberately.
- Document any missing primitive honestly instead of hiding it in brittle CSS hacks.
- If the design is driven by one hero image, make it large enough to dominate the fold.

### For AI/copilot work

- Keep chat and support telemetry close together.
- Use drawers, timelines, and tables as explanation layers.
- Avoid making the chat pane the only source of truth if structured data is available.

## Prompt patterns that produce stronger results

### Product-grade portal

```text
Use the BrickflowUI app starter and data + AI portal skills. Start from the closest repo example, keep the shell product-grade, add real loading states, and make every filter visibly change a chart, table, or workflow surface.
```

### Premium design-led surface

```text
Use the BrickflowUI geometric UI skill. Build a premium glassmorphism showcase in pure Python, prefer local SVG assets for hero art, keep the interactions real, and document any framework primitives that should become first-class for pixel-perfect fidelity.
```

### Release-quality pass

```text
Use the BrickflowUI polish + QA skill. Audit this app like an enterprise evaluator: responsiveness, dark/light parity, empty/loading states, control smoothness, and example honesty all matter more than adding new components.
```

## Example prompts

### Build a data platform portal

```text
Use skills/brickflowui-data-ai-portal/SKILL.md and adapt examples/data_pipeline_command_center/app.py into a multi-page portal for data and AI teams. Keep the shell product-grade, add KPI cards, a pipeline graph, cost view, and an operations table.
```

### Start from the best baseline

```text
Use skills/brickflowui-app-starter/SKILL.md and tell me which existing example is the best baseline for a secure internal AI operations workspace. Then implement the first working page.
```

### Polish before demo day

```text
Use skills/brickflowui-polish-and-qa/SKILL.md and tighten this app for a buyer demo: smooth inputs, loading states, better spacing, mobile fixes, and more product-grade empty states.
```

### Prepare for Databricks

```text
Use skills/brickflowui-databricks-delivery/SKILL.md and make this app deployment-ready for Databricks Apps with a mock-data fallback and packaging checks.
```

### Build a geometric concept surface

```text
Use skills/brickflowui-geometric-ui/SKILL.md and adapt examples/geometric_signal_lab/app.py into a premium showcase surface that feels like a real product concept, not a dashboard disguised as one.
```

## Best practice

Whenever possible, ask the assistant to **adapt a real example** instead of generating a new app from scratch. That keeps the output closer to the framework's proven patterns and lowers the chance of drifting into a generic web-app shape that BrickflowUI does not need.

## Validation expectation

For serious BrickflowUI work, a good AI assistant should not stop at code generation. It should also:

- smoke-run the touched example locally
- check theme and loading behavior conceptually
- keep docs and examples aligned with the shipped API
- avoid promoting weak or fake-looking examples
- explain the tradeoffs when a design requires capabilities that are not yet first-class
