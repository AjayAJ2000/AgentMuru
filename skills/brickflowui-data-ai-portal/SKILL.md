# BrickflowUI Data + AI Portal

## Use this skill when

Use this skill when the target surface is an operational portal, analytics
workspace, pipeline command center, AI copilot shell, or governed internal
application for data and AI teams.

Read the repo-root [SKILL.md](D:\Projects\brickflowUI\brickflowUI\SKILL.md)
first. This file is the focused overlay for domain-specific structure,
information architecture, and quality rules.

## Mission

Push the agent beyond "build a dashboard" into "build a credible internal
product."

The resulting app should:

- answer the operator's most important questions quickly
- connect filters to visible state changes
- support drilldowns and action paths
- stay compatible with auth, governance, and managed deployment
- feel more like a SaaS workspace than a notebook wrapper

## Primary users

Optimize for:

1. data platform teams
2. AI application teams
3. analytics engineers
4. operations teams
5. enterprise evaluators

## First questions to answer

Before generating UI, answer these in plain terms:

1. What does the operator need to know right now?
2. What changed recently?
3. What needs action?
4. What needs drilldown?
5. What does leadership need to see that operators do not?

## Component mapping by operator need

- current health -> `Hero`, `StatusStrip`, `Stat`, `GaugeChart`
- change over time -> `AreaChart`, `LineChart`, `ComposedChart`, `Timeline`
- where the issue lives -> `Table`, `Heatmap`, `PipelineGraph`, `KanbanBoard`
- next action -> `Drawer`, `Modal`, `Toast`, `Alert`, `Stepper`
- AI explanation -> `ChatMessage`, `ChatInput`, supporting metrics, timeline, and structured evidence surfaces

## Best starting examples

Choose among:

- `examples/data_pipeline_command_center/app.py`
- `examples/acme_analytics_command_center/app.py`
- `examples/workspace_studio/app.py`
- `examples/clinical_trial_command_center/app.py`
- `examples/secure_internal_tools/app.py`

Use `examples/geometric_signal_lab/app.py` only when the page is supposed to be
visually premium and image-led, not when the main need is operator density.

## Information architecture

For most data and AI portals, organize the page in this order:

1. identity and scope
2. health summary
3. decision visuals
4. workflow detail
5. action surface

That usually becomes:

1. `Hero` or `SectionHeader`
2. KPI strip or KPI grid
3. filters and control bar
4. charts / workflow visuals
5. table / queue / feed
6. drawer / modal / follow-up surface

## Shell guidance

### Executive analytics portal

Use:
- `Hero`
- KPI grid
- 2 to 4 charts
- one summary table
- one drilldown surface

### Pipeline command center

Use:
- `Sidebar`
- `StatusStrip`
- `PipelineGraph`
- reliability / freshness charts
- incident table
- detail drawer

### AI workspace

Use:
- `Sidebar` or `TopNav`
- chat column
- nearby structured evidence
- timeline and source breakdown
- performance or operations cards

### Secure internal tool

Use:
- multipage shell
- role-aware navigation
- explicit action history
- drilldown and acknowledgement flows

## Data rules

- Every filter must drive a visible outcome.
- Every chart must answer a user question.
- Every table must support a next step: drilldown, export, acknowledge, or navigate.
- Avoid "status theater" where badges say things are live but nothing actually changes.
- Be honest about mock data vs live data.

## Performance rules

- Do not overload the fold with too many charts.
- Prefer a shared control plane rather than many uncoordinated filters.
- Use tabs or section switching when there are many heavy panels.
- Keep text-heavy filters debounced.
- Use `loading`, `empty_message`, and `error_message` intentionally.

## UX and design rules

- The fold should be legible in five seconds.
- The most important chart or workflow visual should be visually dominant.
- Use whitespace to separate jobs, not just component groups.
- Avoid tiny unreadable KPI cards.
- Mixed tables, graphs, and cards must feel like one product surface.
- Dark and light modes both matter.

## Governance and trust rules

- If the app is auth-aware, show only role-relevant navigation and sections.
- If the example uses mocked or sampled data, say so clearly.
- If actions are simulated, the copy should reflect that honestly.
- If a demo cannot run truthfully in a public surface, do not fake it.

## Validation

Before calling the portal complete:

```bash
python scripts/smoke_examples.py
python -m pytest -q tests/test_examples.py tests/test_app_server.py
```

Then run the specific touched example and check:

- filter behavior
- loading behavior
- drilldown path
- dark/light sanity

## Anti-patterns

- Do not build a chart gallery with no action model.
- Do not hide important detail only in prose when structured data exists.
- Do not treat governance as a docs-only concern.
- Do not add more visuals when the real issue is weak information architecture.
- Do not optimize for screenshots over real operator flows.

## Prompt shapes

- "Use the BrickflowUI data and AI portal skill to build a data platform command center with real operator questions, filter-driven charts, and a row drilldown drawer."
- "Create a governed AI workspace in BrickflowUI that combines chat, telemetry, and evidence surfaces without becoming a widget collage."
- "Turn this metrics list into a serious BrickflowUI portal for data and AI teams, with believable shell, action paths, and loading behavior."

## Done means

- the app looks like a product surface
- users can answer the main operator questions quickly
- controls, charts, and tables are tied together
- drilldowns exist
- the app has a plausible path to auth, governance, and deployment
