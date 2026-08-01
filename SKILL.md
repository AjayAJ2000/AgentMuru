# BrickflowUI SKILL.md

> **Audience:** AI coding assistants (Databricks Genie Code, Cursor, VS Code Copilot, etc.)
> **Purpose:** Authoritative reference for generating correct, idiomatic, production-grade BrickflowUI apps.
> **Source:** https://ajayaj2000.github.io/brickflowUI | https://github.com/AjayAJ2000/brickflowUI

---

## 0. What Is BrickflowUI

BrickflowUI is a **Python-first UI framework** for building dashboards, portals, chatbot workspaces, pipeline command centers, and internal web apps — with zero frontend code required. It runs a FastAPI + WebSocket server in Python, serializes a virtual DOM (VNode tree) to the browser, and applies incremental patches on every state change. The React renderer in the browser handles all visual output.

**Import convention — always use this alias:**
```python
import brickflowui as db
```

**Install:**
```bash
pip install brickflowui
```

---

## 1. Mental Model

### 1.1 The Render Cycle

```
page function runs
  → returns VNode tree
  → serialized to JSON over WebSocket
  → React renders in browser
  → user event fires (click, change, submit)
  → Python handler runs
  → use_state() setter marks session dirty
  → page re-renders
  → diff patch sent to browser
```

### 1.2 State Is Session-Scoped

- Every browser session has **isolated state**.
- State does NOT persist across page navigations or new sessions.
- Mutating a list or dict in-place does NOT trigger a re-render. You must call the setter.

### 1.3 The Three Questions for Debugging Non-Updating UI

1. Is the value stored in `use_state`?
2. Is the input's `value=` bound to the state variable (not a local var)?
3. Is `on_change=` wired to the state setter?

---

## 2. App Setup — The Correct Skeleton

```python
import brickflowui as db

app = db.App(
    title="My Portal",
    theme="theme.yaml",   # or inline dict — see Section 8
)

@app.page("/", title="Home")
def home():
    # state declarations always come first
    selected, set_selected = db.use_state("all")

    # event handlers are plain Python functions defined locally
    def handle_change(value):
        set_selected(value)

    return db.Column(
        [
            db.Text("Home", variant="h1"),
            db.Select(
                name="filter",
                label="Environment",
                value=selected,
                options=[
                    {"label": "All", "value": "all"},
                    {"label": "Prod", "value": "prod"},
                ],
                on_change=handle_change,
            ),
            db.Text(f"Selected: {selected}"),
        ],
        gap=4,
        padding=6,
    )

if __name__ == "__main__":
    app.run()
```

### 2.1 API Routes

Use `@app.route` for HTTP POST/GET endpoints (form submissions, webhooks, JSON APIs):

```python
@app.route("/api/create-task", methods=["POST"])
def create_task(data):
    # data is the parsed request body dict
    # return a dict → serialized to JSON response
    return {"status": "ok", "id": data["name"]}
```

---

## 3. State and Reactivity

### 3.1 `use_state`

```python
value, set_value = db.use_state(initial_value)
```

Always call at the **top of the page function**, never inside loops or conditionals.

### 3.2 `use_effect`

Run side-effects (e.g., initial data load) when the page mounts or a dependency changes:

```python
data, set_data = db.use_state([])

def load():
    set_data(fetch_from_warehouse())

db.use_effect(load, deps=[])   # [] = run once on mount
```

### 3.3 `use_memo`

Memoize expensive computations across renders:

```python
filtered = db.use_memo(
    lambda: [r for r in raw_data if r["env"] == selected_env],
    deps=[selected_env, raw_data],
)
```

### 3.4 Critical Anti-Patterns

```python
# ❌ WRONG — local variable, not reactive
items = []
items.append("new")   # UI will NOT update

# ✅ CORRECT — state setter triggers re-render
items, set_items = db.use_state([])
set_items([*items, "new"])

# ❌ WRONG — mutating dict in place
config["key"] = "value"

# ✅ CORRECT
set_config({**config, "key": "value"})
```

---

## 4. Layout System

### 4.1 Core Primitives

All layout props use a **spacing scale** (1 = 4px, 6 = 24px, etc.).

**`db.Column`** — vertical stack (the primary page wrapper)
```python
db.Column(children, gap=4, padding=6, align="start", style={})
```

**`db.Row`** — horizontal grouping
```python
db.Row(children, gap=2, justify="between", align="center", wrap=True)
```

**`db.Grid`** — responsive multi-column layout (collapses on mobile)
```python
db.Grid(children, cols=3, gap=4)
```

**`db.Card`** — grouped surface (use as the primary container for sections)
```python
db.Card(
    children,
    title="Card Title",
    subtitle="Optional subtitle",
    bordered=True,
    elevated=True,
    hover=True,
    animated=True,
    animation="fade",
    animation_delay=100,
    padding=4,
)
```

**`db.Divider`** — section separator
```python
db.Divider()             # plain line
db.Divider("Filters")   # labeled break
```

**`db.Spacer`** — visual pause
```python
db.Spacer(2)
```

### 4.2 Hero and Section Components

**`db.Hero`** — landing pages, exec overview headers
```python
db.Hero(
    "Pipeline Command Center",
    subtitle="Observe freshness, SLA, cost, and incidents in one place.",
    eyebrow="Data Platform",
    badges=[db.Badge("Live", color="green")],
    actions=[db.Button("Open Runbook", on_click=open_runbook)],
    image="assets/hero-bg.png",
)
```

**`db.SectionHeader`** — anchors a major section within a page
```python
db.SectionHeader(
    "Lakehouse Health",
    subtitle="Current state of bronze, silver, and gold data products.",
    actions=[db.Button("Export", on_click=export_data)],
)
```

**`db.StatusStrip`** — compact KPI strip above heavier visualizations
```python
db.StatusStrip([
    {"label": "Freshness", "value": "11m",    "status": "healthy"},
    {"label": "SLA",       "value": "99.4%",  "status": "healthy"},
    {"label": "Failures",  "value": "2",       "status": "warning"},
    {"label": "P95 Lag",   "value": "4.2s",    "status": "critical"},
])
```

### 4.3 The Canonical Dashboard Page Template

This is the most reliable composition pattern for any analytics or operational page:

```python
@app.page("/dashboard", title="Dashboard")
def dashboard():
    selected_env, set_env = db.use_state("prod")
    show_drawer, set_drawer = db.use_state(False)
    selected_row, set_row = db.use_state(None)

    def open_row(row):
        set_row(row)
        set_drawer(True)

    return db.Column(
        [
            # 1. Page Header
            db.Hero(
                "Operations Dashboard",
                subtitle="Real-time pipeline health.",
                eyebrow="Platform Ops",
                badges=[db.Badge("Live", color="green")],
            ),

            # 2. KPI Strip
            db.StatusStrip([
                {"label": "Pipelines", "value": "142",  "status": "healthy"},
                {"label": "Failures",  "value": "3",    "status": "warning"},
                {"label": "SLA",       "value": "99.1%","status": "healthy"},
            ]),

            # 3. Filters
            db.Card(
                [
                    db.Grid(
                        [
                            db.Select(
                                name="env",
                                label="Environment",
                                value=selected_env,
                                options=[
                                    {"label": "Prod", "value": "prod"},
                                    {"label": "Dev",  "value": "dev"},
                                ],
                                on_change=set_env,
                            ),
                        ],
                        cols=4,
                        gap=4,
                    ),
                ],
                bordered=True,
            ),

            # 4. Charts
            db.SectionHeader("Trends", subtitle="Last 7 days"),
            db.Grid(
                [
                    db.Card([db.AreaChart(data=trend_data, x_key="day", y_keys=["runs"],   title="Run Volume")]),
                    db.Card([db.LineChart(data=trend_data, x_key="day", y_keys=["sla_pct"], title="SLA %")]),
                    db.Card([db.BarChart( data=team_data,  x_key="team",y_keys=["failures"],title="Failures by Team")]),
                ],
                cols=3,
                gap=4,
            ),

            # 5. Data Table
            db.Card(
                [
                    db.SectionHeader("Pipeline Inventory", actions=[db.Button("Refresh")]),
                    db.Table(
                        data=pipeline_rows,
                        columns=[
                            {"key": "name",      "label": "Pipeline",   "sortable": True},
                            {"key": "owner",     "label": "Owner"},
                            {"key": "freshness", "label": "Freshness",  "sortable": True},
                            {"key": "status",    "label": "Status"},
                        ],
                        pagination=15,
                        exportable=True,
                        on_row_click=open_row,
                    ),
                ],
                bordered=True,
            ),

            # 6. Row Drilldown Drawer
            db.Drawer(
                visible=show_drawer,
                title="Pipeline Detail",
                side="right",
                on_close=lambda: set_drawer(False),
                children=[db.Text(str(selected_row))],
            ),
        ],
        gap=5,
        padding=6,
    )
```

---

## 5. Component Reference

### 5.1 Content and Typography

```python
# Text variants: h1, h2, h3, h4, body, caption, code, label
db.Text("Title",    variant="h1")
db.Text("Subtitle", variant="h3", muted=True)
db.Text("Note",     variant="caption", muted=True)
db.Text("Label",    variant="label",   bold=True)

# Inline code / SQL snippets
db.Code("SELECT * FROM gold.orders LIMIT 100", language="sql")

# Badge — inline status indicator
db.Badge("Healthy",  color="green")
db.Badge("Warning",  color="amber")
db.Badge("Failing",  color="red")
db.Badge("Pending",  color="blue")
db.Badge("Archived", color="gray")

# Alert — persistent notice
db.Alert(
    "Two pipelines are behind SLA.",
    type="warning",          # info | success | warning | error
    title="Attention Needed",
    dismissible=True,
)

# Toast — transient action feedback
show_toast, set_toast = db.use_state(False)
db.Toast(
    "Saved successfully",
    title="Success",
    type="success",
    visible=show_toast,
    on_close=lambda: set_toast(False),
    auto_hide_ms=3000,
)

# Stat KPI card
db.Stat(
    label="Freshness",
    value="11 min",
    delta="-3 min",
    delta_type="decrease",   # increase | decrease | neutral
    animated=True,
)

# SparklineStat — KPI + mini trend
db.SparklineStat(
    label="Cost per run",
    value="$42",
    data=[{"day": "Mon", "value": 38}, {"day": "Tue", "value": 42}],
    x_key="day",
    y_key="value",
)

# Progress bar
db.Progress(83, label="Validation completeness")

# Spinner
db.Spinner("md")    # sm | md | lg

# EmptyState
db.EmptyState(
    title="No failed jobs",
    message="The current filter set has no matching incidents.",
    actions=[db.Button("Reset Filters", on_click=reset_filters)],
)

# Timeline
db.Timeline(
    [
        {"title": "Bronze job started",  "time": "09:10"},
        {"title": "Silver quality check","time": "09:22", "description": "2 warnings"},
        {"title": "Gold mart loaded",    "time": "09:45"},
    ],
    title="Run History",
)
```

### 5.2 Inputs and Forms

**Critical rule:** every input requires three things: `value=<state>`, `on_change=<setter>`, and `name=<string>`.

```python
# Button
db.Button("Refresh",  on_click=refresh,  variant="primary")
db.Button("Export",   on_click=export,   variant="secondary")
db.Button("Cancel",   on_click=close,    variant="ghost")
db.Button("Delete",   on_click=delete,   variant="destructive")
db.Button("Loading",  loading=is_loading, disabled=is_loading)

# Text input
query, set_query = db.use_state("")
db.Input(
    name="query",
    label="Search Pipelines",
    value=query,
    placeholder="Search by owner or table",
    on_change=set_query,
    type="text",           # text | password | email | number | url | search | date | textarea
    debounce_ms=220,
    change_strategy="debounce",  # debounce | blur | eager
)

# Select (single)
site, set_site = db.use_state("all")
db.Select(
    name="site",
    label="Site",
    value=site,
    options=[
        {"label": "All Sites", "value": "all"},
        {"label": "Toyama",    "value": "toyama"},
        {"label": "Chicago",   "value": "chicago"},
    ],
    on_change=set_site,
)

# MultiSelect
layers, set_layers = db.use_state(["bronze"])
db.MultiSelect(
    name="layers",
    label="Pipeline Layers",
    values=layers,
    options=[
        {"label": "Bronze", "value": "bronze"},
        {"label": "Silver", "value": "silver"},
        {"label": "Gold",   "value": "gold"},
    ],
    on_change=set_layers,
)

# Checkbox
critical_only, set_critical = db.use_state(False)
db.Checkbox(
    name="critical_only",
    label="Only critical incidents",
    checked=critical_only,
    on_change=set_critical,
)

# Toggle
auto_refresh, set_auto = db.use_state(False)
db.Toggle(
    name="auto_refresh",
    label="Auto refresh",
    checked=auto_refresh,
    on_change=set_auto,
)

# Slider
confidence, set_conf = db.use_state(90)
db.Slider(
    name="confidence",
    label=f"Min confidence: {confidence}%",
    min=80,
    max=100,
    step=1,
    value=confidence,
    on_change=set_conf,
)

# DateRangePicker
window, set_window = db.use_state({"start": "", "end": ""})
db.DateRangePicker(
    name="window",
    label="Observation window",
    start=window["start"],
    end=window["end"],
    on_change=set_window,  # receives {"start": ..., "end": ...}
)

# ChatInput
prompt, set_prompt = db.use_state("")
db.ChatInput(
    value=prompt,
    placeholder="Ask about freshness, failures, or cost",
    on_change=set_prompt,
    on_submit=submit_prompt,
)

# Form (HTTP POST to @app.route)
db.Form(
    [
        db.Input(name="owner",   label="Owner"),
        db.Input(name="summary", label="Summary"),
        db.Button("Create", html_type="submit"),
    ],
    action="/api/action-plan",
    method="POST",
    reload_on_success=True,
)
```

#### Recommended Filter Bar Pattern

```python
db.Card(
    [
        db.Grid(
            [
                db.Input(name="q",      label="Search",      value=q,      on_change=set_q),
                db.Select(name="env",   label="Environment", value=env,    on_change=set_env, options=env_opts),
                db.DateRangePicker(name="window", label="Window", start=window["start"], end=window["end"], on_change=set_window),
                db.MultiSelect(name="layers", label="Layers", values=layers, options=layer_opts, on_change=set_layers),
            ],
            cols=4,
            gap=4,
        ),
        db.Row(
            [
                db.Checkbox(name="critical", label="Critical only", checked=critical, on_change=set_critical),
                db.Button("Apply Filters", on_click=apply_filters, variant="primary"),
            ],
            justify="between",
            wrap=True,
        ),
    ],
    bordered=True,
)
```

### 5.3 Navigation and Overlays

**Multi-page sidebar app (recommended for 3+ pages):**
```python
app = db.App(title="Data Ops Portal")

@app.page("/",          title="Overview")
def overview(): ...

@app.page("/pipelines", title="Pipelines")
def pipelines(): ...

@app.page("/incidents", title="Incidents")
def incidents(): ...

# BrickflowUI auto-generates a Sidebar for multi-page apps.
# To override manually:
db.Sidebar(
    [
        db.NavItem("Overview",  "/",          icon="LayoutDashboard"),
        db.NavItem("Pipelines", "/pipelines", icon="GitBranch"),
        db.NavItem("Incidents", "/incidents", icon="AlertTriangle"),
    ],
    brand_name="Data Ops",
)
```

**TopNav (horizontal apps):**
```python
db.TopNav(
    items=[
        db.NavItem("Overview",  "/"),
        db.NavItem("Pipelines", "/pipelines"),
    ],
    brand_name="Acme Analytics",
    show_theme_toggle=True,
)
```

**Breadcrumbs:**
```python
db.Breadcrumbs([
    {"label": "Home",      "path": "/"},
    {"label": "Pipelines", "path": "/pipelines"},
    {"label": "Bronze Orders"},     # no path = current page
])
```

**Tabs (in-page sub-sections):**
```python
db.Tabs([
    db.TabItem("Summary",   [db.Text("Summary content")]),
    db.TabItem("Incidents", [db.Text("Incident list")]),
    db.TabItem("History",   [db.Text("Run history")]),
])
```

**Overlays — selection guide:**

| Need | Component |
|---|---|
| Blocking focused task | `Modal` |
| Side-panel detail while main page stays | `Drawer` |
| Small confirm / helper surface | `Popup` |
| Inline expandable sections | `Accordion` |

```python
# Modal
show_modal, set_modal = db.use_state(False)
db.Modal(
    visible=show_modal,
    title="Approve Release",
    on_close=lambda: set_modal(False),
    children=[
        db.Text("Review the release checklist."),
        db.Row([
            db.Button("Approve", on_click=approve, variant="primary"),
            db.Button("Cancel",  on_click=lambda: set_modal(False), variant="ghost"),
        ], gap=2),
    ],
)

# Drawer (standard row-drilldown pattern)
show_drawer, set_drawer = db.use_state(False)
selected_row, set_row = db.use_state(None)

def open_row(row):
    set_row(row)
    set_drawer(True)

db.Table(data=rows, columns=cols, on_row_click=open_row)
db.Drawer(
    visible=show_drawer,
    title="Pipeline Detail",
    side="right",
    on_close=lambda: set_drawer(False),
    children=[db.Text(str(selected_row))],
)

# Accordion
db.Accordion(
    [
        db.AccordionItem("What happened?",        [db.Text("Pipeline lag increased at 09:30")]),
        db.AccordionItem("Recommended action",    [db.Text("Re-run the silver validation task")]),
        db.AccordionItem("Escalation path",       [db.Text("Page the on-call data engineer")]),
    ],
    default_open=[0],
)
```

### 5.4 Tables

```python
db.Table(
    data=rows,             # list of dicts
    columns=[
        {"key": "pipeline", "label": "Pipeline",  "sortable": True},
        {"key": "owner",    "label": "Owner"},
        {"key": "freshness","label": "Freshness",  "sortable": True},
        {"key": "status",   "label": "Status"},
    ],
    pagination=15,
    exportable=True,
    loading=is_loading,
    empty_message="No pipelines match the current filters.",
    on_row_click=open_row,
)
```

Always pass `loading=True` while data is being fetched. Always pass `empty_message=` for filtered results.

### 5.5 Charts and Visualizations

All charts share these common props:
- `title` — chart title
- `height` — pixel height (default ~300)
- `loading` — show skeleton while data loads
- `empty_message` — shown when `data=[]`

**Time-series and trend:**
```python
# AreaChart — throughput, rows processed, cost over time
db.AreaChart(data=rows, x_key="day",  y_keys=["volume"],   title="Daily Volume",  height=280)

# LineChart — SLA, latency, freshness trends
db.LineChart(data=rows, x_key="day",  y_keys=["sla_pct"],  title="SLA %",         height=280)

# BarChart — comparison by team, domain, environment
db.BarChart( data=rows, x_key="team", y_keys=["failures"], title="Failures",       height=280)

# ComposedChart — bars + lines in one visual
db.ComposedChart(
    data=rows,
    x_key="day",
    bar_keys=["runs"],
    line_keys=["success_rate"],
    title="Runs and Success Rate",
)
```

**Distribution and proportions:**
```python
# DonutChart — incident mix, environment share
db.DonutChart(data=rows, name_key="env", value_key="count", title="By Environment")

# TreeMap — cost concentration, workload share
db.TreeMap(data=rows, name_key="team", value_key="cost", title="Cost by Team")

# FunnelChart — stage drop-off
db.FunnelChart(data=stages, name_key="stage", value_key="count", title="Pipeline Stages")
```

**Operational / analytical:**
```python
# GaugeChart — single health or readiness score
db.GaugeChart(value=94.2, min=0, max=100, title="SLA Score", thresholds=[80, 95])

# RadarChart — multi-dimension scorecard
db.RadarChart(data=dims, name_key="dimension", value_key="score", title="Platform Scorecard")

# Heatmap — hour-by-layer, day-by-team, failure density
db.Heatmap(data=cells, x_key="hour", y_key="layer", value_key="lag_sec", title="Freshness Heatmap")

# ScatterChart — anomaly views (duration vs cost)
db.ScatterChart(data=rows, x_key="duration_s", y_key="cost_usd", title="Duration vs Cost")

# SparklineStat (inline mini-chart + KPI)
db.SparklineStat(label="Cost/run", value="$42", data=hist, x_key="day", y_key="value")

# Plot — raw Plotly for advanced cases
import plotly.graph_objects as go
fig = go.Figure(go.Scatter(x=[1,2,3], y=[4,5,6]))
db.Plot(fig)
```

**Pipeline / operational DAG:**
```python
db.PipelineGraph(
    nodes=[
        {"id": "raw",    "label": "Raw Ingest",      "status": "healthy"},
        {"id": "bronze", "label": "Bronze Orders",   "status": "running"},
        {"id": "silver", "label": "Silver Quality",  "status": "watch"},
        {"id": "gold",   "label": "Gold Mart",       "status": "pending"},
    ],
    edges=[
        {"from": "raw",    "to": "bronze"},
        {"from": "bronze", "to": "silver"},
        {"from": "silver", "to": "gold"},
    ],
    on_node_click=select_node,
)
```

Node status values: `healthy` | `running` | `watch` | `warning` | `critical` | `pending` | `failed`

**Dashboard chart grid pattern:**
```python
db.Grid(
    [
        db.Card([db.ComposedChart(...)]),
        db.Card([db.Heatmap(...)]),
        db.Card([db.GaugeChart(...)]),
        db.Card([db.DonutChart(...)]),
    ],
    cols=2,
    gap=4,
)
```

### 5.6 Workflow Components

```python
# Stepper — release phases, medallion layers, onboarding flows
db.Stepper(
    [
        {"label": "Bronze"},
        {"label": "Silver"},
        {"label": "Gold"},
    ],
    active=1,   # 0-indexed current step
)

# KanbanBoard — triage, incident management, action queues
db.KanbanBoard(
    [
        {"id": "backlog", "label": "Backlog", "cards": [
            {"id": "c1", "title": "Fix SLA breach", "description": "Gold mart late"},
        ]},
        {"id": "doing",   "label": "Doing",   "cards": [
            {"id": "c2", "title": "Backfill silver"},
        ]},
        {"id": "done",    "label": "Done",    "cards": []},
    ],
    on_card_click=handle_card,
)

# Timeline — incident or release history
db.Timeline(
    [
        {"title": "Deploy started",      "time": "09:00"},
        {"title": "Smoke tests passed",  "time": "09:12"},
        {"title": "Rollout complete",    "time": "09:31", "description": "All regions healthy"},
    ],
    title="Release History",
)
```

### 5.7 Chatbot / Copilot Pattern

```python
@app.page("/copilot", title="Ops Copilot")
def copilot():
    messages, set_messages = db.use_state([
        {"role": "assistant", "content": "Hello! Ask me about pipeline health, SLA, or cost."}
    ])
    prompt, set_prompt = db.use_state("")
    loading, set_loading = db.use_state(False)

    def submit(text):
        if not text.strip():
            return
        new_messages = [*messages, {"role": "user", "content": text}]
        set_messages(new_messages)
        set_prompt("")
        set_loading(True)
        answer = call_llm_or_query(text)   # your backend call
        set_messages([*new_messages, {"role": "assistant", "content": answer}])
        set_loading(False)

    return db.Column(
        [
            db.SectionHeader("Ops Copilot", subtitle="Ask about your pipelines"),
            db.Card(
                [
                    db.Column(
                        [
                            db.ChatMessage(msg["role"], msg["content"], name="Ops Copilot")
                            for msg in messages
                        ],
                        gap=2,
                    ),
                    db.Spinner("sm") if loading else db.Spacer(0),
                    db.ChatInput(
                        value=prompt,
                        placeholder="Ask about freshness, failures, or cost",
                        on_change=set_prompt,
                        on_submit=submit,
                    ),
                ],
                bordered=True,
            ),
        ],
        gap=4,
        padding=6,
    )
```

### 5.8 Databricks-Specific Components

`WarehouseSelector`, `JobTrigger`, and `CatalogBrowser` are server-driven. Use the identity-aware helpers in `brickflowui.databricks`, then pass their normalized records and public UI state into the components. Never send tokens or SDK objects through component props.

```python
# WarehouseSelector — let users pick a SQL warehouse
from brickflowui import databricks as dbrx

warehouse_id, set_warehouse = db.use_state("")
db.WarehouseSelector(
    warehouses=dbrx.list_warehouses(),
    selected_id=warehouse_id,
    on_select=set_warehouse,
    label="SQL Warehouse",
)

# JobTrigger — fire a Databricks job
db.JobTrigger(
    job_id="1234567890",
    label="Run Bronze Pipeline",
    on_trigger=lambda payload: dbrx.trigger_job(payload["job_id"]),
)

# CatalogBrowser — Unity Catalog browser
db.CatalogBrowser(
    catalogs=dbrx.catalog_tree(),
    on_select=lambda path: set_selected_table(path),
)
```

---

## 6. Project File Structure (Recommended)

```
my_portal/
├── app.py                  # db.App(), @app.page(), @app.route(), app.run()
├── theme.yaml              # branding, colors, loading screen
├── requirements.txt
├── app.yaml                # Databricks Apps deployment config
├── assets/
│   ├── logo.svg
│   ├── favicon.svg
│   └── loader.gif
├── pages/
│   ├── __init__.py
│   ├── overview.py         # each page in its own module
│   ├── pipelines.py
│   └── incidents.py
├── data/
│   ├── __init__.py
│   └── queries.py          # all DB / warehouse queries isolated here
└── components/
    ├── __init__.py
    └── filter_bar.py       # reusable page-section components
```

**`app.py` with multi-module pages:**
```python
import brickflowui as db
from pages.overview  import overview
from pages.pipelines import pipelines
from pages.incidents import incidents

app = db.App(title="Data Ops Portal", theme="theme.yaml")

app.page("/",          title="Overview") (overview)
app.page("/pipelines", title="Pipelines")(pipelines)
app.page("/incidents", title="Incidents")(incidents)

if __name__ == "__main__":
    app.run()
```

**`pages/pipelines.py`:**
```python
import brickflowui as db
from data.queries import get_pipelines, get_trend

def pipelines():
    env, set_env = db.use_state("prod")
    loading, set_loading = db.use_state(True)
    rows, set_rows = db.use_state([])
    trend, set_trend = db.use_state([])

    def load():
        set_loading(True)
        set_rows(get_pipelines(env))
        set_trend(get_trend(env))
        set_loading(False)

    db.use_effect(load, deps=[env])

    return db.Column(
        [
            db.SectionHeader("Pipelines", subtitle=f"Environment: {env}"),
            # ... rest of page
        ],
        gap=4,
        padding=6,
    )
```

---

## 7. Performance Patterns

### 7.1 Always Do

- Use `debounce_ms=220, change_strategy="debounce"` on search inputs.
- Use a dedicated "Apply Filters" button for expensive backend loads (separate pending/applied state).
- Add `loading=is_loading` to every Table and Chart while data is fetching.
- Add `empty_message=` to every Table and Chart.
- Paginate tables: `pagination=15` or `pagination=25` for large datasets.
- Pre-aggregate in SQL/Python before sending to the UI. Never pass thousands of raw rows to a chart.
- Keep chart data to 30–90 points. Aggregate by hour, day, or week as needed.
- Use `use_memo` for filtered/sorted datasets derived from raw state.

### 7.2 Never Do

- Run a warehouse query on every keystroke.
- Pass raw DataFrames or Spark DataFrames to components — always `.toPandas().to_dict("records")` first.
- Mutate lists or dicts in place — always create new objects.
- Call expensive helpers multiple times inside one render — compute once, reuse.
- Skip `loading` states — users will think the app is broken.

### 7.3 The Pending/Applied Filter Pattern

For any expensive load, never trigger a fetch on every dropdown change:

```python
# Pending = what the user is editing
# Applied = what the backend has actually fetched

pending_env, set_pending = db.use_state("prod")
applied_env, set_applied = db.use_state("prod")
rows,        set_rows    = db.use_state([])

def apply():
    set_applied(pending_env)   # triggers effect
    # or inline: set_rows(fetch(pending_env))

db.use_effect(lambda: set_rows(fetch(applied_env)), deps=[applied_env])

db.Row([
    db.Select(name="env", value=pending_env, options=env_opts, on_change=set_pending, label="Env"),
    db.Button("Apply", on_click=apply, variant="primary"),
], gap=3)
```

### 7.4 Loading State Pattern

```python
loading, set_loading = db.use_state(False)

def refresh():
    set_loading(True)
    try:
        set_rows(fetch_data())
    finally:
        set_loading(False)

db.Button("Refresh", on_click=refresh, loading=loading)
db.Table(data=rows, columns=cols, loading=loading)
```

---

## 8. Theming

### 8.1 theme.yaml (recommended — keep in repo root)

```yaml
default_mode: light   # light | dark

branding:
  title: "Acme Data Portal"
  tagline: "Powered by BrickflowUI"
  logo: "assets/logo.svg"
  favicon: "assets/favicon.svg"
  show_theme_toggle: true

loading:
  title: "Acme Data Portal"
  subtitle: "Analytics workspace"
  message: "Connecting to warehouse..."
  animation: "pulse"        # spinner | pulse | float
  asset: "assets/loader.gif"

colors:
  primary:       "#4361EE"
  primary_hover: "#3650D8"
  success:       "#22C55E"
  warning:       "#F59E0B"
  error:         "#F43F5E"

light_mode:
  colors:
    background: "#F8FAFC"
    surface:    "#FFFFFF"
    text:       "#0F172A"
    text_muted: "#475569"
    border:     "#E2E8F0"

dark_mode:
  colors:
    background: "#0A0F1E"
    surface:    "#0F172A"
    text:       "#F1F5F9"
    text_muted: "#94A3B8"
    border:     "#1E293B"
```

### 8.2 Using the Theme

```python
app = db.App(title="Acme Portal", theme="theme.yaml")
# or inline dict:
app = db.App(title="Acme Portal", theme={"default_mode": "light", "branding": {...}})
```

### 8.3 Theme Toggle

```python
# In TopNav:
db.TopNav(..., show_theme_toggle=True)

# Standalone:
db.ThemeToggle()
```

### 8.4 Local Assets

BrickflowUI auto-serves assets from your working directory. Reference them by relative path:

```python
db.Image("assets/logo.svg",  alt="Acme",  variant="inline")
db.Image("assets/user.png",  alt="User",  variant="avatar", width="40px")
db.Hero("Title", image="assets/hero.png")
app = db.App(loading={"asset": "assets/loader.gif"})
```

---

## 9. Databricks Apps Deployment

### 9.1 Minimum Files Required

```
app.py
requirements.txt
app.yaml
```

### 9.2 `app.yaml`

```yaml
command:
  - python
  - app.py

env:
  - name: BRICKFLOWUI_ENV
    value: production
```

**Never use** `streamlit run app.py`. **Never hardcode** `DATABRICKS_TOKEN` in `app.yaml`.

### 9.3 `requirements.txt`

```
# From PyPI (recommended for stable releases):
brickflowui>=0.1.4

# From GitHub tag (for specific version):
brickflowui @ git+https://github.com/AjayAJ2000/brickflowUI.git@v0.1.4

# From main branch (for latest):
brickflowui @ git+https://github.com/AjayAJ2000/brickflowUI.git@main
```

### 9.4 Verify Frontend Bundle Is Included

Before deploying, run this in the environment:

```python
import pathlib, brickflowui
pkg = pathlib.Path(brickflowui.__file__).parent
print("index:", (pkg / "frontend" / "dist" / "index.html").exists())   # must be True
print("assets:", (pkg / "frontend" / "dist" / "assets").exists())      # must be True
```

If either is `False`, the app will show "Connecting to runtime..." and never load.

### 9.5 Port Handling

In Databricks Apps, the port comes from the environment. BrickflowUI handles this automatically — do not hardcode `port=8000`.

---

## 10. Common Patterns Cheatsheet

### Filter + Table + Drawer (Most Common Pattern)
```python
@app.page("/pipelines")
def pipelines():
    env,         set_env     = db.use_state("prod")
    rows,        set_rows    = db.use_state([])
    loading,     set_loading = db.use_state(False)
    show_drawer, set_drawer  = db.use_state(False)
    selected,    set_selected= db.use_state(None)

    def load():
        set_loading(True)
        set_rows(get_pipeline_data(env))
        set_loading(False)

    def open_row(row):
        set_selected(row)
        set_drawer(True)

    db.use_effect(load, deps=[env])

    return db.Column([
        db.SectionHeader("Pipelines"),
        db.Card([
            db.Select(name="env", label="Env", value=env,
                      options=[{"label":"Prod","value":"prod"},{"label":"Dev","value":"dev"}],
                      on_change=set_env),
        ], bordered=True),
        db.Card([
            db.Table(data=rows, columns=COLS, pagination=15,
                     exportable=True, loading=loading,
                     empty_message="No pipelines found.",
                     on_row_click=open_row),
        ], bordered=True),
        db.Drawer(visible=show_drawer, title="Detail",
                  on_close=lambda: set_drawer(False),
                  children=[db.Text(str(selected))]),
    ], gap=4, padding=6)
```

### Toast After Action
```python
saved, set_saved = db.use_state(False)

def save():
    do_save()
    set_saved(True)

db.Button("Save", on_click=save)
db.Toast("Saved!", type="success", visible=saved,
         on_close=lambda: set_saved(False), auto_hide_ms=3000)
```

### Conditional Rendering
```python
# Always control flow via state — never modify component tree by side-effects
if len(rows) == 0:
    return db.EmptyState(title="No data", message="Try adjusting filters.")
return db.Table(data=rows, columns=cols)
```

### Modal Confirm
```python
show_modal, set_modal = db.use_state(False)

def confirm_delete():
    do_delete()
    set_modal(False)

db.Button("Delete", on_click=lambda: set_modal(True), variant="destructive")
db.Modal(
    visible=show_modal,
    title="Confirm Delete",
    on_close=lambda: set_modal(False),
    children=[
        db.Text("This action cannot be undone."),
        db.Row([
            db.Button("Confirm", on_click=confirm_delete, variant="destructive"),
            db.Button("Cancel",  on_click=lambda: set_modal(False), variant="ghost"),
        ], gap=2),
    ],
)
```

---

## 11. Anti-Patterns to Avoid

| Anti-Pattern | Why It Fails | Fix |
|---|---|---|
| `items.append(x)` — mutate in place | No re-render triggered | `set_items([*items, x])` |
| `db.use_state` inside a conditional | Breaks hook ordering | Move to top of page function |
| Passing a DataFrame directly to Table | Type error | `.to_dict("records")` first |
| Querying DB on every keystroke | Too slow, hammers warehouse | Use `debounce_ms` + `change_strategy="debounce"` |
| `loading` never set | UI looks broken on slow calls | Always set loading before/after async work |
| `empty_message` omitted | Blank/empty table with no explanation | Always include `empty_message=` |
| Hardcoding `port=8000` | Breaks in Databricks Apps | Remove — BrickflowUI reads env automatically |
| Using `streamlit run` in app.yaml | Wrong runtime | Use `python app.py` |
| `use_effect` with no `deps=` | Infinite render loop | Always pass `deps=[]` for mount or `deps=[var]` for reactivity |

---

## 12. Component Quick Reference

| Component | Category | Use When |
|---|---|---|
| `Column` | Layout | Vertical stacking (primary page wrapper) |
| `Row` | Layout | Horizontal grouping |
| `Grid` | Layout | Responsive card grids (cols=2/3/4) |
| `Card` | Layout | Section container with optional border/elevation |
| `Hero` | Layout | Page header, exec overview |
| `SectionHeader` | Layout | Section anchor within a page |
| `StatusStrip` | Layout | Compact multi-KPI header |
| `Text` | Content | All typography (h1-h4, body, caption, label) |
| `Badge` | Content | Inline status tags |
| `Alert` | Content | Persistent notices (info/warning/error/success) |
| `Toast` | Content | Transient post-action feedback |
| `Stat` | Content | KPI card with delta |
| `SparklineStat` | Content | KPI + mini sparkline |
| `Progress` | Content | Progress bar |
| `EmptyState` | Content | No-results or empty data state |
| `Timeline` | Content | Event/run history |
| `Button` | Input | Primary action trigger |
| `Input` | Input | Text, number, date, textarea |
| `Select` | Input | Single-option dropdown |
| `MultiSelect` | Input | Multi-option dropdown |
| `Checkbox` | Input | Boolean toggle with label |
| `Toggle` | Input | Switch-style boolean |
| `Slider` | Input | Numeric range |
| `DateRangePicker` | Input | Date window |
| `ChatInput` | Input | Copilot/chatbot prompt box |
| `Form` | Input | HTTP POST form |
| `Sidebar` | Nav | Multi-page app shell |
| `TopNav` | Nav | Horizontal app navigation |
| `NavItem` | Nav | Individual nav link |
| `Breadcrumbs` | Nav | Page location trail |
| `Tabs` | Nav | In-page sub-section switcher |
| `Modal` | Overlay | Blocking focused workflow |
| `Drawer` | Overlay | Side-panel detail (row drilldown) |
| `Popup` | Overlay | Small confirm/helper |
| `Accordion` | Overlay | Inline expandable sections |
| `Table` | Data | Structured records with sort/filter/export |
| `AreaChart` | Chart | Throughput/volume over time |
| `LineChart` | Chart | SLA/latency trend |
| `BarChart` | Chart | Comparison across categories |
| `DonutChart` | Chart | Mix/proportions |
| `ComposedChart` | Chart | Bars + lines combined |
| `GaugeChart` | Chart | Single score/SLA indicator |
| `RadarChart` | Chart | Multi-dimension scorecard |
| `Heatmap` | Chart | Density/freshness by 2D grid |
| `ScatterChart` | Chart | Anomaly/correlation view |
| `FunnelChart` | Chart | Stage drop-off |
| `TreeMap` | Chart | Cost/workload concentration |
| `SparklineStat` | Chart | KPI + inline trend |
| `PipelineGraph` | Chart | DAG / data lineage view |
| `Plot` | Chart | Raw Plotly figure |
| `Stepper` | Workflow | Phase/stage progression |
| `KanbanBoard` | Workflow | Work queues, triage |
| `ChatMessage` | Workflow | Copilot/chatbot message bubble |
| `WarehouseSelector` | Databricks | SQL warehouse picker |
| `JobTrigger` | Databricks | Trigger Databricks job |
| `CatalogBrowser` | Databricks | Unity Catalog browser |

---

## 13. Full Production Example

A complete, production-grade pipeline monitoring portal:

```python
# app.py
import brickflowui as db

app = db.App(title="Pipeline Portal", theme="theme.yaml")

@app.page("/", title="Overview")
def overview():
    env, set_env             = db.use_state("prod")
    rows, set_rows           = db.use_state([])
    trend, set_trend         = db.use_state([])
    loading, set_loading     = db.use_state(False)
    show_drawer, set_drawer  = db.use_state(False)
    selected, set_selected   = db.use_state(None)
    saved, set_saved         = db.use_state(False)

    def load():
        set_loading(True)
        set_rows(get_pipelines(env))
        set_trend(get_trend(env))
        set_loading(False)

    def open_row(row):
        set_selected(row)
        set_drawer(True)

    db.use_effect(load, deps=[env])

    COLS = [
        {"key": "name",      "label": "Pipeline",  "sortable": True},
        {"key": "owner",     "label": "Owner"},
        {"key": "freshness", "label": "Freshness",  "sortable": True},
        {"key": "status",    "label": "Status"},
    ]

    return db.Column(
        [
            db.Hero(
                "Pipeline Command Center",
                subtitle="Real-time lakehouse operations.",
                eyebrow="Data Platform",
                badges=[db.Badge("Live", color="green")],
            ),

            db.StatusStrip([
                {"label": "Pipelines", "value": str(len(rows)), "status": "healthy"},
                {"label": "Failures",  "value": str(sum(1 for r in rows if r.get("status") == "failed")), "status": "warning"},
                {"label": "SLA",       "value": "99.1%", "status": "healthy"},
            ]),

            db.Card(
                [
                    db.Select(
                        name="env", label="Environment",
                        value=env, on_change=set_env,
                        options=[
                            {"label": "Production", "value": "prod"},
                            {"label": "Development", "value": "dev"},
                        ],
                    )
                ],
                bordered=True,
            ),

            db.SectionHeader("Trends", subtitle="Last 7 days"),
            db.Grid(
                [
                    db.Card([db.AreaChart(data=trend, x_key="day", y_keys=["runs"],   title="Run Volume",  loading=loading)]),
                    db.Card([db.LineChart(data=trend, x_key="day", y_keys=["sla"],    title="SLA %",       loading=loading)]),
                    db.Card([db.BarChart( data=trend, x_key="day", y_keys=["cost"],   title="Daily Cost",  loading=loading)]),
                ],
                cols=3, gap=4,
            ),

            db.Card(
                [
                    db.SectionHeader(
                        "Pipelines",
                        actions=[db.Button("Refresh", on_click=load)],
                    ),
                    db.Table(
                        data=rows, columns=COLS,
                        pagination=20, exportable=True,
                        loading=loading,
                        empty_message="No pipelines found.",
                        on_row_click=open_row,
                    ),
                ],
                bordered=True,
            ),

            db.Drawer(
                visible=show_drawer,
                title="Pipeline Detail",
                side="right",
                on_close=lambda: set_drawer(False),
                children=[
                    db.Text(selected.get("name", "") if selected else "", variant="h3"),
                    db.Text(f"Owner: {selected.get('owner','') if selected else ''}"),
                    db.Text(f"Freshness: {selected.get('freshness','') if selected else ''}"),
                ],
            ),

            db.Toast(
                "Action saved",
                type="success",
                visible=saved,
                on_close=lambda: set_saved(False),
                auto_hide_ms=3000,
            ),
        ],
        gap=5, padding=6,
    )

if __name__ == "__main__":
    app.run()
```

---

## 14. Auth and Access Control

BrickflowUI has a first-class auth system. Use it for any app that touches sensitive data or is deployed to Databricks Apps.

### 14.1 Full `db.App()` Parameter Surface

```python
app = db.App(
    title="My Portal",
    theme="theme.yaml",

    # Auth
    auth_mode="hybrid",             # "app" | "user" | "hybrid"
    auth_provider=db.HeaderAuthProvider(),   # see below

    # Security
    cors_origins=["https://your-domain.com"],
    trusted_hosts=["your-domain.com"],
    websocket_origins=["https://your-domain.com"],

    # Branding shortcuts (also settable in theme.yaml)
    logo="assets/logo.svg",
    favicon="assets/favicon.svg",
)
```

### 14.2 Auth Helpers

```python
# Get the current authenticated user (returns Principal or None)
user = db.current_user()
principal = db.current_principal()
identity = db.current_app_identity()   # Databricks app service identity

# Booleans
is_auth = db.is_authenticated()

# Guards — call at top of page function to enforce access
db.require_auth()               # 401 if not authenticated
db.require_role("admin")        # 403 if user lacks role
```

### 14.3 Restricting Pages and Routes

```python
# Page only accessible to authenticated users
@app.page("/admin", title="Admin", access="authenticated")
def admin():
    ...

# Page restricted to a role
@app.page("/ops", title="Ops", access="authenticated", roles=["ops_team", "admin"])
def ops():
    ...

# Same on routes
@app.route("/api/delete", methods=["POST"], access="authenticated", roles=["admin"])
def delete_pipeline(data):
    ...
```

### 14.4 Auth Providers

```python
# Databricks Apps — reads the identity injected by the platform (recommended)
app = db.App(auth_mode="user", auth_provider=db.HeaderAuthProvider())

# Header auth — trust a header forwarded by a proxy/reverse proxy
app = db.App(auth_mode="user", auth_provider=db.HeaderAuthProvider(
    header_prefix="x-mycompany-",
))

# Static principal — for local dev / testing
app = db.App(auth_mode="user", auth_provider=db.StaticAuthProvider(
    db.Principal(
        subject="dev-user",
        display_name="Dev User",
        email="dev@example.com",
        roles=("admin",),
        authenticated=True,
        principal_type="user",
    )
))
```

### 14.5 Using the Current User in Page Logic

```python
@app.page("/", title="Home")
def home():
    user = db.current_user()

    return db.Column([
        db.Hero(
            f"Welcome, {user.display_name}" if user else "Welcome",
            subtitle="Data Platform Portal",
        ),
        db.Alert("You are not authenticated.", type="warning")
            if not user else db.Spacer(0),
    ], gap=4, padding=6)
```

---

## 15. Databricks SQL and Unity Catalog Helpers

These are the correct way to query data inside BrickflowUI apps running in Databricks. Never use raw `requests` or custom SQL drivers when these helpers are available.

### 15.1 SQL Helpers

```python
from brickflowui.databricks import sql

# Returns a list of dicts — ready to pass directly to db.Table or charts
rows = sql.query_to_records("SELECT * FROM gold.orders WHERE env = :env", params={"env": "prod"})

# Lower-level — returns raw result object
result = sql.query("SELECT COUNT(*) as total FROM silver.events")

# Execute DML (INSERT, UPDATE, DELETE, CALL)
sql.execute("INSERT INTO ops_log VALUES (:msg, current_timestamp())", params={"msg": "Triggered"})

# Transaction block
with sql.transaction():
    sql.execute("UPDATE pipelines SET status = 'running' WHERE id = :id", params={"id": pipeline_id})
    sql.execute("INSERT INTO audit_log VALUES (:id, 'started')",           params={"id": pipeline_id})
```

**Critical usage pattern inside a page:**
```python
@app.page("/pipelines")
def pipelines():
    from brickflowui.databricks import sql

    env, set_env     = db.use_state("prod")
    rows, set_rows   = db.use_state([])
    loading, set_loading = db.use_state(False)

    def load():
        set_loading(True)
        set_rows(sql.query_to_records(
            "SELECT name, owner, freshness_min, status FROM gold.pipeline_health WHERE env = :env ORDER BY freshness_min DESC",
            params={"env": env},
        ))
        set_loading(False)

    db.use_effect(load, deps=[env])

    return db.Column([
        db.Table(data=rows, columns=COLS, loading=loading, empty_message="No pipelines found."),
    ], gap=4, padding=6)
```

### 15.2 Unity Catalog Helpers

```python
from brickflowui import databricks as dbrx
from brickflowui.databricks import uc

# Browsing the catalog programmatically
catalogs = uc.list_catalogs()                            # ["main", ...]
schemas  = uc.list_schemas("main")                      # ["gold", ...]
tables   = uc.list_tables("main", "gold")               # [{"name": "orders"}, ...]
schema   = uc.table_schema("main", "gold", "orders")    # [{"name": "id", "type": "bigint"}, ...]

# Fetch sample rows — returns list of dicts
rows = uc.get_table("main", "gold", "orders", limit=50)
```

**Use with `CatalogBrowser` for interactive table selection:**
```python
selected_table, set_table = db.use_state(None)
preview_rows, set_preview = db.use_state([])

def on_table_select(selection):
    set_table(selection)
    set_preview(uc.get_table(
        selection["catalog"],
        selection["schema"],
        selection["table"],
        limit=25,
    ))

db.CatalogBrowser(catalogs=dbrx.catalog_tree(), on_select=on_table_select)

if preview_rows:
    db.Table(data=preview_rows, columns=[{"key": k, "label": k} for k in preview_rows[0]])
```

---

## 16. Cross-Page State with `use_context`

Use `use_context` / `set_context` when you need state that survives page navigation within the same session — like a selected warehouse, a logged-in user's preferences, or a global filter that applies across multiple pages.

```python
# Set from any page or component
db.set_context("selected_warehouse", warehouse_id)
db.set_context("active_env", "prod")

# Read from any page or component
warehouse = db.use_context("selected_warehouse", default="")
env        = db.use_context("active_env",        default="prod")
```

**Global navigation bar with persistent context:**
```python
# In a shared component module: components/nav.py
import brickflowui as db

def global_nav():
    env, set_env = db.use_state(db.use_context("active_env", "prod"))

    def change_env(v):
        set_env(v)
        db.set_context("active_env", v)   # persists across pages

    return db.TopNav(
        items=[
            db.NavItem("Overview",  "/"),
            db.NavItem("Pipelines", "/pipelines"),
            db.NavItem("Incidents", "/incidents"),
        ],
        brand_name="Data Ops",
        show_theme_toggle=True,
        actions=[
            db.Select(
                name="env", value=env,
                options=[{"label":"Prod","value":"prod"},{"label":"Dev","value":"dev"}],
                on_change=change_env,
            ),
        ],
    )
```

---

## 17. App-Level Mount (Global Shell)

Use `app.mount()` to attach a component that renders on every page — a persistent `TopNav`, a global `Alert` banner, or a session-wide `Toast` queue.

```python
app = db.App(title="Portal", theme="theme.yaml")

@app.mount
def shell():
    return db.TopNav(
        items=[
            db.NavItem("Overview",  "/"),
            db.NavItem("Pipelines", "/pipelines"),
        ],
        brand_name="Acme Data",
        show_theme_toggle=True,
    )

@app.page("/", title="Overview")
def overview():
    # TopNav renders automatically above this content
    ...
```

---

## 18. Visual Polish — Animation and Elevation Props

These additive props are available on `Card`, `Button`, `Stat`, and layout components. Always use them on executive-facing dashboards and KPI surfaces.

```python
# Card with entrance animation
db.Card(
    [db.Stat("Freshness", "11 min", delta="-3 min", delta_type="decrease", animated=True)],
    elevated=True,
    animated=True,
    animation="fade-up",      # fade | fade-up | fade-down | slide | scale
    animation_delay=0.1,      # seconds — stagger cards by incrementing this
)

# Grid of animated stat cards with staggered entrance
db.Grid(
    [
        db.Card([db.Stat("Pipelines", "142", animated=True)], elevated=True, animated=True, animation="fade-up", animation_delay=0.0),
        db.Card([db.Stat("Failures",  "3",   animated=True)], elevated=True, animated=True, animation="fade-up", animation_delay=0.1),
        db.Card([db.Stat("SLA",       "99%", animated=True)], elevated=True, animated=True, animation="fade-up", animation_delay=0.2),
        db.Card([db.Stat("Cost",      "$42", animated=True)], elevated=True, animated=True, animation="fade-up", animation_delay=0.3),
    ],
    cols=4, gap=4,
)

# Animated button
db.Button("Run Pipeline", on_click=run, variant="primary", animated=True, animation="pulse")
```

**Rule of thumb:** Use `animation_delay` in increments of `0.1` seconds across a grid of cards to create a staggered cascade effect. Never animate more than 6-8 items on a single page.

---

## 19. Chart Interactivity — `on_click`

Charts support click callbacks. Use them to drive drilldowns, filter other components, or open drawers.

```python
selected_week, set_week = db.use_state(None)
show_drawer,   set_drawer = db.use_state(False)

def handle_bar_click(point):
    # point contains the clicked data: {"x": "2024-W12", "y": 42, ...}
    set_week(point.get("x"))
    set_drawer(True)

db.BarChart(
    data=weekly_data,
    x_key="week",
    y_keys=["failures"],
    title="Failures by Week",
    on_click=handle_bar_click,
)

db.Drawer(
    visible=show_drawer,
    title=f"Week {selected_week} detail",
    on_close=lambda: set_drawer(False),
    children=[
        db.Table(
            data=[r for r in raw_data if r["week"] == selected_week],
            columns=DETAIL_COLS,
        )
    ],
)
```

Same pattern works for `AreaChart`, `LineChart`, `DonutChart`, `ScatterChart`, `ComposedChart`, `Heatmap`, and `PipelineGraph.on_node_click`.

---

## 20. Input Loading States

Inputs support `loading=True` to show an inline loading affordance while backend data (options, validation) is being fetched. Use this whenever options come from a database call.

```python
options, set_options   = db.use_state([])
opts_loading, set_opts = db.use_state(True)

def load_options():
    set_opts(True)
    set_options(sql.query_to_records("SELECT DISTINCT env as value, env as label FROM pipelines"))
    set_opts(False)

db.use_effect(load_options, deps=[])

db.Select(
    name="env",
    label="Environment",
    value=env,
    options=options,
    on_change=set_env,
    loading=opts_loading,   # shows spinner in the dropdown while loading
)

# Same for MultiSelect and DateRangePicker
db.MultiSelect(name="layers", values=layers, options=layer_opts, on_change=set_layers, loading=opts_loading)
```

---

## 21. Recipe Blueprints — Full Starter Skeletons

These are complete, runnable starting points. Pick the one closest to your use case and build on top of it.

### 21.1 Executive Dashboard

Best for: KPI overview, financial summaries, exec reporting, business analytics.

```python
import brickflowui as db

app = db.App(title="Executive Dashboard", theme="theme.yaml")

@app.page("/", title="Overview")
def overview():
    period, set_period = db.use_state("last_30_days")
    kpis,   set_kpis   = db.use_state([])
    trend,  set_trend  = db.use_state([])
    loading, set_loading = db.use_state(False)

    def load():
        set_loading(True)
        set_kpis(fetch_kpis(period))
        set_trend(fetch_trend(period))
        set_loading(False)

    db.use_effect(load, deps=[period])

    return db.Column([
        db.Hero("Executive Overview", subtitle="Real-time business metrics", eyebrow="Q2 2024"),

        db.Grid(
            [
                db.Card([db.Stat(k["label"], k["value"], delta=k.get("delta"), delta_type=k.get("delta_type"), animated=True)],
                         elevated=True, animated=True, animation="fade-up", animation_delay=i * 0.1)
                for i, k in enumerate(kpis or [{"label":"Revenue","value":"—"},{"label":"Users","value":"—"},{"label":"Conversion","value":"—"},{"label":"Churn","value":"—"}])
            ],
            cols=4, gap=4,
        ),

        db.Card([
            db.SectionHeader("Period", actions=[
                db.Select(name="period", label="", value=period, on_change=set_period,
                          options=[{"label":"Last 30 days","value":"last_30_days"},{"label":"Last 90 days","value":"last_90_days"}]),
            ]),
            db.Grid([
                db.Card([db.AreaChart(data=trend, x_key="date", y_keys=["revenue"], title="Revenue", loading=loading)]),
                db.Card([db.BarChart( data=trend, x_key="date", y_keys=["users"],   title="Users",   loading=loading)]),
                db.Card([db.LineChart(data=trend, x_key="date", y_keys=["cvr"],     title="CVR %",   loading=loading)]),
                db.Card([db.DonutChart(data=kpis, name_key="label", value_key="raw",title="Mix",     loading=loading)]),
            ], cols=2, gap=4),
        ], bordered=True),
    ], gap=5, padding=6)

if __name__ == "__main__":
    app.run()
```

### 21.2 Pipeline Command Center

Best for: Data engineering ops, medallion health, job monitoring, SLA tracking.

```python
import brickflowui as db
from brickflowui.databricks import sql

app = db.App(title="Pipeline Command Center", theme="theme.yaml")

COLS = [
    {"key": "name",        "label": "Pipeline",   "sortable": True},
    {"key": "layer",       "label": "Layer"},
    {"key": "freshness",   "label": "Freshness",  "sortable": True},
    {"key": "status",      "label": "Status"},
    {"key": "owner",       "label": "Owner"},
]

@app.page("/", title="Command Center")
def command_center():
    env,         set_env     = db.use_state("prod")
    rows,        set_rows    = db.use_state([])
    graph_nodes, set_nodes   = db.use_state([])
    graph_edges, set_edges   = db.use_state([])
    loading,     set_loading = db.use_state(False)
    show_drawer, set_drawer  = db.use_state(False)
    selected,    set_selected= db.use_state(None)

    def load():
        set_loading(True)
        set_rows(sql.query_to_records(
            "SELECT name, layer, freshness_min AS freshness, status, owner FROM gold.pipeline_health WHERE env = :env",
            params={"env": env}
        ))
        set_nodes([
            {"id": r["name"], "label": r["name"], "status": r["status"], "layer": r["layer"]}
            for r in rows
        ])
        set_loading(False)

    def open_row(row):
        set_selected(row)
        set_drawer(True)

    db.use_effect(load, deps=[env])

    return db.Column([
        db.Hero("Pipeline Command Center",
                subtitle="Medallion health, SLA, and incident triage.",
                eyebrow="Data Platform",
                badges=[db.Badge("Live", color="green")]),

        db.StatusStrip([
            {"label": "Pipelines", "value": str(len(rows)),                                          "status": "healthy"},
            {"label": "Failing",   "value": str(sum(1 for r in rows if r.get("status")=="failed")), "status": "warning" if any(r.get("status")=="failed" for r in rows) else "healthy"},
            {"label": "SLA",       "value": "99.1%",  "status": "healthy"},
            {"label": "P95 Lag",   "value": "4.2 min","status": "watch"},
        ]),

        db.Card([
            db.Select(name="env", label="Environment", value=env, on_change=set_env,
                      options=[{"label":"Production","value":"prod"},{"label":"Development","value":"dev"}]),
        ], bordered=True),

        db.Grid([
            db.Card([db.PipelineGraph(nodes=graph_nodes, edges=graph_edges, on_node_click=open_row)]),
            db.Card([db.Heatmap(data=rows, x_key="layer", y_key="owner", value_key="freshness", title="Freshness by Layer/Owner", loading=loading)]),
        ], cols=2, gap=4),

        db.Card([
            db.SectionHeader("Pipeline Inventory", actions=[db.Button("Refresh", on_click=load)]),
            db.Table(data=rows, columns=COLS, pagination=20, exportable=True, loading=loading,
                     empty_message="No pipelines found.", on_row_click=open_row),
        ], bordered=True),

        db.Drawer(visible=show_drawer, title="Pipeline Detail", side="right",
                  on_close=lambda: set_drawer(False),
                  children=[
                      db.Text(selected["name"] if selected else "", variant="h3"),
                      db.Badge(selected.get("status","") if selected else "", color="green" if selected and selected.get("status")=="healthy" else "red"),
                      db.Divider(),
                      db.Text(f"Owner: {selected.get('owner','') if selected else ''}"),
                      db.Text(f"Freshness: {selected.get('freshness','') if selected else ''} min"),
                  ]),
    ], gap=5, padding=6)

if __name__ == "__main__":
    app.run()
```

### 21.3 Chatbot / Copilot Workspace

Best for: Data Q&A, LLM-backed pipelines, AI assistants, Databricks Genie integrations.

```python
import brickflowui as db

app = db.App(title="Ops Copilot", theme="theme.yaml")

SYSTEM_INTRO = {"role": "assistant", "content": "Hello! Ask me about pipeline health, SLA, cost, or freshness."}

@app.page("/", title="Copilot")
def copilot():
    messages, set_messages = db.use_state([SYSTEM_INTRO])
    prompt,   set_prompt   = db.use_state("")
    loading,  set_loading  = db.use_state(False)
    sources,  set_sources  = db.use_state([])
    show_drawer, set_drawer= db.use_state(False)

    def submit(text):
        if not text.strip():
            return
        new_msgs = [*messages, {"role": "user", "content": text}]
        set_messages(new_msgs)
        set_prompt("")
        set_loading(True)
        answer, source_list = call_your_backend(text)   # returns (str, list)
        set_messages([*new_msgs, {"role": "assistant", "content": answer}])
        set_sources(source_list)
        set_loading(False)

    return db.Column([
        db.Hero("Ops Copilot", subtitle="Ask about your data platform.", eyebrow="AI Assistant"),

        db.Row([
            # Main chat column
            db.Column([
                db.Card([
                    db.Column(
                        [db.ChatMessage(m["role"], m["content"], name="Copilot" if m["role"]=="assistant" else None)
                         for m in messages],
                        gap=2,
                    ),
                    db.Spinner("sm") if loading else db.Spacer(0),
                    db.ChatInput(value=prompt, placeholder="Ask about failures, SLA, or cost...",
                                 on_change=set_prompt, on_submit=submit),
                ], bordered=True),
            ], gap=3),
        ], gap=4, wrap=True),

        db.Drawer(visible=show_drawer, title="Sources",
                  on_close=lambda: set_drawer(False),
                  children=[
                      db.Timeline([{"title": s["title"], "time": s.get("time","")} for s in sources], title="Retrieved Sources"),
                  ]),
    ], gap=5, padding=6)

if __name__ == "__main__":
    app.run()
```

### 21.4 Internal Product / Landing Page

Best for: Team portals, tool directories, internal microsites, launch pages.

```python
import brickflowui as db

app = db.App(title="Data Platform", theme="theme.yaml")

FEATURES = [
    {"title": "Pipeline Health",  "desc": "Real-time freshness, SLA, and incident tracking.",       "link": "/pipelines"},
    {"title": "Cost Explorer",    "desc": "Warehouse spend by team, domain, and environment.",        "link": "/cost"},
    {"title": "Catalog Browser",  "desc": "Browse Unity Catalog tables, schemas, and lineage.",       "link": "/catalog"},
    {"title": "Ops Copilot",      "desc": "Ask questions about your data platform in plain English.", "link": "/copilot"},
]

UPDATES = [
    {"title": "Gold mart SLA improved to 99.4%", "time": "Today"},
    {"title": "Cost per run reduced 18% via cluster right-sizing", "time": "This week"},
    {"title": "Unity Catalog migration complete", "time": "Last week"},
]

@app.page("/", title="Home")
def home():
    return db.Column([
        db.Hero("Data Platform Portal",
                subtitle="The single pane of glass for your Databricks lakehouse.",
                eyebrow="Acme Analytics",
                badges=[db.Badge("v2.4 Live", color="green")],
                actions=[db.Button("Get Started", on_click=lambda: None, variant="primary")]),

        db.SectionHeader("Platform Tools", subtitle="Everything you need to build, monitor, and ship data products."),
        db.Grid(
            [
                db.Card([
                    db.Text(f["title"], variant="h3"),
                    db.Text(f["desc"],  variant="body", muted=True),
                    db.Button("Open", on_click=lambda: None, variant="ghost"),
                ], hover=True, animated=True, animation="fade-up", animation_delay=i * 0.1, elevated=True)
                for i, f in enumerate(FEATURES)
            ],
            cols=2, gap=4,
        ),

        db.Grid([
            db.Card([
                db.SectionHeader("Recent Updates"),
                db.Timeline(UPDATES),
            ], bordered=True),
            db.Card([
                db.SectionHeader("Platform Health"),
                db.StatusStrip([
                    {"label": "Pipelines", "value": "142", "status": "healthy"},
                    {"label": "SLA",       "value": "99.4%","status": "healthy"},
                    {"label": "Incidents", "value": "1",   "status": "warning"},
                ]),
                db.Accordion([
                    db.AccordionItem("What counts as an incident?", [db.Text("Any pipeline that misses its SLA window by more than 30 minutes.")]),
                    db.AccordionItem("How is freshness measured?",  [db.Text("Time since the last successful table refresh in Unity Catalog.")]),
                ]),
            ], bordered=True),
        ], cols=2, gap=4),
    ], gap=5, padding=6)

if __name__ == "__main__":
    app.run()
```

---

## 22. AI Agent Decision Guide

This section is specifically for AI coding agents. Use it as a fast decision tree before writing any BrickflowUI code.

### 22.1 "What component should I reach for?"

| User intent | Correct first choice | Common wrong choice |
|---|---|---|
| Show a single number with a trend | `Stat` + `SparklineStat` | `Text` |
| Show 3-6 KPIs above charts | `StatusStrip` | A `Row` of `Stat` components |
| Compare values across categories | `BarChart` | `Table` |
| Show change over time (throughput) | `AreaChart` | `LineChart` |
| Show change over time (SLA / rate) | `LineChart` | `AreaChart` |
| Show proportions / mix | `DonutChart` | `BarChart` |
| Show a DAG or pipeline flow | `PipelineGraph` | Custom CSS layout |
| Show a 2D density grid | `Heatmap` | Multiple `BarChart` |
| Show a single health score | `GaugeChart` | `Progress` |
| Show sortable, filterable records | `Table` | `Column` of `Text` rows |
| Row detail without leaving page | `Drawer` | New `@app.page` |
| Quick confirm/warning | `Modal` or `Popup` | Inline `Alert` |
| Multi-step process | `Stepper` | Multiple pages |
| Work queue / triage board | `KanbanBoard` | `Table` |
| Chat / LLM Q&A | `ChatMessage` + `ChatInput` | `Input` + `Text` |
| Page header / hero | `Hero` | `Text("h1")` |
| Section anchor inside a page | `SectionHeader` | `Divider` + `Text` |
| Page navigation (3+ pages) | `Sidebar` or `TopNav` | Hand-built `Row` of `Button` |
| Expandable FAQ / notes | `Accordion` | Multiple `Card` rows |

### 22.2 "What state pattern should I use?"

| Scenario | Pattern |
|---|---|
| Data loads on page mount | `use_state([])` + `use_effect(load, deps=[])` |
| Data reloads when a filter changes | `use_effect(load, deps=[filter_var])` |
| Expensive dropdown options from DB | `use_state([])` + `use_effect` + `loading=opts_loading` on Select |
| User edits filters, applies explicitly | pending/applied split state + "Apply" button |
| Row drilldown into detail | `on_row_click` → `set_selected(row)` + `set_drawer(True)` |
| Chart click into detail | `on_click` → `set_selected(point)` + `set_drawer(True)` |
| Action feedback (save, delete) | `set_toast(True)` → `Toast(visible=..., auto_hide_ms=3000)` |
| Confirm before destructive action | `set_modal(True)` → `Modal(visible=...)` + two buttons |
| State needed on multiple pages | `use_context` / `set_context` |
| Computed value from existing state | `use_memo(fn, deps=[...])` |
| Aggregate once, use in 3+ components | `use_memo` — compute once, pass the memo result |

### 22.3 "What's the minimum viable polished page?"

Every page that gets shipped should have, at minimum:
1. A `Hero` or `SectionHeader` at the top
2. `loading=True` passed to every `Table` and `Chart` while data fetches
3. `empty_message=` on every `Table` and `Chart`
4. A `Toast` for any user-triggered write action
5. A `Drawer` (not a new page) for row/node drilldowns

If a page is missing any of these, it is not production-ready.

### 22.4 "How do I connect to real data?"

```python
# Databricks SQL (recommended for all Databricks-hosted apps)
from brickflowui.databricks import sql
rows = sql.query_to_records("SELECT * FROM gold.my_table WHERE env = :env", params={"env": env})

# Pandas DataFrame from any source
import pandas as pd
df = pd.read_csv("data.csv")
rows = df.to_dict("records")   # always convert before passing to Table/Chart

# PySpark DataFrame
rows = spark_df.limit(500).toPandas().to_dict("records")

# Static mock data for prototyping
rows = [
    {"name": "bronze_orders", "status": "healthy", "freshness": "8 min"},
    {"name": "silver_quality","status": "warning",  "freshness": "42 min"},
]
```

### 22.5 "How should I structure a file I'm generating?"

Follow this order strictly within every page function:

```python
def my_page():
    # 1. ALL use_state() declarations — never inside conditionals or loops
    value, set_value = db.use_state(...)

    # 2. ALL derived/memoized values
    filtered = db.use_memo(lambda: ..., deps=[value])

    # 3. ALL event handler functions (def, not lambda for complex logic)
    def handle_click(row):
        ...

    # 4. ALL use_effect() registrations
    db.use_effect(load_data, deps=[value])

    # 5. return — the component tree
    return db.Column([...], gap=4, padding=6)
```

### 22.6 "What does a good app feel like vs a bad one?"

**Good BrickflowUI app:**
- Has a `Hero` or `SectionHeader` on every page
- Shows a `Spinner` or `loading=True` while data fetches
- Uses `StatusStrip` for 3+ related KPIs instead of ad-hoc `Stat` rows
- Uses `Drawer` for row details, not a new page
- Uses `Toast` to confirm writes, not a permanent `Alert`
- Uses `animated=True` + staggered `animation_delay` on hero KPI cards
- Uses `exportable=True` on operational tables
- Has a consistent color theme from `theme.yaml`
- Uses `db.EmptyState` with a reset action when filters return nothing
- Never passes raw Spark DataFrames or Pandas DataFrames directly to components

**Bad BrickflowUI app (agent warning signs):**
- Page is just `db.Text` and `db.Table` with no structure
- Uses `print()` or `st.write()` (wrong framework)
- Calls `set_value()` with a mutated dict/list in place
- Calls `use_state()` inside a conditional
- Has no `loading=` state on any component
- Has charts with no `empty_message=`
- Navigates to a new page for every row detail
- Passes a Pandas DataFrame object (not `.to_dict("records")`) to `Table`
- Uses hardcoded `port=8000` in app.run()
- Has `streamlit run` in app.yaml

---

## 23. Source Links

- **Documentation:** https://ajayaj2000.github.io/brickflowUI/
- **GitHub:** https://github.com/AjayAJ2000/brickflowUI
- **Architecture:** https://ajayaj2000.github.io/brickflowUI/ARCHITECTURE/
- **Component Library:** https://ajayaj2000.github.io/brickflowUI/components/
- **Theming:** https://ajayaj2000.github.io/brickflowUI/THEMING/
- **Performance:** https://ajayaj2000.github.io/brickflowUI/PERFORMANCE/
- **Databricks Apps:** https://ajayaj2000.github.io/brickflowUI/DATABRICKS_APPS/
- **Troubleshooting:** https://ajayaj2000.github.io/brickflowUI/TROUBLESHOOTING/
