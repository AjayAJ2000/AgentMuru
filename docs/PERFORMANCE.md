# Performance And Scalability

BrickflowUI is designed around a Python runtime and a frontend renderer that stay synchronized over WebSockets. That model is productive, but it also means performance depends on how often state changes, how much UI changes per event, and how much data a page tries to render at once.

This guide explains the practical rules that keep BrickflowUI smooth in larger environments.

## What The Runtime Optimizes For You

BrickflowUI already includes several protections by default:

- Text inputs sync locally first and debounce backend updates, so typing does not require a full Python round-trip per character.
- Interactive controls can show backend pending state automatically while handlers are still running.
- The frontend applies backend tree updates on the next animation frame and treats them as non-urgent React work, which reduces visible jank under heavier event traffic.
- WebSocket responses use patch updates when possible instead of replacing the entire rendered tree every time.

These defaults help a lot, but app structure still matters.

## The Main Rule

Keep high-frequency user actions local and keep heavy backend work intentional.

Good examples:

- debounce search text before querying data
- paginate tables instead of rendering thousands of rows
- group filters inside one fetch action instead of reloading everything after every small change
- compute aggregates once per event and reuse them across multiple cards and charts

Less ideal examples:

- running a warehouse query on every keystroke
- rebuilding large dashboards from multiple repeated helper calls inside a single render
- rendering giant raw datasets directly into tables and charts without slicing or summarizing

## Recommended Patterns

### 1. Use debounce-friendly inputs

`db.Input` and `db.ChatInput` support local-first sync behavior:

```python
query, set_query = db.use_state("")

search = db.Input(
    name="query",
    label="Search",
    value=query,
    on_change=set_query,
    debounce_ms=220,
    change_strategy="debounce",
)
```

Use `change_strategy="blur"` when the backend should only be updated after the user leaves the field.

### 2. Separate filter editing from expensive refreshes

For expensive data loads, let users adjust controls locally and fetch when they explicitly apply changes:

```python
pending_site, set_pending_site = db.use_state("all")
applied_site, set_applied_site = db.use_state("all")

filters = db.Row(
    [
        db.Select(
            name="site",
            label="Site",
            options=site_options,
            value=pending_site,
            on_change=set_pending_site,
        ),
        db.Button("Apply Filters", on_click=lambda: set_applied_site(pending_site)),
    ],
    gap=3,
)
```

This pattern is usually better than firing data work on every dropdown change when the backend call is expensive.

### 3. Prefer summary cards over raw data dumps

When a page represents a large system, lead with:

- KPI cards
- trend charts
- status strips
- health summaries
- paginated tables

Show detailed raw records only when the user drills in.

### 4. Keep charts focused

Charts become heavy when they try to show too many points at once.

Better approaches:

- show the latest 30 to 90 points
- pre-aggregate by hour, day, week, or environment
- use table drilldowns for raw record exploration
- use `PipelineGraph`, `StatusStrip`, `GaugeChart`, and `Heatmap` for operational summaries instead of forcing everything into a single mega-chart

### 5. Use loading states intentionally

If a backend action is expected to take time, surface that clearly:

```python
run_loading, set_run_loading = db.use_state(False)

def refresh():
    set_run_loading(True)
    try:
        load_data()
    finally:
        set_run_loading(False)

db.Button("Refresh", on_click=refresh, loading=run_loading)
```

BrickflowUI also tracks pending event lifecycle automatically for many components, so backend work can show loading even without custom glue. Explicit loading state is still useful when a page depends on multiple coordinated operations.

## Layout Guidance For Large Apps

For more scalable app shells:

- use `Sidebar` or `TopNav` for navigation instead of custom hand-built nav bars
- keep the page body constrained with a central max-width when the content is analytical
- split large screens into sections with `SectionHeader`, `Card`, and `Grid`
- use drawers, modals, or popups for secondary workflows instead of navigating away from the primary workspace

This improves both rendering clarity and mobile behavior.

## Data Guidance

If your data source is large:

- page backend queries
- pre-aggregate results in SQL or Python before rendering
- avoid sending large repeated payloads back into component state when only a small slice is needed
- reuse transformed datasets across multiple charts in the same render

For Databricks-backed apps, this usually means:

- query fewer columns
- aggregate in SQL first
- bring only the records the page actually needs

## When To Use Which View

Use the component that matches the information shape:

- `Table` for structured records
- `PipelineGraph` for lineage and workflow
- `KanbanBoard` for work queues
- `Timeline` for incident or release history
- `StatusStrip` for operational health
- `GaugeChart` for SLA or confidence indicators
- `Heatmap` for freshness, utilization, or failure density
- `Plot` when you need Plotly-specific interactivity

Using the right visual primitive is often the biggest performance improvement, because it avoids overloading a generic component with too much responsibility.

## Local Validation Checklist

Before calling an app production-ready, test these:

1. Type quickly in search inputs and confirm there is no lag.
2. Change filters rapidly and confirm the UI remains responsive while backend work is pending.
3. Resize to tablet and mobile widths and confirm navigation collapses cleanly.
4. Load the largest realistic table you expect and confirm pagination keeps the page usable.
5. Trigger multiple actions in succession and confirm loading banners, button states, and toasts resolve correctly.

## Recommended Example Apps

Use these as practical performance baselines:

- [`examples/local_playground/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/local_playground/app.py)
- [`examples/component_studio/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/component_studio/app.py)
- [`examples/acme_analytics_command_center/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/acme_analytics_command_center/app.py)
- [`examples/clinical_trial_command_center/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/clinical_trial_command_center/app.py)

They cover local-first inputs, mobile shell behavior, charts, workflow views, and professional dashboard composition patterns.
