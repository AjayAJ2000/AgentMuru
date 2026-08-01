# Build A Real Portal

This tutorial is for engineers and evaluation teams who want to understand how BrickflowUI feels when used to build a serious internal product, not just a toy demo.

By the end, you should be able to design a multi-page portal with:

- responsive navigation
- controlled inputs and filters
- tables, charts, and pipeline views
- media surfaces
- auth-aware page structure
- theme-driven branding
- custom routes and form actions
- Databricks-ready deployment structure

## The Target

We are going to think like a SaaS team building a platform portal. The finished app should feel like one product with several jobs:

- an executive dashboard for high-level signals
- an operations view for tables, exports, and drilldowns
- a pipeline view for DAG-style runtime visibility
- an assistant workspace for guided investigation
- a secure admin surface for privileged actions

That is the right mental model for BrickflowUI. It is not only a dashboard library. It is a Python-first app framework for structured internal web products.

## Step 1: Start With The Shell

Create the app, define your theme, and choose your loading experience.

```python
from pathlib import Path
import brickflowui as db

app = db.App(
    title="Platform Control Center",
    theme={
        "branding": {"title": "Platform Control Center"},
        "colors": {
            "primary": "#0F766E",
            "surface": "#FFFFFF",
            "background": "#F6FBFA",
            "text": "#0F172A",
            "text_muted": "#475569",
            "border": "#D6E6E4",
        },
    },
    loading={
        "title": "Platform Control Center",
        "message": "Preparing the portal runtime...",
        "animation": "pulse",
    },
)
```

Why this matters:

- `App(...)` is where the global product frame starts
- `theme` controls the long-lived brand language
- `loading` now controls the first impression before the websocket connects

## Step 2: Model The Pages

Think in routes, not giant monolith functions.

```python
@app.page("/", title="Overview", icon="LayoutDashboard")
def overview():
    ...

@app.page("/pipeline", title="Pipeline", icon="GitBranch")
def pipeline():
    ...

@app.page("/assistant", title="Assistant", icon="Sparkles")
def assistant():
    ...
```

If you register more than one page, BrickflowUI automatically wraps your content with the app shell and sidebar.

## Step 3: Build Reusable View Helpers

Do not let page functions become one thousand lines long. Create helper functions for repeated surfaces.

```python
def metric_card(label: str, value: str, delta: str, delta_type: str) -> db.VNode:
    return db.Card(
        [
            db.Stat(label=label, value=value, delta=delta, delta_type=delta_type),
        ],
        hover=True,
        animated=True,
    )
```

This is one of the biggest skill shifts with BrickflowUI: treat your UI as a composed Python tree.

## Step 4: Add Controlled Filters

Controlled inputs are how serious portals stay predictable.

```python
@app.page("/", title="Overview")
def overview():
    query, set_query = db.use_state("")
    team, set_team = db.use_state("platform")
    urgent_only, set_urgent_only = db.use_state(False)

    return db.Card(
        [
            db.Input("query", label="Search", value=query, on_change=set_query),
            db.Select(
                "team",
                label="Team",
                value=team,
                on_change=set_team,
                options=[
                    {"label": "Platform", "value": "platform"},
                    {"label": "Operations", "value": "operations"},
                ],
            ),
            db.Checkbox("urgent", "Only urgent", checked=urgent_only, on_change=set_urgent_only),
        ]
    )
```

What changed recently and why it matters:

- falsy values like `False` and `""` now round-trip correctly
- users can check and uncheck controls without UI drift
- text inputs can safely become empty strings without getting stuck

## Step 5: Add High-Signal Surfaces

A good portal gives several levels of detail on one screen.

```python
db.Grid(
    [
        metric_card("Freshness", "9 min", "-2 min", "decrease"),
        metric_card("Success Rate", "98.7%", "+0.4%", "increase"),
        metric_card("Cost", "$4.2k", "-3.1%", "decrease"),
    ],
    cols=3,
)
```

Then layer in:

- `Table` for structured detail
- `StatusStrip` for compact operational signals
- `Timeline` for event narration
- `Badge` and `Alert` for focused context

## Step 6: Add Charts And Pipeline Views

Most enterprise portals need more than one visual grammar.

Recommended pattern:

- `ComposedChart` for throughput plus SLA
- `Heatmap` for failures across time and domain
- `GaugeChart` for readiness or quality
- `PipelineGraph` for DAG-like mental models
- `Plot` when you need full Plotly power

```python
db.Grid(
    [
        db.Card([
            db.ComposedChart(
                trend_rows,
                x_key="week",
                bar_keys=["runs"],
                line_keys=["success_rate"],
                title="Runs vs success rate",
            )
        ]),
        db.Card([
            db.PipelineGraph(nodes, edges, title="Pipeline topology")
        ]),
    ],
    cols=2,
)
```

## Step 7: Add Workflow Components

Many internal products are only partly dashboards. The rest is workflow.

Use:

- `Drawer` for detail without leaving context
- `Popup` for lightweight confirmations
- `Modal` for heavier task flows
- `KanbanBoard` for issue triage
- `Stepper` for release or onboarding stages
- `ChatMessage` and `ChatInput` for assistant surfaces

Example:

```python
detail_open, set_detail_open = db.use_state(False)

db.Button("Open details", on_click=lambda: set_detail_open(True))

db.Drawer(
    visible=detail_open,
    title="Runtime detail",
    on_close=lambda: set_detail_open(False),
    children=[
        db.Text("Show evidence, logs, sources, or operator guidance here."),
    ],
)
```

## Step 8: Add Media

You can now render images, GIFs, and videos directly from Python.

```python
db.Image("assets/architecture.png", alt="Architecture", caption="Local files are served automatically.")

db.Video(
    "assets/demo.mp4",
    caption="Product walkthrough",
    controls=True,
)
```

Why this is useful:

- onboarding walkthroughs
- architecture diagrams
- product demos
- clinical or manufacturing process explainers
- richer landing pages

## Step 9: Add Auth And Governance

For serious internal tools, build page boundaries early.

```python
app = db.App(
    auth_mode="user",
    auth_provider=db.HeaderAuthProvider(),
    allow_anonymous=False,
)

@app.page("/admin", title="Admin", access="user", roles=["admin"])
def admin():
    return db.Text("Restricted admin view")
```

This lets you separate:

- public product pages
- authenticated workspaces
- admin views
- data-governance or security review pages

## Step 10: Add Forms And Backend Actions

Use `Form` for simple JSON posting to your own route.

```python
@app.route("/api/action-plan", methods=["POST"])
async def create_action_plan(request):
    payload = await request.json()
    return {"status": "ok", "summary": payload.get("summary")}

db.Form(
    [
        db.Input("owner", label="Owner"),
        db.Input("summary", label="Summary"),
        db.Button("Create plan", html_type="submit"),
    ],
    action="/api/action-plan",
    method="POST",
    reload_on_success=True,
)
```

## Step 11: Design For Mobile Early

The current library is now substantially better on mobile, but good app structure still matters.

Design recommendations:

- avoid overly wide tables above the fold
- let rows wrap when showing badges or action groups
- use drawers for detail instead of stuffing too much into cards
- keep hero sections readable on one column
- prefer 2-column desktop grids that collapse to 1-column naturally

## Step 12: Package For Databricks Apps

Your app project usually needs:

```text
app.py
requirements.txt
app.yaml
```

Example:

```yaml
command:
  - python
  - app.py

env:
  - name: BRICKFLOWUI_ENV
    value: production
```

## Recommended Capstone

If you want to really learn the library, build one portal with all of these:

- executive overview
- pipeline topology page
- assistant page
- secure admin page
- local media assets
- Plotly plus native charts
- forms posting to custom routes
- auth-aware routing
- theme branding
- responsive review on mobile

That one exercise will teach you far more than isolated snippets.

## Best Companion Examples

After this tutorial, open these examples:

- `component_studio`
- `clinical_trial_command_center`
- `data_pipeline_command_center`
- `auth_portal`
- `chatbot_workspace`

Each one is opinionated on purpose. The goal is to show how teams actually build portals, not just how to render a button.
