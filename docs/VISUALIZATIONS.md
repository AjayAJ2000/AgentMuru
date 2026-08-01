# Visualizations And Pipelines

BrickflowUI `0.1.13` expands beyond basic dashboard charts. The goal is to let a data team represent operational reality directly: pipelines, freshness, failures, cost, triage, chatbot assistants, and executive signals.

## Chart Selection Guide

Use these defaults:

- `AreaChart` for volume, throughput, and long-running trends.
- `LineChart` for SLA, latency, freshness, and rate trends.
- `BarChart` for comparisons by team, layer, or pipeline.
- `DonutChart` for status mix, ownership mix, or risk mix.
- `ComposedChart` for mixed views like runs plus success rate plus cost.
- `ScatterChart` for cost vs duration, rows vs failures, or anomaly views.
- `GaugeChart` for one big health score, freshness score, or reliability score.
- `RadarChart` for capability scorecards.
- `Heatmap` for failures by time and layer.
- `FunnelChart` for stage drop-off or validation gates.
- `TreeMap` for cost, storage, table size, or workload concentration.

## Pipeline Graphs

`PipelineGraph` accepts plain dictionaries, so it works well with Databricks SQL query results or mock data while prototyping.

```python
nodes = [
    {"id": "source", "label": "Source API", "layer": "source", "status": "healthy"},
    {"id": "bronze", "label": "Bronze Events", "layer": "bronze", "status": "running"},
    {"id": "silver", "label": "Silver Quality", "layer": "silver", "status": "watch"},
    {"id": "gold", "label": "Gold Marts", "layer": "gold", "status": "healthy"},
]

edges = [
    {"from": "source", "to": "bronze"},
    {"from": "bronze", "to": "silver"},
    {"from": "silver", "to": "gold"},
]

selected, set_selected = db.use_state("No node selected")

db.PipelineGraph(
    nodes=nodes,
    edges=edges,
    title="Lakehouse Flow",
    on_node_click=lambda node: set_selected(f"{node['label']} is {node['status']}"),
)
```

## Chatbot UI Pattern

Use `ChatMessage` and `ChatInput` when you want an assistant/copilot surface around your dashboard.

```python
prompt, set_prompt = db.use_state("")
answer, set_answer = db.use_state("Ask about pipeline risk.")

db.Column(
    [
        db.ChatMessage("assistant", answer, name="Ops Copilot"),
        db.ChatInput(
            value=prompt,
            on_change=set_prompt,
            on_submit=lambda value: set_answer(f"Reviewing: {value}"),
        ),
    ]
)
```

## State And Events

Interactive components use the same event model as the rest of BrickflowUI:

- `ChatInput.on_change` receives the current text.
- `ChatInput.on_submit` receives the submitted text.
- `PipelineGraph.on_node_click` receives the clicked node dictionary.
- `KanbanBoard.on_card_click` receives the clicked card dictionary plus its column.
- Chart `on_click` callbacks receive the clicked chart payload where the underlying chart provides one.
- `Heatmap.on_click` receives the clicked cell dictionary.

## Recommended Example

Run:

```bash
python -m examples.data_pipeline_command_center.app
```

This example shows pipeline graphs, multiple controls, assistant UI, composed charts, heatmaps, kanban triage, and operational tables in one Databricks-ready app.
