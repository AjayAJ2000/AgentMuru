from __future__ import annotations

from pathlib import Path

import plotly.graph_objects as go

import brickflowui as db
from brickflowui.databricks.sql import query_to_records


EXAMPLE_ROOT = Path(__file__).parent
LOGO = EXAMPLE_ROOT / "assets" / "brickflowui-mark.svg"

TRIAL_SITE_ROWS = [
    {"site": "Toyama", "patients": 128, "screen_failures": 11, "deviations": 2, "risk": "Low"},
    {"site": "Leiden", "patients": 119, "screen_failures": 15, "deviations": 3, "risk": "Moderate"},
    {"site": "Northbrook", "patients": 104, "screen_failures": 8, "deviations": 1, "risk": "Low"},
]

ENROLLMENT_TREND = [
    {"week": "W01", "enrolled": 17, "queries": 46, "ready": 95},
    {"week": "W02", "enrolled": 21, "queries": 43, "ready": 96},
    {"week": "W03", "enrolled": 23, "queries": 39, "ready": 97},
    {"week": "W04", "enrolled": 26, "queries": 34, "ready": 98},
]

SAFETY_HEATMAP = [
    {"week": "W01", "signal": "AE", "count": 6},
    {"week": "W01", "signal": "SAE", "count": 1},
    {"week": "W02", "signal": "AE", "count": 4},
    {"week": "W02", "signal": "SAE", "count": 0},
    {"week": "W03", "signal": "AE", "count": 7},
    {"week": "W03", "signal": "SAE", "count": 2},
]

PIPELINE_NODES = [
    {"id": "consent", "label": "Consent intake", "status": "success", "layer": "capture"},
    {"id": "cleaning", "label": "Clinical cleaning", "status": "warning", "layer": "quality"},
    {"id": "safety", "label": "Safety review", "status": "info", "layer": "review"},
    {"id": "submission", "label": "Regulatory package", "status": "success", "layer": "publish"},
]

PIPELINE_EDGES = [
    {"from": "consent", "to": "cleaning"},
    {"from": "cleaning", "to": "safety"},
    {"from": "safety", "to": "submission"},
]

ROLE_HINT = "Use x-brickflow-user-id and x-brickflow-user-roles headers when testing locally."

app = db.App(
    title="Clinical Trial Command Center",
    asset_roots=[EXAMPLE_ROOT],
    logo=str(LOGO) if LOGO.exists() else None,
    favicon=str(LOGO) if LOGO.exists() else None,
    auth_mode="user",
    auth_provider=db.HeaderAuthProvider(),
    allow_anonymous=False,
    loading={
        "title": "Clinical Trial Command Center",
        "message": "Validating trial access and preparing study metrics...",
        "animation": "pulse",
        "asset": str(LOGO) if LOGO.exists() else None,
    },
    theme={
        "branding": {"title": "Clinical Trial Command Center"},
        "colors": {
            "primary": "#7C2D12",
            "primary_hover": "#9A3412",
            "background": "#FFF9F7",
            "surface": "#FFFFFF",
            "text": "#1F2937",
            "text_muted": "#6B7280",
            "border": "#F0D7CF",
            "info": "#2563EB",
        },
    },
)


def load_uc_records() -> list[dict]:
    sql = """
    SELECT study_site AS site,
           enrolled_patients AS patients,
           screen_failures,
           protocol_deviations AS deviations,
           operational_risk AS risk
    FROM main.clinical.trial_site_daily
    ORDER BY study_site
    LIMIT 50
    """
    try:
        return query_to_records(sql)
    except Exception:
        return TRIAL_SITE_ROWS


def enrollment_figure():
    fig = go.Figure()
    fig.add_bar(x=[row["week"] for row in ENROLLMENT_TREND], y=[row["enrolled"] for row in ENROLLMENT_TREND], name="Enrolled")
    fig.add_scatter(x=[row["week"] for row in ENROLLMENT_TREND], y=[row["queries"] for row in ENROLLMENT_TREND], name="Open queries", mode="lines+markers", yaxis="y2")
    fig.update_layout(
        title="Enrollment vs open queries",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#1F2937"},
        yaxis2={"overlaying": "y", "side": "right"},
        margin={"l": 30, "r": 30, "t": 44, "b": 24},
    )
    return fig


@app.page("/", title="Study Home", icon="Home", access="user")
def home():
    return db.Column(
        [
            db.Hero(
                "Clinical trial dashboards with Databricks-ready controls",
                subtitle="This example combines auth-gated pages, direct Unity Catalog query patterns, Plotly, pipeline visualization, and trial operations dashboards.",
                eyebrow="Clinical operations",
                badges=[db.Badge("Auth required", color="red"), db.Badge("Plotly", color="blue"), db.Badge("Databricks SQL", color="purple")],
                visual=db.Card([db.GaugeChart(97, title="Readiness", label="study launch confidence")]),
            ),
            db.Alert(ROLE_HINT, type="info", title="Local testing"),
            db.Grid(
                [
                    db.Card([db.Stat("Sites live", "3", delta="+1", delta_type="increase"), db.Text("Promote one site per study or region page.", variant="caption", muted=True)]),
                    db.Card([db.Stat("Patients enrolled", "351", delta="+14", delta_type="increase"), db.Text("Use Databricks SQL to replace mock numbers cleanly.", variant="caption", muted=True)]),
                    db.Card([db.Stat("Protocol deviations", "6", delta="-1", delta_type="decrease"), db.Text("Safety and quality signals can share the same shell.", variant="caption", muted=True)]),
                ],
                cols=3,
                gap=4,
            ),
        ],
        gap=5,
        padding=5,
    )


@app.page("/overview", title="Trial Overview", icon="LayoutDashboard", access="user", roles=["clinician", "ops"])
def overview():
    rows = load_uc_records()
    selected_site, set_selected_site = db.use_state("All sites")

    return db.Column(
        [
            db.SectionHeader("Trial overview", subtitle="Executive view of enrollment, site readiness, and protocol quality."),
            db.Row([db.Badge("Clinician / Ops", color="green"), db.Badge(selected_site, color="orange")], gap=2),
            db.Grid(
                [
                    db.Card([db.ComposedChart(ENROLLMENT_TREND, x_key="week", bar_keys=["enrolled"], line_keys=["ready"], title="Enrollment and readiness", height=320)]),
                    db.Card([db.Plot(enrollment_figure())]),
                ],
                cols=2,
                gap=4,
            ),
            db.Card(
                [
                    db.Row(
                        [
                            db.Text("Site scorecard", variant="h3"),
                            db.Select(
                                "site",
                                label="Highlight site",
                                options=[{"label": "All sites", "value": "All sites"}] + [{"label": row["site"], "value": row["site"]} for row in rows],
                                value=selected_site,
                                on_change=set_selected_site,
                            ),
                        ],
                        justify="between",
                        align="center",
                        wrap=True,
                    ),
                    db.Spacer(2),
                    db.Table(rows, columns=[
                        {"key": "site", "label": "Site", "sortable": True},
                        {"key": "patients", "label": "Patients", "sortable": True},
                        {"key": "screen_failures", "label": "Screen failures", "sortable": True},
                        {"key": "deviations", "label": "Protocol deviations", "sortable": True},
                        {"key": "risk", "label": "Risk", "sortable": True},
                    ], exportable=True),
                ]
            ),
        ],
        gap=5,
        padding=5,
    )


@app.page("/safety", title="Safety View", icon="Activity", access="user", roles=["clinician"])
def safety():
    return db.Column(
        [
            db.SectionHeader("Safety review", subtitle="Heatmaps, timelines, and alerts keep review teams grounded in current signal movement."),
            db.Alert("This page is role-gated to clinicians in order to keep safety workflows separated from general operational views.", type="warning", title="Safety access"),
            db.Grid(
                [
                    db.Card([db.Heatmap(SAFETY_HEATMAP, x_key="week", y_key="signal", value_key="count", title="Safety heatmap")]),
                    db.Card([db.Timeline([
                        {"title": "DSMB packet ready", "time": "Today 09:30", "description": "Latest safety packet staged for reviewer sign-off."},
                        {"title": "Grade 3 event review", "time": "Today 11:10", "description": "Cross-functional assessment routed to clinical lead."},
                    ])]),
                ],
                cols=2,
                gap=4,
            ),
        ],
        gap=5,
        padding=5,
    )


@app.page("/dataops", title="Data Operations", icon="Database", access="user", roles=["ops"])
def dataops():
    return db.Column(
        [
            db.SectionHeader("Study data operations", subtitle="Direct Unity Catalog browsing, SQL warehouse selection, and pipeline topology."),
            db.Grid(
                [
                    db.Card([db.WarehouseSelector(selected_id="clinical-warehouse"), db.Spacer(2), db.CatalogBrowser()]),
                    db.Card([db.PipelineGraph(PIPELINE_NODES, PIPELINE_EDGES, title="Clinical data flow"), db.Spacer(2), db.Text("The same portal can mix controlled navigation with visual lineage and query operations.", muted=True)]),
                ],
                cols=2,
                gap=4,
            ),
        ],
        gap=5,
        padding=5,
    )


if __name__ == "__main__":
    app.run()
