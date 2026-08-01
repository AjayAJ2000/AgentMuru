# Recipes

Use these patterns when you know the kind of product you want to build and want a practical starting point.

## Executive dashboard

Use:

- `Grid`
- `Card`
- `Stat`
- `Table`
- `AreaChart`
- `BarChart`
- `DateRangePicker`
- `MultiSelect`
- `Drawer`

Good examples:

- [Data Pipeline Command Center](./EXAMPLES.md)
- [Workspace Studio](./EXAMPLES.md)

## Chatbot workspace

Use:

- `ChatMessage`
- `ChatInput`
- `Card`
- `Toast`
- `Drawer`
- `Timeline`
- `Accordion`
- `Breadcrumbs`

Recommended pattern:

1. Keep the conversation in `use_state`.
2. Use `Card` blocks for user and assistant messages.
3. Use a `Drawer` for traces, sources, or tool results.
4. Use `Toast` for completion or send-state feedback.
5. Use `ChatInput.on_submit` for the action that calls your model, job, or backend route.

## Landing page or internal product site

Use:

- `Card`
- `Grid`
- `SparklineStat`
- `Accordion`
- `Timeline`
- `Button`
- `Badge`

Recommended pattern:

1. Lead with a hero `Card`.
2. Use a 3-column feature grid.
3. Add a roadmap `Timeline`.
4. Use `Accordion` for FAQ.
5. Keep the theme calm and whitespace-heavy.

## Geometric showcase or glassmorphism concept

Use:

- `Card`
- `Row`
- `Column`
- `Grid`
- `Image`
- `Button`
- `Badge`
- `Popup`

Recommended pattern:

1. Build one outer shell card with a controlled gradient background.
2. Use a rounded top rail with pill-style navigation.
3. Keep one dominant hero message and one dominant image-led visual.
4. Use local SVG or PNG art rather than fake placeholder geometry boxes.
5. Add a rotating recent-work or featured-card section driven by `use_state`.

Best example:

- [Geometric Signal Lab](./GEOMETRIC_UI.md)

## Pipeline command center

Use:

- `PipelineGraph`
- `StatusStrip`
- `GaugeChart`
- `ComposedChart`
- `Heatmap`
- `ScatterChart`
- `Stat`
- `AreaChart`
- `BarChart`
- `DonutChart`
- `Table`
- `Breadcrumbs`
- `DateRangePicker`
- `MultiSelect`
- `Drawer`

Recommended pattern:

1. Start in mock mode.
2. Keep every metric visible as plain values and charts.
3. Add drilldown with row click or chart click.
4. Use `empty_message` and `loading` aggressively so the app stays honest while data loads.
5. Use `PipelineGraph.on_node_click` to open a drawer, select a node, or filter a table.

## Pipeline graph plus triage board

Use:

- `PipelineGraph`
- `KanbanBoard`
- `Drawer`
- `Table`
- `Alert`

Recommended pattern:

1. Keep pipeline nodes as dictionaries with `id`, `label`, `layer`, and `status`.
2. Keep edges as dictionaries with `from` and `to`.
3. Store the selected node in `use_state`.
4. Send delayed or failed nodes into `KanbanBoard` columns.
5. Use a `Drawer` or `Card` to show details for the selected node/card.

```python
selected, set_selected = db.use_state("No node selected")

db.PipelineGraph(
    nodes=nodes,
    edges=edges,
    on_node_click=lambda node: set_selected(node["id"]),
)
```
