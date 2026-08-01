from __future__ import annotations

import brickflowui as db


app = db.App(
    theme={
        "branding": {"title": "Pipeline Observability 0.1.13"},
        "colors": {
            "primary": "#C81E5B",
            "primary_hover": "#A8184A",
            "background": "#F7F8F7",
            "surface": "#FFFFFF",
            "text": "#1B1F1D",
            "text_muted": "#5E6A64",
            "border": "#E2E8E3",
            "success": "#0F8A6C",
            "warning": "#C67A00",
            "error": "#B42318",
            "info": "#2563EB",
        },
        "typography": {
            "font_family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif",
            "base_size": "15px",
        },
        "borders": {"radius": "18px"},
    }
)


PIPELINE_NODES = [
    {"id": "source_api", "label": "Source API", "layer": "source", "status": "healthy"},
    {"id": "bronze_events", "label": "Bronze Events", "layer": "bronze", "status": "running"},
    {"id": "silver_quality", "label": "Silver Quality", "layer": "silver", "status": "watch"},
    {"id": "gold_marts", "label": "Gold Marts", "layer": "gold", "status": "healthy"},
    {"id": "bi_dashboards", "label": "BI Dashboards", "layer": "serving", "status": "healthy"},
]

PIPELINE_EDGES = [
    {"from": "source_api", "to": "bronze_events"},
    {"from": "bronze_events", "to": "silver_quality"},
    {"from": "silver_quality", "to": "gold_marts"},
    {"from": "gold_marts", "to": "bi_dashboards"},
]

RUNS = [
    {"pipeline": "Customer 360", "layer": "gold", "status": "healthy", "freshness": 11, "success": 99.4, "rows_m": 42, "cost": 82, "duration": 18},
    {"pipeline": "Orders Lakehouse", "layer": "silver", "status": "watch", "freshness": 44, "success": 97.8, "rows_m": 84, "cost": 127, "duration": 36},
    {"pipeline": "Finance Mart", "layer": "gold", "status": "healthy", "freshness": 18, "success": 99.1, "rows_m": 31, "cost": 64, "duration": 22},
    {"pipeline": "ML Features", "layer": "silver", "status": "at risk", "freshness": 78, "success": 95.9, "rows_m": 25, "cost": 119, "duration": 55},
    {"pipeline": "Raw Ingestion", "layer": "bronze", "status": "healthy", "freshness": 7, "success": 99.8, "rows_m": 152, "cost": 141, "duration": 14},
]

TREND = [
    {"day": "Mon", "runs": 85, "success": 98.6, "cost": 310},
    {"day": "Tue", "runs": 89, "success": 98.9, "cost": 328},
    {"day": "Wed", "runs": 93, "success": 99.1, "cost": 336},
    {"day": "Thu", "runs": 91, "success": 98.7, "cost": 329},
    {"day": "Fri", "runs": 96, "success": 99.3, "cost": 342},
]

HEATMAP = [
    {"hour": "08", "layer": "bronze", "failures": 0},
    {"hour": "08", "layer": "silver", "failures": 1},
    {"hour": "08", "layer": "gold", "failures": 0},
    {"hour": "12", "layer": "bronze", "failures": 0},
    {"hour": "12", "layer": "silver", "failures": 3},
    {"hour": "12", "layer": "gold", "failures": 1},
    {"hour": "16", "layer": "bronze", "failures": 1},
    {"hour": "16", "layer": "silver", "failures": 2},
    {"hour": "16", "layer": "gold", "failures": 0},
]


def filtered_runs(layer: str, search: str, min_success: float, urgent_only: bool) -> list[dict]:
    text = search.strip().lower()
    return [
        run
        for run in RUNS
        if (layer == "all" or run["layer"] == layer)
        and run["success"] >= min_success
        and (not urgent_only or run["status"] in {"watch", "at risk"})
        and (not text or text in run["pipeline"].lower())
    ]


def triage_columns(rows: list[dict]) -> list[dict]:
    healthy = [row for row in rows if row["status"] == "healthy"]
    watch = [row for row in rows if row["status"] == "watch"]
    risk = [row for row in rows if row["status"] == "at risk"]

    def cards(items: list[dict]) -> list[dict]:
        return [
            {
                "id": item["pipeline"],
                "title": item["pipeline"],
                "subtitle": f"{item['freshness']} min freshness, {item['success']}% success",
                "status": item["status"],
            }
            for item in items
        ]

    return [
        {"id": "healthy", "label": "Healthy", "cards": cards(healthy)},
        {"id": "watch", "label": "Watch", "cards": cards(watch)},
        {"id": "risk", "label": "At Risk", "cards": cards(risk)},
    ]


@app.page("/", title="Pipeline Command Center")
def home():
    layer, set_layer = db.use_state("all")
    search, set_search = db.use_state("")
    min_success, set_min_success = db.use_state(95.0)
    urgent_only, set_urgent_only = db.use_state(False)
    selected, set_selected = db.use_state("No pipeline selected")
    prompt, set_prompt = db.use_state("")
    chat_answer, set_chat_answer = db.use_state("Ask about delayed, costly, or failed pipelines.")

    rows = filtered_runs(layer, search, float(min_success), bool(urgent_only))
    avg_success = sum(row["success"] for row in rows) / max(len(rows), 1)
    avg_freshness = sum(row["freshness"] for row in rows) / max(len(rows), 1)
    total_cost = sum(row["cost"] for row in rows)

    def ask_copilot(value: str):
        set_prompt("")
        if "risk" in value.lower() or "fail" in value.lower():
            set_chat_answer("ML Features is the first review target: freshness is 78 minutes and success is 95.9%.")
        elif "cost" in value.lower():
            set_chat_answer(f"Raw Ingestion and Orders Lakehouse are the largest cost contributors. Current filtered cost is ${total_cost}.")
        else:
            set_chat_answer(f"{len(rows)} pipelines match your filters. Average success is {avg_success:.1f}%.")

    return db.Column(
        [
            db.Hero(
                title="Pipeline observability for serious internal data apps",
                subtitle="A 0.1.13 showcase with pipeline graphs, drilldowns, chart variety, kanban triage, and chatbot-style controls.",
                eyebrow="BrickflowUI 0.1.13",
                badges=[db.Badge("Databricks Apps ready", color="green"), db.Badge("Pure Python", color="purple")],
                actions=[db.Button("Refresh view", variant="primary"), db.Button("Open runbook", variant="secondary")],
                visual=db.GaugeChart(avg_success, label="Filtered success rate", color="#C81E5B"),
            ),
            db.Card(
                [
                    db.SectionHeader("Controls", "All inputs are stateful and can drive charts, tables, chat, and graph drilldowns."),
                    db.Grid(
                        [
                            db.Select(
                                name="layer",
                                label="Layer",
                                value=layer,
                                options=[
                                    {"label": "All", "value": "all"},
                                    {"label": "Bronze", "value": "bronze"},
                                    {"label": "Silver", "value": "silver"},
                                    {"label": "Gold", "value": "gold"},
                                ],
                                on_change=set_layer,
                            ),
                            db.Input(name="search", label="Search pipeline", value=search, on_change=set_search),
                            db.Slider(name="min_success", label=f"Minimum success: {min_success:.1f}%", min=95, max=100, step=0.1, value=min_success, on_change=set_min_success),
                            db.Checkbox(name="urgent", label="Only watch / at risk", checked=urgent_only, on_change=set_urgent_only),
                        ],
                        cols=4,
                    ),
                ],
                elevated=True,
                animated=True,
            ),
            db.StatusStrip(
                [
                    {"label": "Visible pipelines", "value": str(len(rows)), "status": "info", "detail": "After filters"},
                    {"label": "Avg success", "value": f"{avg_success:.1f}%", "status": "healthy", "detail": "Across selected rows"},
                    {"label": "Freshness", "value": f"{avg_freshness:.0f}m", "status": "watch" if avg_freshness > 30 else "healthy", "detail": "Lower is better"},
                    {"label": "Cost", "value": f"${total_cost}", "status": "info", "detail": "Current run window"},
                ]
            ),
            db.Grid(
                [
                    db.Card(
                        [
                            db.PipelineGraph(
                                nodes=PIPELINE_NODES,
                                edges=PIPELINE_EDGES,
                                title="Lakehouse Pipeline Flow",
                                on_node_click=lambda node: set_selected(f"{node['label']} selected ({node['status']})"),
                            ),
                            db.Spacer(2),
                            db.Alert(selected, type="info", title="Graph Drilldown"),
                        ],
                        elevated=True,
                    ),
                    db.Card(
                        [
                            db.SectionHeader("Pipeline Copilot", "A simple chatbot UI pattern for operational assistants."),
                            db.ChatMessage("assistant", chat_answer, name="Ops Copilot"),
                            db.ChatInput(
                                value=prompt,
                                placeholder="Ask: what is at risk, what costs most...",
                                on_change=set_prompt,
                                on_submit=ask_copilot,
                            ),
                        ],
                        elevated=True,
                    ),
                ],
                cols=2,
                gap=4,
            ),
            db.Grid(
                [
                    db.Card([db.ComposedChart(TREND, x_key="day", bar_keys=["runs"], line_keys=["success"], area_keys=["cost"], title="Runs, Success, and Cost")], elevated=True),
                    db.Card([db.ScatterChart(rows, x_key="cost", y_key="duration", title="Cost vs Duration", on_click=lambda point: set_selected(f"{point['pipeline']} costs ${point['cost']}"))], elevated=True),
                    db.Card([db.Heatmap(HEATMAP, x_key="hour", y_key="layer", value_key="failures", title="Failure Heatmap", on_click=lambda cell: set_selected(f"{cell['layer']} had {cell['failures']} failures at {cell['hour']}:00"))], elevated=True),
                    db.Card([db.TreeMap([{"name": row["pipeline"], "value": row["cost"]} for row in rows], title="Cost Treemap")], elevated=True),
                ],
                cols=2,
                gap=4,
            ),
            db.Grid(
                [
                    db.Card([db.FunnelChart([{"label": "Started", "value": 96}, {"label": "Validated", "value": 91}, {"label": "Published", "value": 88}], title="Pipeline Stage Funnel")], elevated=True),
                    db.Card([db.RadarChart([{"metric": "Freshness", "score": 88}, {"metric": "Reliability", "score": avg_success}, {"metric": "Cost", "score": 76}, {"metric": "Quality", "score": 93}], angle_key="metric", value_keys=["score"], title="Platform Scorecard")], elevated=True),
                ],
                cols=2,
                gap=4,
            ),
            db.Card(
                [
                    db.SectionHeader("Triage Board", "Kanban cards can power incident, quality, or release workflows."),
                    db.KanbanBoard(triage_columns(rows), on_card_click=lambda card: set_selected(f"{card['title']} opened from {card['column']}")),
                ],
                elevated=True,
            ),
            db.Card(
                [
                    db.SectionHeader("Run Table", "Tables can still be the operational source of truth."),
                    db.Table(
                        rows,
                        columns=[
                            {"key": "pipeline", "label": "Pipeline", "sortable": True},
                            {"key": "layer", "label": "Layer", "sortable": True},
                            {"key": "status", "label": "Status", "sortable": True},
                            {"key": "freshness", "label": "Freshness", "sortable": True},
                            {"key": "success", "label": "Success %", "sortable": True},
                            {"key": "cost", "label": "Cost", "sortable": True},
                        ],
                        exportable=True,
                        empty_message="No pipeline runs match your filters.",
                    ),
                ],
                elevated=True,
            ),
        ],
        padding=6,
        gap=5,
        style={"maxWidth": "1440px", "margin": "0 auto"},
    )


if __name__ == "__main__":
    app.run()


