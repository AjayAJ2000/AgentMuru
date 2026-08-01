# 19. Capstone Project

## Learning Goal

Build one complete app that proves you can use BrickflowUI as a skill.

The capstone is a **Data Product Command Center**. It combines:

- landing-page style hero
- dashboard KPIs
- filters
- tables
- multiple charts
- pipeline graph
- kanban triage
- chatbot assistant
- theming
- Databricks deployment files

## App Concept

Your app helps a data platform team monitor pipelines and explain the current state to stakeholders.

It should answer:

- Are pipelines healthy?
- Which layer is delayed?
- What is the success rate?
- What costs the most?
- Which pipeline should we investigate first?
- What does the assistant say about the current filters?

## File Structure

```text
capstone_command_center/
  app.py
  app.yaml
  requirements.txt
```

## Step 1: Create Mock Data

```python
PIPELINES = [
    {"pipeline": "Customer 360", "layer": "gold", "status": "healthy", "freshness": 11, "success": 99.4, "cost": 82, "duration": 18},
    {"pipeline": "Orders Lakehouse", "layer": "silver", "status": "watch", "freshness": 44, "success": 97.8, "cost": 127, "duration": 36},
    {"pipeline": "ML Features", "layer": "silver", "status": "at risk", "freshness": 78, "success": 95.9, "cost": 119, "duration": 55},
]
```

## Step 2: Add Theme

```python
app = db.App(
    theme={
        "branding": {"title": "Data Product Command Center"},
        "colors": {
            "primary": "#C81E5B",
            "primary_hover": "#A8184A",
            "background": "#F7F8F7",
            "surface": "#FFFFFF",
            "text": "#1B1F1D",
            "text_muted": "#5E6A64",
            "border": "#E2E8E3",
        },
        "borders": {"radius": "18px"},
    }
)
```

## Step 3: Add Controls

Use `Select` for layer, `Input` for search, `Slider` for success-rate floor, and `Checkbox` for urgent-only.

## Step 4: Add Summary

Use `Hero`, `StatusStrip`, `GaugeChart`, and `Stat`.

## Step 5: Add Charts

Use:

- `ComposedChart` for runs, success, and cost
- `ScatterChart` for cost vs duration
- `Heatmap` for failures by hour/layer
- `TreeMap` for cost concentration
- `RadarChart` for platform scorecard
- `FunnelChart` for pipeline stage gates

## Step 6: Add Pipeline Graph

```python
db.PipelineGraph(
    nodes=[
        {"id": "source", "label": "Source", "status": "healthy"},
        {"id": "bronze", "label": "Bronze", "status": "running"},
        {"id": "silver", "label": "Silver", "status": "watch"},
        {"id": "gold", "label": "Gold", "status": "healthy"},
    ],
    edges=[
        {"from": "source", "to": "bronze"},
        {"from": "bronze", "to": "silver"},
        {"from": "silver", "to": "gold"},
    ],
    on_node_click=lambda node: set_selected(node["label"]),
)
```

## Step 7: Add Triage

Use `KanbanBoard` with Healthy, Watch, and At Risk columns.

Clicking a card should update selected detail state.

## Step 8: Add Assistant

Use `ChatMessage` and `ChatInput`.

The assistant should answer at least:

- "what is at risk?"
- "what costs most?"
- "how many pipelines are healthy?"

It can use simple Python logic.

## Step 9: Add Table

Use:

```python
db.Table(filtered_rows, exportable=True, empty_message="No pipelines match your filters.")
```

## Step 10: Add Deployment Files

`requirements.txt`:

```text
brickflowui>=0.1.13
```

`app.yaml`:

```yaml
command:
  - python
  - app.py
```

## Success Criteria

Your capstone is complete when:

- all controls update the dashboard
- the table and charts use the same filtered data
- pipeline graph clicks update selected detail
- kanban card clicks update selected detail
- chat submit updates the assistant answer
- the page has a branded theme
- the app has Databricks-ready files

## Stretch Goals

- Add a `Drawer` for selected pipeline details.
- Add a `Modal` for creating an action plan.
- Replace mock data with Databricks SQL.
- Add auth protection.
- Add a second page for data model documentation.

## Checkpoint

If you can build this capstone without copying the full example, you are no longer just trying BrickflowUI. You are building with it.



