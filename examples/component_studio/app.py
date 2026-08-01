from __future__ import annotations

from pathlib import Path

import brickflowui as db


EXAMPLE_ROOT = Path(__file__).parent
LOCAL_LOGO = EXAMPLE_ROOT / "assets" / "brickflowui-mark.svg"

app = db.App(
    title="BrickflowUI Component Studio",
    asset_roots=[EXAMPLE_ROOT],
    logo=str(LOCAL_LOGO) if LOCAL_LOGO.exists() else None,
    favicon=str(LOCAL_LOGO) if LOCAL_LOGO.exists() else None,
    loading={
        "title": "BrickflowUI Studio",
        "message": "Preparing interactive component documentation...",
        "animation": "pulse",
        "asset": str(LOCAL_LOGO) if LOCAL_LOGO.exists() else None,
    },
    theme={
        "branding": {"title": "BrickflowUI Component Studio"},
        "colors": {
            "primary": "#C2410C",
            "primary_hover": "#9A3412",
            "background": "#FFF8F1",
            "surface": "#FFFFFF",
            "text": "#111827",
            "text_muted": "#6B7280",
            "border": "#F2D8C2",
            "info": "#0EA5E9",
        },
        "motion": {
            "duration_normal": "260ms",
            "duration_slow": "420ms",
        },
    },
)


TEAM_OPTIONS = [
    {"label": "Platform", "value": "platform"},
    {"label": "Operations", "value": "operations"},
    {"label": "Analytics", "value": "analytics"},
]

STATUS_ITEMS = [
    {"label": "Runtime", "value": "Healthy", "status": "success", "detail": "WebSocket session active"},
    {"label": "Motion", "value": "Enabled", "status": "info", "detail": "Animation props enabled"},
    {"label": "Docs", "value": "Interactive", "status": "warning", "detail": "Example doubles as reference"},
    {"label": "Media", "value": "Ready", "status": "success", "detail": "Image, GIF, and video support"},
]

TREND = [
    {"week": "W01", "runs": 128, "success_rate": 97.8, "latency": 4.1},
    {"week": "W02", "runs": 136, "success_rate": 98.2, "latency": 3.9},
    {"week": "W03", "runs": 141, "success_rate": 98.5, "latency": 3.6},
    {"week": "W04", "runs": 149, "success_rate": 98.9, "latency": 3.4},
]

PIPELINE_NODES = [
    {"id": "ingest", "label": "Ingest", "status": "success", "layer": "source"},
    {"id": "bronze", "label": "Bronze", "status": "success", "layer": "bronze"},
    {"id": "silver", "label": "Silver", "status": "warning", "layer": "silver"},
    {"id": "gold", "label": "Gold", "status": "info", "layer": "gold"},
]

PIPELINE_EDGES = [
    {"from": "ingest", "to": "bronze"},
    {"from": "bronze", "to": "silver"},
    {"from": "silver", "to": "gold"},
]

TABLE_DATA = [
    {"component": "Table", "category": "Data", "state": "Stable", "notes": "CSV export enabled"},
    {"component": "PipelineGraph", "category": "Visualization", "state": "Stable", "notes": "Node click drilldowns"},
    {"component": "Video", "category": "Media", "state": "New", "notes": "Direct script-based video rendering"},
    {"component": "Toast", "category": "Feedback", "state": "Stable", "notes": "Dismissible and state-safe"},
]

TIMELINE_ITEMS = [
    {"title": "Component tree mounted", "time": "09:00", "description": "Initial render completed with motion-safe defaults."},
    {"title": "User changed filter", "time": "09:02", "description": "Controlled input updated Python state and rerendered charts."},
    {"title": "Pipeline node clicked", "time": "09:05", "description": "Node metadata was passed through the websocket payload."},
]

KANBAN_COLUMNS = [
    {"id": "todo", "label": "To Review", "cards": [{"id": "a", "title": "Drawer patterns", "subtitle": "Navigation and detail flows", "status": "Watch"}]},
    {"id": "doing", "label": "Live", "cards": [{"id": "b", "title": "Media support", "subtitle": "Image/GIF/video in Python", "status": "Running"}]},
    {"id": "done", "label": "Released", "cards": [{"id": "c", "title": "Responsive nav", "subtitle": "Mobile sidebar and tabs", "status": "Healthy"}]},
]

VIDEO_URL = "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4"
GIF_URL = "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExMjFhNnM0aG9iaDJ1N2s4bWZmOHh5eXQwdnVmN2o2YTVubXd3NW1hYiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/xT9IgzoKnwFNmISR8I/giphy.gif"


def section_badges(scope: str, team: str) -> db.VNode:
    return db.Row(
        [
            db.Badge(f"Scope: {scope.title()}", color="orange"),
            db.Badge(f"Team: {team.title()}", color="purple"),
            db.Badge("Interactive", color="green"),
        ],
        gap=2,
        wrap=True,
    )


@app.page("/", title="Studio", icon="LayoutDashboard")
def studio():
    section, set_section = db.use_state("overview")
    search, set_search = db.use_state("")
    team, set_team = db.use_state("platform")
    detail_open, set_detail_open = db.use_state(False)
    modal_open, set_modal_open = db.use_state(False)
    popup_open, set_popup_open = db.use_state(False)
    toast_visible, set_toast_visible = db.use_state(False)
    slider_value, set_slider_value = db.use_state(72.0)
    toggle_value, set_toggle_value = db.use_state(True)
    selected_tags, set_selected_tags = db.use_state(["platform", "media"])
    selected_range, set_selected_range = db.use_state({"start": "2026-05-01", "end": "2026-05-07"})
    selected_node, set_selected_node = db.use_state("ingest")
    chat_value, set_chat_value = db.use_state("")
    last_prompt, set_last_prompt = db.use_state("Summarize the dashboard composition patterns.")

    filtered_rows = [
        row for row in TABLE_DATA
        if not search.strip()
        or search.lower() in row["component"].lower()
        or search.lower() in row["category"].lower()
    ]

    view_map = {
        "overview": db.Column(
            [
                db.Hero(
                    "Component Studio for Real BrickflowUI Apps",
                    subtitle="This app is intentionally interactive. Use it as a living reference for layouts, forms, motion, media, charts, pipeline views, and assistant-style UX.",
                    eyebrow="Documentation-quality example",
                    badges=[db.Badge("Supported surface", color="orange"), db.Badge("Responsive", color="green")],
                    actions=[
                        db.Button("Open detail drawer", on_click=lambda: set_detail_open(True), animated=True, animation="fade-up"),
                        db.Button("Trigger toast", on_click=lambda: set_toast_visible(True), variant="secondary"),
                    ],
                    visual=db.Card(
                        [
                            db.GaugeChart(94, title="Readiness", label="Example quality"),
                            db.Text("The right-hand hero visual can be any VNode tree.", variant="caption", muted=True),
                        ],
                        elevated=True,
                    ),
                ),
                db.StatusStrip(STATUS_ITEMS, title="Framework Signals", animated=True, animation="fade-up"),
                db.Grid(
                    [
                        db.Card(
                            [
                                db.SectionHeader("Live filters", subtitle="Controlled inputs rerender without losing values.", animated=True),
                                db.Input("search", label="Search components", value=search, on_change=set_search),
                                db.Select("team", label="Audience", options=TEAM_OPTIONS, value=team, on_change=set_team),
                                db.Slider("confidence", label=f"Readiness: {int(slider_value)}%", min=0, max=100, step=1, value=slider_value, on_change=set_slider_value),
                                db.Toggle("motion", label="Enable motion", checked=toggle_value, on_change=set_toggle_value),
                                db.Button("Open popup", on_click=lambda: set_popup_open(True), variant="outline"),
                            ],
                            hover=True,
                            animated=True,
                        ),
                        db.Card(
                            [
                                db.SectionHeader("Documentation promises", subtitle="The framework should explain itself clearly.", animated=True),
                                db.Timeline(TIMELINE_ITEMS, animated=True),
                            ],
                            animated=True,
                            animation="fade-up",
                            animation_delay=0.08,
                        ),
                    ],
                    cols=2,
                    gap=4,
                ),
                db.Card(
                    [
                        db.SectionHeader("Component inventory", subtitle="Tables, badges, sorting, export, and click-through behavior."),
                        db.Table(
                            data=filtered_rows,
                            columns=[
                                {"key": "component", "label": "Component", "sortable": True},
                                {"key": "category", "label": "Category", "sortable": True},
                                {"key": "state", "label": "State", "sortable": True},
                                {"key": "notes", "label": "Notes"},
                            ],
                            pagination=6,
                            exportable=True,
                        ),
                    ],
                    animated=True,
                ),
            ],
            gap=5,
        ),
        "visuals": db.Column(
            [
                db.SectionHeader("Charts, plotly, and pipeline views", subtitle="Choose one surface or combine them for richer operational storytelling.", animated=True),
                db.Grid(
                    [
                        db.Card([db.ComposedChart(TREND, x_key="week", bar_keys=["runs"], line_keys=["success_rate"], title="Runs vs success rate", height=320)], animated=True),
                        db.Card([db.LineChart(TREND, x_key="week", y_keys=["latency"], title="Latency trend", height=320)], animated=True, animation_delay=0.05),
                    ],
                    cols=2,
                    gap=4,
                ),
                db.Grid(
                    [
                        db.Card([db.PipelineGraph(PIPELINE_NODES, PIPELINE_EDGES, title="Pipeline map", on_node_click=lambda payload: set_selected_node(payload["id"]))]),
                        db.Card(
                            [
                                db.Text("Selected node", variant="h3"),
                                db.Text(selected_node),
                                db.Spacer(2),
                                db.Plot(
                                    {
                                        "data": [
                                            {"type": "bar", "x": ["Freshness", "Reliability", "Cost"], "y": [92, 97, 81], "marker": {"color": ["#C2410C", "#0EA5E9", "#FDBA74"]}},
                                        ],
                                        "layout": {
                                            "title": "Native Plotly support",
                                            "paper_bgcolor": "rgba(0,0,0,0)",
                                            "plot_bgcolor": "rgba(0,0,0,0)",
                                            "font": {"color": "#111827"},
                                        },
                                    }
                                ),
                            ]
                        ),
                    ],
                    cols=2,
                    gap=4,
                ),
            ],
            gap=5,
        ),
        "media": db.Column(
            [
                db.SectionHeader("Media, loading, and motion", subtitle="Images, GIFs, and videos can live directly in your Python script.", animated=True),
                db.Grid(
                    [
                        db.Card(
                            [
                                db.Text("Local or remote image", variant="h3"),
                                db.Image(str(LOCAL_LOGO) if LOCAL_LOGO.exists() else GIF_URL, alt="BrickflowUI logo", fit="contain", height="180px", caption="Local file paths are now served automatically.", animated=True, animation="float"),
                            ]
                        ),
                        db.Card(
                            [
                                db.Text("Animated GIF via Image", variant="h3"),
                                db.Image(GIF_URL, alt="Animated loading sample", fit="cover", height="180px", caption="GIFs work through the same image component.", animated=True, animation="pulse"),
                            ]
                        ),
                    ],
                    cols=2,
                    gap=4,
                ),
                db.Card(
                    [
                        db.Text("Video surface", variant="h3"),
                        db.Video(VIDEO_URL, caption="Videos can be embedded directly as part of onboarding, product storytelling, or incident walkthroughs.", animated=True),
                    ]
                ),
            ],
            gap=5,
        ),
        "workflow": db.Column(
            [
                db.SectionHeader("Workflow components", subtitle="Use these for copilots, release boards, triage, and guided flows.", animated=True),
                db.Grid(
                    [
                        db.Card([db.Stepper([{"label": "Draft"}, {"label": "Review"}, {"label": "Release"}], active=1, animated=True)]),
                        db.Card([db.KanbanBoard(KANBAN_COLUMNS, on_card_click=lambda _: set_detail_open(True), animated=True)]),
                    ],
                    cols=2,
                    gap=4,
                ),
                db.Card(
                    [
                        db.Text("Assistant panel", variant="h3"),
                        db.ChatMessage("assistant", "I can help explain which BrickflowUI components fit each portal pattern.", name="Studio Guide", animated=True),
                        db.ChatMessage("user", last_prompt, name="Engineer", animated=True),
                        db.ChatInput(value=chat_value, on_change=set_chat_value, on_submit=lambda value: (set_last_prompt(value), set_chat_value("")), placeholder="Ask how to build a portal, dashboard, or landing page.", animated=True),
                    ]
                ),
            ],
            gap=5,
        ),
    }

    return db.Column(
        [
            db.Row(
                [
                    db.Column(
                        [
                            db.Text("BrickflowUI Component Studio", variant="h2"),
                            db.Text("An opinionated, interactive reference app for evaluating the framework.", muted=True),
                        ]
                    ),
                    section_badges(section, team),
                ],
                justify="between",
                align="center",
                wrap=True,
            ),
            db.Breadcrumbs([{"label": "Docs"}, {"label": "Examples"}, {"label": "Component Studio"}]),
            db.Tabs(
                [
                    db.TabItem("Overview", [view_map["overview"]]),
                    db.TabItem("Visuals", [view_map["visuals"]]),
                    db.TabItem("Media", [view_map["media"]]),
                    db.TabItem("Workflow", [view_map["workflow"]]),
                ],
                default_active={"overview": 0, "visuals": 1, "media": 2, "workflow": 3}[section],
                on_change=lambda index: set_section(["overview", "visuals", "media", "workflow"][index]),
            ),
            db.Row(
                [
                    db.MultiSelect(
                        "tags",
                        label="Highlight focus areas",
                        options=[
                            {"label": "Platform", "value": "platform"},
                            {"label": "Media", "value": "media"},
                            {"label": "Security", "value": "security"},
                        ],
                        values=selected_tags,
                        on_change=set_selected_tags,
                    ),
                    db.DateRangePicker("window", label="Documentation window", start=selected_range["start"], end=selected_range["end"], on_change=set_selected_range),
                ],
                gap=4,
                wrap=True,
            ),
            db.Drawer(
                visible=detail_open,
                title="Why this example matters",
                on_close=lambda: set_detail_open(False),
                children=[
                    db.Text("This example is designed to be read like product documentation, not just a demo."),
                    db.Spacer(2),
                    db.Alert("Use it to validate component behavior, responsiveness, form handling, and motion in one place.", type="info"),
                ],
            ),
            db.Modal(
                visible=modal_open,
                title="Studio modal",
                on_close=lambda: set_modal_open(False),
                children=[db.Text("Modals remain responsive and keep their close controls intact on mobile."), db.Spacer(2), db.Button("Close", on_click=lambda: set_modal_open(False))],
            ),
            db.Popup(
                visible=popup_open,
                title="Quick peek",
                on_close=lambda: set_popup_open(False),
                children=[db.Text("Popup flows are useful for lightweight acknowledgements and in-place confirmations."), db.Spacer(2), db.Button("Close popup", on_click=lambda: set_popup_open(False), variant="secondary")],
            ),
            db.Toast(
                "The notification system now supports dismissal without page refresh.",
                title="Toast demo",
                type="success",
                visible=toast_visible,
                on_close=lambda: set_toast_visible(False),
                auto_hide_ms=2400,
            ),
        ],
        padding=5,
        gap=5,
        style={"maxWidth": "1400px", "margin": "0 auto"},
    )


if __name__ == "__main__":
    app.run()
