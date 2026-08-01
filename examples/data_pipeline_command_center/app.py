from __future__ import annotations

import os
import logging

import brickflowui as db


LOGGER = logging.getLogger(__name__)


BRICKFLOW_THEME = {
    "branding": {"title": "BrickflowUI Pipeline Command Center"},
    "colors": {
        "primary": "#8B1E3F",
        "primary_hover": "#741733",
        "background": "#F5F6F4",
        "surface": "#FFFFFF",
        "text": "#19201C",
        "text_muted": "#65706A",
        "border": "#DDE2DE",
        "success": "#147D64",
        "warning": "#B36A12",
        "error": "#B42318",
        "info": "#35618D",
    },
    "typography": {
        "font_family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        "base_size": "15px",
    },
    "spacing": {"unit": "6px"},
    "borders": {"radius": "16px"},
}

CHART_COLORS = ["#8B1E3F", "#147D64", "#6D7872", "#B36A12"]
VIEW_KEYS = ("overview", "pipelines", "reliability", "triage", "assistant")
VIEW_LABELS = {
    "overview": "Overview",
    "pipelines": "Pipeline Flow",
    "reliability": "Reliability",
    "triage": "Triage",
    "assistant": "Assistant",
}

app = db.App(theme=BRICKFLOW_THEME)

SOURCE_OPTIONS = [
    {"label": "Mock records", "value": "mock"},
    {"label": "Databricks SQL", "value": "sql"},
]
DOMAIN_OPTIONS = [
    {"label": "All layers", "value": "all"},
    {"label": "Bronze", "value": "bronze"},
    {"label": "Silver", "value": "silver"},
    {"label": "Gold", "value": "gold"},
]
PIPELINE_OPTIONS = [
    {"label": "All pipelines", "value": "all"},
    {"label": "Customer 360", "value": "customer_360"},
    {"label": "Orders Lakehouse", "value": "orders_lakehouse"},
    {"label": "Finance Mart", "value": "finance_mart"},
    {"label": "ML Features", "value": "ml_features"},
    {"label": "Product Analytics", "value": "product_analytics"},
    {"label": "Raw Ingestion", "value": "raw_ingestion"},
]

PIPELINE_RECORDS = [
    {"pipeline": "customer_360", "pipeline_label": "Customer 360", "domain": "gold", "owner": "Data Platform", "status": "Healthy", "freshness_min": 12, "sla_target_min": 30, "rows_processed_m": 248, "cost_usd": 186, "success_rate": 99.8, "latency_min": 18, "incidents": 0},
    {"pipeline": "orders_lakehouse", "pipeline_label": "Orders Lakehouse", "domain": "silver", "owner": "Commerce Analytics", "status": "Watch", "freshness_min": 47, "sla_target_min": 45, "rows_processed_m": 412, "cost_usd": 263, "success_rate": 98.9, "latency_min": 36, "incidents": 2},
    {"pipeline": "finance_mart", "pipeline_label": "Finance Mart", "domain": "gold", "owner": "Finance BI", "status": "Healthy", "freshness_min": 21, "sla_target_min": 60, "rows_processed_m": 128, "cost_usd": 141, "success_rate": 99.5, "latency_min": 29, "incidents": 1},
    {"pipeline": "ml_features", "pipeline_label": "ML Features", "domain": "silver", "owner": "ML Platform", "status": "At Risk", "freshness_min": 83, "sla_target_min": 60, "rows_processed_m": 96, "cost_usd": 219, "success_rate": 96.8, "latency_min": 54, "incidents": 4},
    {"pipeline": "raw_ingestion", "pipeline_label": "Raw Ingestion", "domain": "bronze", "owner": "Data Platform", "status": "Healthy", "freshness_min": 8, "sla_target_min": 20, "rows_processed_m": 690, "cost_usd": 308, "success_rate": 99.9, "latency_min": 11, "incidents": 0},
    {"pipeline": "product_analytics", "pipeline_label": "Product Analytics", "domain": "gold", "owner": "Product Data", "status": "Healthy", "freshness_min": 17, "sla_target_min": 40, "rows_processed_m": 164, "cost_usd": 172, "success_rate": 99.3, "latency_min": 22, "incidents": 1},
]

SQL_EXAMPLE = """-- Normalized metrics boundary used by this application
SELECT pipeline, pipeline_label, domain, owner, status,
       freshness_min, sla_target_min, rows_processed_m,
       cost_usd, success_rate, latency_min, incidents
FROM your_catalog.your_schema.pipeline_metrics
"""


def load_pipeline_source(source_mode: str) -> tuple[list[dict], dict]:
    """Load normalized records with safe, browser-ready source metadata."""
    if source_mode != "sql":
        return PIPELINE_RECORDS, {
            "requested": "mock",
            "active": "mock",
            "fallback": False,
            "error": None,
        }

    table_name = os.getenv("DEMO_PIPELINE_METRICS_TABLE", "").strip()
    if not table_name:
        return PIPELINE_RECORDS, {
            "requested": "sql",
            "active": "mock",
            "fallback": True,
            "error": "SQL table is not configured",
        }

    try:
        from brickflowui.databricks import sql

        query = f"""
        SELECT pipeline, pipeline_label, domain, owner, status,
               freshness_min, sla_target_min, rows_processed_m,
               cost_usd, success_rate, latency_min, incidents
        FROM {table_name}
        """
        return sql.query_to_records(query), {
            "requested": "sql",
            "active": "sql",
            "fallback": False,
            "error": None,
        }
    except Exception:
        LOGGER.exception("Databricks SQL pipeline source failed; using mock fallback")
        return PIPELINE_RECORDS, {
            "requested": "sql",
            "active": "mock",
            "fallback": True,
            "error": "SQL source unavailable",
        }


def load_pipeline_records(source_mode: str) -> list[dict]:
    """Compatibility adapter returning normalized records without metadata."""
    records, _ = load_pipeline_source(source_mode)
    return records


def _renderer_status(status: str) -> str:
    return status.strip().lower()


def pipeline_flow(records: list[dict]) -> tuple[list[dict], list[dict]]:
    """Return a deterministic lakehouse graph keyed by pipeline identifiers."""
    layer_order = {"bronze": 0, "silver": 1, "gold": 2}
    ordered_records = sorted(
        records,
        key=lambda row: (layer_order.get(row["domain"], 99), row["pipeline"]),
    )
    nodes = [
        {
            "id": row["pipeline"],
            "label": row["pipeline_label"],
            "layer": row["domain"],
            "status": _renderer_status(row["status"]),
        }
        for row in ordered_records
    ]
    layer_ids = {
        layer: [row["pipeline"] for row in ordered_records if row["domain"] == layer]
        for layer in ("bronze", "silver", "gold")
    }
    edges = [
        {"from": source, "to": target}
        for source_layer, target_layer in (("bronze", "silver"), ("silver", "gold"))
        for source in layer_ids[source_layer]
        for target in layer_ids[target_layer]
    ]
    return nodes, edges


def triage_columns(records: list[dict]) -> list[dict]:
    """Group stable pipeline cards into operational triage lanes."""
    groups = (
        ("healthy", "Healthy", {"Healthy", "Strong"}),
        ("watch", "Watch", {"Watch"}),
        ("at-risk", "At Risk", {"At Risk"}),
    )
    return [
        {
            "id": group_id,
            "label": label,
            "cards": [
                {
                    "id": row["pipeline"],
                    "title": row["pipeline_label"],
                    "subtitle": f"{row['freshness_min']}m freshness · {row['success_rate']:.1f}% success",
                    "status": _renderer_status(row["status"]),
                }
                for row in records
                if row["status"] in statuses
            ],
        }
        for group_id, label, statuses in groups
    ]


def operational_chart_data(records: list[dict]) -> list[dict]:
    return [
        {
            "scope": row["pipeline_label"],
            "rows_m": row["rows_processed_m"],
            "cost_usd": row["cost_usd"],
            "sla_pct": row["success_rate"],
        }
        for row in records
    ]


def reliability_heatmap_data(records: list[dict]) -> list[dict]:
    return [
        {
            "pipeline": row["pipeline_label"],
            "layer": row["domain"],
            "failures": row["incidents"],
        }
        for row in records
    ]


def _page_heading(title: str, description: str, badge: str):
    return db.Row(
        [
            db.Column(
                [db.Text(title, variant="h1"), db.Text(description, muted=True)],
                gap=1,
                style={"minWidth": "0"},
            ),
            db.Badge(badge, color="green"),
        ],
        justify="between",
        align="center",
        wrap=True,
    )


def _empty_state(records: list[dict]):
    if records:
        return None
    return db.Alert(
        "No pipelines match the current filters. Reset the pipeline, layer, or success-rate controls.",
        type="warning",
        title="Empty filtered result",
    )


def _source_notice(source: dict):
    if source["active"] == "mock" and not source["fallback"]:
        return db.Alert(
            "Local mock records are active. Actions and acknowledgements in this showcase are simulated.",
            type="info",
            title="Mock source active",
        )
    if source["fallback"]:
        return db.Alert(
            f"{source['error']}. Showing normalized mock records as a safe fallback.",
            type="warning",
            title="SQL fallback active",
        )
    return db.Alert(
        "Databricks SQL returned normalized pipeline records for the current operating scope.",
        type="success",
        title="SQL source active",
    )


def _summary_strip(records: list[dict], period: str):
    average_success = sum(row["success_rate"] for row in records) / max(len(records), 1)
    average_freshness = sum(row["freshness_min"] for row in records) / max(len(records), 1)
    total_cost = sum(row["cost_usd"] for row in records)
    attention = sum(row["status"] in {"Watch", "At Risk"} for row in records)
    return db.StatusStrip(
        [
            {"label": "Visible pipelines", "value": str(len(records)), "status": "info", "detail": f"{period} filtered scope"},
            {"label": "Success rate", "value": f"{average_success:.1f}%", "status": "healthy" if average_success >= 99 else "watch", "detail": "Across visible runs"},
            {"label": "Freshness", "value": f"{average_freshness:.0f}m", "status": "healthy" if average_freshness <= 30 else "watch", "detail": "Lower is better"},
            {"label": "Run cost", "value": f"${total_cost:,.0f}", "status": "info", "detail": f"{attention} need attention"},
        ],
        title="Current operating window",
        columns=4,
    )


def _filters(
    source_mode,
    set_source_mode,
    domain,
    set_domain,
    pipeline,
    set_pipeline,
    period,
    set_period,
    search,
    set_search,
    min_sla,
    set_min_sla,
    critical_only,
    set_critical_only,
):
    return db.Card(
        [
            db.SectionHeader("Scope and guardrails", "Refine every operational view from one shared record boundary."),
            db.Grid(
                [
                    db.Select(name="source_mode", label="Source", options=SOURCE_OPTIONS, value=source_mode, on_change=set_source_mode),
                    db.Select(name="domain", label="Layer", options=DOMAIN_OPTIONS, value=domain, on_change=set_domain),
                    db.Select(name="pipeline", label="Pipeline", options=PIPELINE_OPTIONS, value=pipeline, on_change=set_pipeline),
                    db.Input(name="search", label="Search pipeline or owner", value=search, on_change=set_search),
                ],
                cols=4,
                gap=3,
            ),
            db.Row(
                [
                    db.Slider(name="min_sla", label=f"Minimum success: {min_sla:.1f}%", min=95, max=100, step=0.1, value=min_sla, on_change=set_min_sla),
                    db.Checkbox(name="critical_only", label="Watch and at-risk only", checked=critical_only, on_change=set_critical_only),
                    db.Row(
                        [
                            db.Button("MTD", on_click=lambda: set_period("MTD"), variant="primary" if period == "MTD" else "ghost"),
                            db.Button("QTD", on_click=lambda: set_period("QTD"), variant="primary" if period == "QTD" else "ghost"),
                            db.Button("YTD", on_click=lambda: set_period("YTD"), variant="primary" if period == "YTD" else "ghost"),
                        ],
                        gap=1,
                    ),
                ],
                justify="between",
                align="center",
                wrap=True,
            ),
        ],
        style={"border": "1px solid var(--db-border)"},
    )


def overview_page(records: list[dict], period: str, show_data_model, set_show_data_model):
    empty = _empty_state(records)
    table = db.Table(
        records,
        columns=[
            {"key": "pipeline_label", "label": "Pipeline", "sortable": True},
            {"key": "domain", "label": "Layer", "sortable": True},
            {"key": "owner", "label": "Owner", "sortable": True},
            {"key": "status", "label": "Status", "sortable": True},
            {"key": "freshness_min", "label": "Freshness", "sortable": True},
            {"key": "success_rate", "label": "Success %", "sortable": True},
        ],
        pagination=10,
        empty_message="No pipeline records match the current scope.",
    )
    children = [
        _page_heading("Operational pulse", "A dense read on throughput, freshness, and pipelines requiring intervention.", f"{period} snapshot"),
    ]
    if empty:
        children.extend(
            [
                empty,
                db.Card(
                    [
                        db.SectionHeader(
                            "Pipeline register",
                            "No records are available in the current filtered scope.",
                        ),
                        table,
                    ]
                ),
            ]
        )
    else:
        children.append(
            db.Grid(
                [
                    db.Card([db.ComposedChart(operational_chart_data(records), x_key="scope", bar_keys=["rows_m"], line_keys=["sla_pct"], area_keys=["cost_usd"], title="Filtered volume, SLA, and compute", colors=CHART_COLORS, height=300)]),
                    db.Card([db.SectionHeader("Pipeline register", "The operational source of truth for the current filters."), table]),
                ],
                cols=2,
                gap=4,
            )
        )
    children.extend(
        [
            db.Card(
                [
                    db.Row(
                        [
                            db.Column([db.Text("Normalized data contract", variant="h3"), db.Text("Mock and Databricks SQL sources produce the same pipeline record shape.", muted=True)], gap=1),
                            db.Button("Hide SQL shape" if show_data_model else "Show SQL shape", on_click=lambda: set_show_data_model(not show_data_model), variant="secondary"),
                        ],
                        justify="between",
                        align="center",
                        wrap=True,
                    ),
                    *([db.Code(SQL_EXAMPLE, language="sql")] if show_data_model else []),
                ]
            ),
        ]
    )
    return db.Column(children, gap=4)


def pipelines_page(records: list[dict], selected_node: str, set_selected_node, job_state: str, set_job_state):
    nodes, edges = pipeline_flow(records)
    empty = _empty_state(records)
    if job_state == "pending":
        action_feedback = db.Alert("Simulated pipeline refresh is pending. No production job was started.", type="warning", title="Simulated action pending")
    elif job_state == "success":
        action_feedback = db.Alert("Simulated pipeline refresh completed and the acknowledgement was recorded.", type="success", title="Simulated action acknowledged")
    else:
        action_feedback = db.Alert(selected_node, type="info", title="Graph selection")
    children = [
        _page_heading("Pipeline flow", "Trace record movement across bronze, silver, and gold layers without losing the operating context.", f"{len(nodes)} nodes"),
    ]
    if empty:
        children.append(empty)
    children.extend(
        [
            db.Card([db.PipelineGraph(nodes, edges, title="Lakehouse dependency flow", empty_message="No pipeline nodes match the current filters.", on_node_click=lambda node: set_selected_node(f"{node.get('label', node['id'])} selected for operational review.")), action_feedback]),
            db.Row(
                [
                    db.Button("Run simulated refresh", on_click=lambda: set_job_state("pending"), disabled=job_state == "pending"),
                    db.Button("Complete simulated run", on_click=lambda: set_job_state("success"), variant="secondary", disabled=job_state != "pending"),
                ],
                gap=2,
                wrap=True,
            ),
        ]
    )
    return db.Column(children, gap=4)


def reliability_page(records: list[dict], selected_signal: str, set_selected_signal):
    empty = _empty_state(records)
    children = [
        _page_heading("Reliability signals", "Correlate cost, duration, failures, and success-rate movement before choosing an intervention.", "Filtered scope"),
    ]
    if empty:
        children.append(empty)
    else:
        children.extend(
            [
                db.Alert(selected_signal, type="info", title="Selected reliability signal"),
                db.Grid(
                    [
                        db.Card([db.ComposedChart(operational_chart_data(records), x_key="scope", bar_keys=["rows_m"], line_keys=["sla_pct"], area_keys=["cost_usd"], title="Filtered throughput, SLA, and cost", colors=CHART_COLORS, height=300)]),
                        db.Card([db.ScatterChart(records, x_key="cost_usd", y_key="latency_min", title="Run cost vs latency", color=CHART_COLORS[0], empty_message="No reliability points match the filters.", on_click=lambda point: set_selected_signal(f"{point.get('pipeline_label', 'Pipeline')} selected: ${point.get('cost_usd', 0)} cost and {point.get('latency_min', 0)}m latency."))]),
                    ],
                    cols=2,
                    gap=4,
                ),
                db.Card([db.Heatmap(reliability_heatmap_data(records), x_key="pipeline", y_key="layer", value_key="failures", title="Incidents by pipeline and layer", color=CHART_COLORS[0], on_click=lambda cell: set_selected_signal(f"{cell.get('pipeline', 'Pipeline')} recorded {cell.get('failures', 0)} incidents in {cell.get('layer', 'the selected layer')}."))]),
            ]
        )
    return db.Column(children, gap=4)


def triage_page(records: list[dict], selected_card: str, set_selected_card):
    columns = triage_columns(records)
    empty = _empty_state(records)
    children = [
        _page_heading("Triage queue", "Move from a health signal to an owner-ready queue with stable pipeline identities.", f"{sum(len(column['cards']) for column in columns)} cards"),
    ]
    if empty:
        children.append(empty)
    children.extend(
        [
            db.Alert(selected_card, type="info", title="Triage selection"),
            db.Card([db.KanbanBoard(columns, on_card_click=lambda card: set_selected_card(f"{card.get('title', card['id'])} opened from the triage queue."))]),
            db.Card([db.SectionHeader("Permission and error boundary", "Mutation controls should remain explicit even when a queue is read-only."), db.Alert("This showcase is read-only. A production implementation would report permission denial or a safe correlation ID here without exposing query details.", type="warning", title="No write permission configured")]),
        ]
    )
    return db.Column(children, gap=4)


def assistant_page(records: list[dict], prompt: str, set_prompt, assistant_status: str, assistant_answer: str, submit_prompt, finish_response):
    if assistant_status == "pending":
        transcript = db.ChatMessage("assistant", "A simulated response is pending while the pipeline context is evaluated.", name="Pipeline Assistant", tone="info")
    elif assistant_status == "complete":
        transcript = db.ChatMessage("assistant", assistant_answer, name="Pipeline Assistant", tone="success")
    else:
        transcript = db.ChatMessage("assistant", "No question submitted yet. Ask about freshness, cost, or pipelines at risk.", name="Pipeline Assistant")
    return db.Column(
        [
            _page_heading("Pipeline assistant", "Ask against the same filtered records shown in every other view; responses are visibly simulated.", f"{len(records)} records in context"),
            db.Grid(
                [
                    db.Card([db.SectionHeader("Operations conversation", "The assistant never starts a job or changes source data."), transcript, db.ChatInput(value=prompt, placeholder="Ask which pipeline needs attention…", on_change=set_prompt, on_submit=submit_prompt, loading=assistant_status == "pending", disabled=assistant_status == "pending"), db.Button("Complete simulated response", on_click=finish_response, variant="secondary", disabled=assistant_status != "pending")]),
                    db.Card([db.SectionHeader("Context supplied to the assistant", "Only normalized, currently filtered pipeline records are in scope."), db.Table(records, columns=[{"key": "pipeline_label", "label": "Pipeline"}, {"key": "status", "label": "Status"}, {"key": "freshness_min", "label": "Freshness"}, {"key": "cost_usd", "label": "Cost"}], pagination=10, empty_message="No records are available for assistant context.")]),
                ],
                cols=2,
                gap=4,
            ),
        ],
        gap=4,
    )


def _view_handler(set_active_view, view_key: str):
    def activate_view():
        set_active_view(view_key)

    return activate_view


def top_nav(active_view: str, set_active_view, set_show_brief):
    buttons = [
        db.Button(
            VIEW_LABELS[view_key],
            on_click=_view_handler(set_active_view, view_key),
            variant="primary" if active_view == view_key else "ghost",
            viewKey=view_key,
        )
        for view_key in VIEW_KEYS
    ]
    buttons.append(db.Button("Executive brief", on_click=lambda: set_show_brief(True), variant="secondary"))
    return db.Column(
        [
            db.Row(
                [
                    db.Column([db.Text("BrickflowUI", variant="h3"), db.Text("Pipeline Command Center", variant="caption", muted=True)], gap=0, style={"width": "auto", "flex": "0 0 auto"}),
                    db.Row(
                        buttons,
                        gap=1,
                        align="center",
                        wrap=True,
                        style={
                            "width": "auto",
                            "flex": "0 1 auto",
                            "minWidth": "0",
                            "justifyContent": "flex-start",
                        },
                    ),
                ],
                justify="between",
                align="center",
                wrap=True,
            )
        ],
        padding=3,
        style={"background": "var(--db-surface)", "borderBottom": "1px solid var(--db-border)", "position": "sticky", "top": "0", "zIndex": "20"},
    )


def executive_brief_modal(show_brief: bool, set_show_brief, records: list[dict]):
    attention = [row for row in records if row["status"] in {"Watch", "At Risk"}]
    return db.Modal(
        visible=show_brief,
        title="Executive brief",
        on_close=lambda: set_show_brief(False),
        size="lg",
        children=[
            db.Column(
                [
                    db.Alert(f"{len(attention)} visible pipelines need operational follow-up. Recover freshness and reliability before adding compute.", type="warning" if attention else "success", title="Current attention summary"),
                    db.Progress(94, label="Runbook coverage"),
                    db.Progress(91, label="Owner assignment coverage"),
                    db.Row([db.Button("Close", variant="secondary", on_click=lambda: set_show_brief(False)), db.Button("Simulated acknowledge", on_click=lambda: set_show_brief(False))], justify="end", gap=2),
                ],
                gap=3,
            )
        ],
    )


@app.page("/", title="Pipeline Command Center")
def command_center():
    active_view, set_active_view = db.use_state("overview")
    source_mode, set_source_mode = db.use_state("mock")
    domain, set_domain = db.use_state("all")
    pipeline, set_pipeline = db.use_state("all")
    period, set_period = db.use_state("YTD")
    search, set_search = db.use_state("")
    min_sla, set_min_sla = db.use_state(95.0)
    critical_only, set_critical_only = db.use_state(False)
    show_brief, set_show_brief = db.use_state(False)
    show_data_model, set_show_data_model = db.use_state(False)
    selected_node, set_selected_node = db.use_state("Select a graph node to inspect its operating state.")
    selected_signal, set_selected_signal = db.use_state("Select a chart point or heatmap cell for details.")
    selected_card, set_selected_card = db.use_state("Select a card to open its triage context.")
    job_state, set_job_state = db.use_state("idle")
    prompt, set_prompt = db.use_state("")
    assistant_status, set_assistant_status = db.use_state("empty")
    assistant_answer, set_assistant_answer = db.use_state("")

    source_result = db.use_memo(lambda: load_pipeline_source(source_mode), [source_mode])
    all_records, source = source_result
    normalized_search = search.strip().lower()
    records = [
        row
        for row in all_records
        if (domain == "all" or row["domain"] == domain)
        and (pipeline == "all" or row["pipeline"] == pipeline)
        and row["success_rate"] >= float(min_sla)
        and (not critical_only or row["status"] in {"Watch", "At Risk"})
        and (not normalized_search or normalized_search in row["pipeline_label"].lower() or normalized_search in row["owner"].lower())
    ]

    def submit_prompt(value: str):
        set_prompt(value.strip())
        set_assistant_status("pending")

    def finish_response():
        attention = [row for row in records if row["status"] in {"Watch", "At Risk"}]
        if attention:
            target = max(attention, key=lambda row: (row["incidents"], row["freshness_min"]))
            answer = f"Simulated analysis: {target['pipeline_label']} is the first review target at {target['freshness_min']}m freshness with {target['incidents']} incidents."
        else:
            answer = f"Simulated analysis: {len(records)} pipelines match the current filters and none are marked watch or at risk."
        set_assistant_answer(answer)
        set_assistant_status("complete")

    views = {
        "overview": lambda: overview_page(records, period, show_data_model, set_show_data_model),
        "pipelines": lambda: pipelines_page(records, selected_node, set_selected_node, job_state, set_job_state),
        "reliability": lambda: reliability_page(records, selected_signal, set_selected_signal),
        "triage": lambda: triage_page(records, selected_card, set_selected_card),
        "assistant": lambda: assistant_page(records, prompt, set_prompt, assistant_status, assistant_answer, submit_prompt, finish_response),
    }

    return db.Column(
        [
            top_nav(active_view, set_active_view, set_show_brief),
            db.Column(
                [
                    db.Row([db.Column([db.Text("Production pipeline operations", variant="h2"), db.Text("Freshness, reliability, cost, lineage, and triage from one normalized data boundary.", muted=True)], gap=1), db.Badge(f"Requested: {source['requested'].upper()} · Active: {source['active'].upper()}", color="gray")], justify="between", align="center", wrap=True),
                    _summary_strip(records, period),
                    _source_notice(source),
                    views[active_view](),
                    _filters(source_mode, set_source_mode, domain, set_domain, pipeline, set_pipeline, period, set_period, search, set_search, min_sla, set_min_sla, critical_only, set_critical_only),
                ],
                padding=4,
                gap=4,
                style={"maxWidth": "1480px", "margin": "0 auto", "width": "100%"},
            ),
            executive_brief_modal(show_brief, set_show_brief, records),
        ],
        gap=0,
        style={"minHeight": "100vh", "background": "var(--db-bg)"},
    )


if __name__ == "__main__":
    app.run()
