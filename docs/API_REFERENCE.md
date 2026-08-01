# API Reference

Use this page when you already understand the overall framework shape and want the current public surface in one place.

Pair this page with:

- [Quick Start](./GETTING_STARTED.md)
- [Examples](./EXAMPLES.md)
- [How It Works](./HOW_IT_WORKS.md)
- [Polish Guide](./POLISH_GUIDE.md)
- [Why BrickflowUI](./WHY_BRICKFLOWUI.md)

## API Usage Model

Think about the API in four layers:

1. `db.App(...)` and page/route registration
2. state hooks like `db.use_state(...)`
3. composable components like `db.Column(...)`, `db.Table(...)`, and `db.PipelineGraph(...)`
4. theme, auth, media, and deployment behavior around the app

This page is intentionally organized around those layers.

## Core

### `db.App(...)`

Main application object.

Important parameters:

- `title`
- `theme`
- `theme_color`
- `logo`
- `favicon`
- `auth_mode`
- `auth_provider`
- `cors_origins`
- `trusted_hosts`
- `websocket_origins`
- `loading`

Notes:

- `theme` accepts light/dark sections and style preset configuration
- `loading` accepts branded loading fields such as title, message, asset, animation, and mode-specific overrides

Methods:

- `@app.page(path, title=..., icon=..., access=..., roles=...)`
- `@app.route(path, methods=[...], access=..., roles=...)`
- `app.mount(component)`
- `app.run(host=None, port=None, reload=False)`

## State Hooks

- `db.use_state(initial)`
- `db.use_effect(fn, deps=None)`
- `db.use_memo(fn, deps=[...])`
- `db.use_context(key, default=None)`
- `db.set_context(key, value)`

## Auth Helpers

- `db.current_principal()`
- `db.current_user()`
- `db.current_app_identity()`
- `db.is_authenticated()`
- `db.require_auth()`
- `db.require_role(role)`
- `db.Principal(...)`
- `db.HeaderAuthProvider()`
- `db.StaticAuthProvider(principal)`

## Layout Components

- `db.Column`
- `db.Row`
- `db.Grid`
- `db.Card`
- `db.Divider`
- `db.Spacer`

Useful additive props:

- `Card(..., elevated=True, animated=True, animation="fade-up", animation_delay=0.1)`
- `Button(..., animated=True, animation="pulse")`
- `Button(..., icon="ArrowRight")`

## Content Components

- `db.Text`
- `db.Code`
- `db.Badge`
- `db.Alert`
- `db.Stat`
- `db.Progress`
- `db.Spinner`
- `db.EmptyState`
- `db.Toast`
- `db.Timeline`
- `db.Image`
- `db.SparklineStat`
- `db.Hero`
- `db.SectionHeader`
- `db.StatusStrip`
- `db.Stepper`
- `db.KanbanBoard`
- `db.ChatMessage`
- `db.ChatInput`

Useful additive props:

- `Stat(..., animated=True)`
- `Toast(..., visible=True)`

## Input Components

- `db.Button`
- `db.Input`
- `db.Select`
- `db.Checkbox`
- `db.Toggle`
- `db.Slider`
- `db.DateRangePicker`
- `db.MultiSelect`
- `db.Form`

Notes:

- `Input(..., loading=True)` and `Select(..., loading=True)` show inline loading affordances
- `Input` supports `debounce_ms`, `change_strategy`, and `sync_on_blur` for smoother backend-controlled typing flows
- `DateRangePicker` emits `{"start": "...", "end": "..."}` to its `on_change`
- `MultiSelect` emits `list[str]` to its `on_change`
- `MultiSelect(..., loading=True)` and `DateRangePicker(..., loading=True)` can reflect backend work directly
- `Form` preserves repeated field names as arrays when posting JSON
- components that accept `icon=` can use current Lucide icon names such as `"ArrowRight"`, `"ShieldCheck"`, `"LayoutDashboard"`, or `"Database"`

## Navigation And Surface Components

- `db.Sidebar`
- `db.NavItem`
- `db.Breadcrumbs`
- `db.Tabs`
- `db.TabItem`
- `db.Modal`
- `db.Drawer`
- `db.Popup`
- `db.Accordion`
- `db.AccordionItem`

## Data Components

- `db.Table`

Useful additive props:

- `Table(..., loading=True)`
- `Table(..., empty_message="No rows yet")`
- `Table(..., exportable=True)`
- `Table(..., on_row_click=handler)`

## Chart Components

- `db.Plot`
- `db.AreaChart`
- `db.BarChart`
- `db.LineChart`
- `db.DonutChart`
- `db.ScatterChart`
- `db.ComposedChart`
- `db.GaugeChart`
- `db.RadarChart`
- `db.Heatmap`
- `db.FunnelChart`
- `db.TreeMap`
- `db.PipelineGraph`

Useful additive props:

- `loading`
- `empty_message`
- `on_click`
- `colors`

Example:

```python
db.BarChart(
    data=rows,
    x_key="week",
    y_keys=["runs", "failures"],
    title="Pipeline trend",
    loading=is_loading,
    empty_message="No pipeline data available",
    on_click=handle_bar_click,
)
```

## Pipeline And App Composition Components

These components were added for richer `0.1.13` dashboards and internal apps:

- `db.PipelineGraph(nodes, edges, on_node_click=...)` renders a simple pipeline/DAG-style flow from plain dictionaries.
- `db.StatusStrip(items=[...])` renders compact signal cards for freshness, SLA, cost, latency, and incident counts.
- `db.KanbanBoard(columns=[...], on_card_click=...)` renders operational triage boards.
- `db.Stepper(steps=[...], active=...)` renders release, setup, or pipeline-stage progress.
- `db.ChatMessage(...)` and `db.ChatInput(...)` render chatbot/copilot-style experiences.
- `db.Hero(...)` and `db.SectionHeader(...)` provide polished landing-page and dashboard section patterns.
- `db.Popup(...)` provides a lightweight overlay for helper flows and quick confirmations.
- `db.Image(...)` renders screenshots, diagrams, and branded media inside apps.

Example pipeline graph:

```python
db.PipelineGraph(
    nodes=[
        {"id": "bronze", "label": "Bronze Orders", "layer": "bronze", "status": "running"},
        {"id": "silver", "label": "Silver Quality", "layer": "silver", "status": "watch"},
        {"id": "gold", "label": "Gold Mart", "layer": "gold", "status": "healthy"},
    ],
    edges=[
        {"from": "bronze", "to": "silver"},
        {"from": "silver", "to": "gold"},
    ],
    on_node_click=lambda node: set_selected(node["id"]),
)
```

Example chat input:

```python
message, set_message = db.use_state("")

db.ChatInput(
    value=message,
    placeholder="Ask about failed pipelines",
    on_change=set_message,
    on_submit=lambda prompt: set_answer(f"Investigating: {prompt}"),
)
```

## Theme Surface

Supported theme sections:

- `branding`
- `light`
- `dark`
- `colors`
- `surfaces`
- `typography`
- `spacing`
- `borders`
- `shadows`
- `motion`

Useful aliases:

- `background -> bg`
- `primary_hover -> primary-hover`
- `text_muted -> text-muted`
- `font_family -> sans`
- `base_size -> base-size`
- `surfaces.background -> canvas`
- `surfaces.surface -> muted`
- `shadows.medium -> md`
- `motion.duration_normal -> duration-normal`

## Databricks Helpers

### `brickflowui.databricks.sql`

- `query(sql, params=None)`
- `query_to_records(sql, params=None)`
- `execute(sql, params=None)`
- `transaction()`

### `brickflowui.databricks.uc`

- `list_catalogs()`
- `list_schemas(catalog)`
- `list_tables(catalog, schema)`
- `table_schema(catalog, schema, table)`
- `get_table(catalog, schema, table, limit=100)`


