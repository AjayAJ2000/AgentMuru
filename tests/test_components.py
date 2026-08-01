import re
from pathlib import Path

import brickflowui as db


def test_new_components_serialize_expected_props_and_nested_actions():
    node = db.Column(
        [
            db.Breadcrumbs(
                [
                    {"label": "Home", "path": "/"},
                    {"label": "Studio", "path": "/studio"},
                    {"label": "Preview"},
                ]
            ),
            db.EmptyState(
                title="No pipelines",
                message="Add a pipeline or adjust your filters.",
                actions=[db.Button("Create", on_click=lambda: None)],
            ),
            db.Drawer(visible=True, title="Details", children=[db.Text("Body")]),
            db.Accordion(
                [
                    db.AccordionItem("Section A", [db.Text("A content")]),
                    db.AccordionItem("Section B", [db.Text("B content")]),
                ],
                default_open=[0],
                allow_multiple=True,
            ),
            db.DateRangePicker(name="window", start="2026-04-01", end="2026-04-07", loading=True),
            db.MultiSelect(
                name="layers",
                options=[{"label": "Bronze", "value": "bronze"}],
                values=["bronze"],
                loading=True,
            ),
            db.Popup(visible=True, title="Quick action", children=[db.Text("Body")]),
            db.Toast("Saved", title="Success", on_close=lambda: None, auto_hide_ms=1500),
            db.Image("https://example.com/preview.png", alt="Preview", caption="Example image"),
            db.Video("https://example.com/demo.mp4", poster="https://example.com/poster.png", caption="Example video"),
            db.Timeline([{"title": "Run started", "time": "09:30"}]),
            db.SparklineStat(
                label="Freshness",
                value="17 min",
                data=[{"day": "Mon", "value": 12}, {"day": "Tue", "value": 17}],
                x_key="day",
                y_key="value",
            ),
        ]
    )

    payload = node.serialize({})
    rendered_types = [child["type"] for child in payload["children"]]

    assert "Breadcrumbs" in rendered_types
    assert "EmptyState" in rendered_types
    assert "Drawer" in rendered_types
    assert "Accordion" in rendered_types
    assert "DateRangePicker" in rendered_types
    assert "MultiSelect" in rendered_types
    assert "Popup" in rendered_types
    assert "Toast" in rendered_types
    assert "Image" in rendered_types
    assert "Video" in rendered_types
    assert "Timeline" in rendered_types
    assert "SparklineStat" in rendered_types

    empty_state = next(child for child in payload["children"] if child["type"] == "EmptyState")
    popup = next(child for child in payload["children"] if child["type"] == "Popup")
    toast = next(child for child in payload["children"] if child["type"] == "Toast")
    image = next(child for child in payload["children"] if child["type"] == "Image")
    video = next(child for child in payload["children"] if child["type"] == "Video")
    date_range = next(child for child in payload["children"] if child["type"] == "DateRangePicker")
    multiselect = next(child for child in payload["children"] if child["type"] == "MultiSelect")
    assert empty_state["props"]["title"] == "No pipelines"
    assert empty_state["props"]["actions"][0]["type"] == "Button"
    assert popup["props"]["title"] == "Quick action"
    assert "close" in toast["props"]
    assert toast["props"]["autoHideMs"] == 1500
    assert image["props"]["caption"] == "Example image"
    assert video["props"]["poster"] == "https://example.com/poster.png"
    assert date_range["props"]["loading"] is True
    assert multiselect["props"]["loading"] is True


def test_interactive_controls_serialize_busy_state_motion_and_placeholders():
    node = db.Column(
        [
            db.Select(
                name="site",
                options=[{"label": "Network", "value": "network"}],
                value="network",
                loading=True,
                animated=True,
                animation="fade-up",
                animation_delay=0.2,
            ),
            db.Checkbox(
                name="urgent",
                label="Urgent only",
                checked=True,
                loading=True,
                animated=True,
                animation="fade-up",
                animation_delay=0.3,
            ),
            db.Toggle(
                name="bench",
                label="Show benchmark",
                checked=False,
                loading=True,
                animated=True,
                animation="fade-up",
                animation_delay=0.4,
            ),
            db.Slider(
                name="confidence",
                label="Confidence",
                value=92,
                min=0,
                max=100,
                disabled=True,
                loading=True,
                animated=True,
                animation="fade-up",
                animation_delay=0.5,
            ),
            db.Tabs(
                [db.TabItem("Overview", [db.Text("Body")])],
                animated=True,
                animation="fade-up",
                animation_delay=0.6,
            ),
            db.MultiSelect(
                name="layers",
                options=[{"label": "Bronze", "value": "bronze"}],
                values=[],
                placeholder="Choose layers",
                animated=True,
                animation="fade-up",
                animation_delay=0.7,
            ),
            db.Table(
                data=[],
                columns=[{"key": "name", "label": "Name"}],
                error_message="Warehouse query failed",
            ),
            db.Sidebar(
                items=[db.NavItem("Overview", "/")],
                show_theme_toggle=True,
                sticky=False,
            ),
        ]
    )

    payload = node.serialize({})
    rendered = {child["type"]: child for child in payload["children"]}

    assert rendered["Select"]["props"]["loading"] is True
    assert rendered["Select"]["props"]["animation"] == "fade-up"
    assert rendered["Checkbox"]["props"]["loading"] is True
    assert rendered["Toggle"]["props"]["loading"] is True
    assert rendered["Slider"]["props"]["disabled"] is True
    assert rendered["Slider"]["props"]["loading"] is True
    assert rendered["Tabs"]["props"]["animated"] is True
    assert rendered["MultiSelect"]["props"]["placeholder"] == "Choose layers"
    assert rendered["Table"]["props"]["errorMessage"] == "Warehouse query failed"
    assert rendered["Sidebar"]["props"]["showThemeToggle"] is True
    assert rendered["Sidebar"]["props"]["sticky"] is False


def test_navigation_media_and_embed_components_serialize_new_branding_props():
    node = db.Column(
        [
            db.TopNav(
                items=[db.NavItem("Overview", "/"), db.NavItem("Pipelines", "/pipelines", badge="12")],
                brand_name="Acme Analytics",
                tagline="React components. Python syntax.",
                logo="/logo.svg",
                actions=[db.Button("Export")],
                show_theme_toggle=True,
            ),
            db.ThemeToggle(),
            db.Image("/logo.svg", alt="Acme", variant="inline"),
            db.Image("/avatar.png", alt="Operator", variant="avatar", width="40px"),
            db.Hero(
                "Command center",
                tagline="Built for operating teams",
                image="/mark.svg",
                image_alt="Brand mark",
            ),
            db.Embed("https://example.com/embed", title="Embedded dashboard"),
        ]
    )

    payload = node.serialize({})
    rendered = {child["type"]: child for child in payload["children"]}
    images = [child for child in payload["children"] if child["type"] == "Image"]

    assert rendered["TopNav"]["props"]["tagline"] == "React components. Python syntax."
    assert rendered["TopNav"]["props"]["showThemeToggle"] is True
    assert rendered["ThemeToggle"]["props"]["label"] == "Theme"
    assert images[0]["props"]["variant"] == "inline"
    assert images[1]["props"]["variant"] == "avatar"
    assert rendered["Hero"]["props"]["image"] == "/mark.svg"
    assert rendered["Hero"]["props"]["tagline"] == "Built for operating teams"
    assert rendered["Embed"]["props"]["title"] == "Embedded dashboard"


def test_input_and_chatinput_serialize_debounced_sync_props():
    node = db.Column(
        [
            db.Input(
                name="search",
                value="bronze",
                debounce_ms=250,
                change_strategy="debounce",
                sync_on_blur=False,
            ),
            db.ChatInput(
                value="hello",
                debounce_ms=220,
                change_strategy="immediate",
            ),
        ]
    )

    payload = node.serialize({})
    input_node = next(child for child in payload["children"] if child["type"] == "Input")
    chat_node = next(child for child in payload["children"] if child["type"] == "ChatInput")

    assert input_node["props"]["debounceMs"] == 250
    assert input_node["props"]["changeStrategy"] == "debounce"
    assert input_node["props"]["syncOnBlur"] is False
    assert chat_node["props"]["debounceMs"] == 220
    assert chat_node["props"]["changeStrategy"] == "immediate"


def test_chart_components_expose_loading_empty_and_click_handlers():
    chart = db.BarChart(
        data=[],
        x_key="week",
        y_keys=["runs"],
        loading=True,
        empty_message="Nothing here",
        on_click=lambda payload: payload,
    )

    registry = {}
    payload = chart.serialize(registry)

    assert payload["props"]["loading"] is True
    assert payload["props"]["emptyMessage"] == "Nothing here"
    assert "click" in payload["props"]
    assert payload["props"]["click"] in registry


def test_table_can_be_marked_exportable():
    table = db.Table(
        data=[{"id": 1, "name": "A"}],
        columns=[{"key": "id", "label": "ID"}, {"key": "name", "label": "Name"}],
        exportable=True,
    )

    payload = table.serialize({})

    assert payload["props"]["exportable"] is True


def test_015_visual_components_serialize_callbacks_and_props():
    node = db.Column(
        [
            db.Hero(
                "Pipeline command center",
                subtitle="Observe jobs, tables, and SLAs.",
                eyebrow="Data platform",
                badges=[db.Badge("Live", color="green")],
                actions=[db.Button("Refresh")],
                animation="float",
            ),
            db.SectionHeader("Lakehouse health", actions=[db.Button("Export")], animated=True),
            db.StatusStrip([{"label": "Freshness", "value": "11m", "status": "healthy"}], animated=True, animation="fade-up"),
            db.Stepper([{"label": "Bronze"}, {"label": "Silver"}], active=1, animated=True),
            db.KanbanBoard(
                [{"id": "todo", "label": "Todo", "cards": [{"id": "a", "title": "Fix SLA"}]}],
                on_card_click=lambda payload: payload,
                animated=True,
            ),
            db.ChatMessage("assistant", "I found two delayed jobs.", name="Ops Copilot", animated=True),
            db.ChatInput(on_change=lambda value: value, on_submit=lambda value: value, animated=True),
        ]
    )

    registry = {}
    payload = node.serialize(registry)
    rendered_types = [child["type"] for child in payload["children"]]

    assert "Hero" in rendered_types
    assert "SectionHeader" in rendered_types
    assert "StatusStrip" in rendered_types
    assert "Stepper" in rendered_types
    assert "KanbanBoard" in rendered_types
    assert "ChatMessage" in rendered_types
    assert "ChatInput" in rendered_types

    kanban = next(child for child in payload["children"] if child["type"] == "KanbanBoard")
    chat_input = next(child for child in payload["children"] if child["type"] == "ChatInput")

    assert kanban["props"]["cardClick"] in registry
    assert payload["children"][0]["props"]["animation"] == "float"
    assert payload["children"][1]["props"]["animated"] is True
    assert chat_input["props"]["change"] in registry
    assert chat_input["props"]["submit"] in registry


def test_015_chart_and_pipeline_components_serialize_expected_props():
    charts = [
        db.ScatterChart([{"x": 1, "y": 2}], x_key="x", y_key="y", on_click=lambda payload: payload),
        db.ComposedChart([{"day": "Mon", "runs": 10, "sla": 96}], x_key="day", bar_keys=["runs"], line_keys=["sla"]),
        db.GaugeChart(91, label="Reliability"),
        db.RadarChart([{"metric": "Freshness", "score": 90}], angle_key="metric", value_keys=["score"]),
        db.Heatmap([{"hour": "09", "layer": "Bronze", "failures": 1}], x_key="hour", y_key="layer", value_key="failures"),
        db.FunnelChart([{"label": "Raw", "value": 100}]),
        db.TreeMap([{"name": "Storage", "value": 42}]),
        db.PipelineGraph(
            nodes=[{"id": "bronze", "label": "Bronze", "status": "running"}],
            edges=[],
            on_node_click=lambda payload: payload,
        ),
    ]

    registry = {}
    payloads = [chart.serialize(registry) for chart in charts]
    types = [payload["type"] for payload in payloads]

    assert types == [
        "ScatterChart",
        "ComposedChart",
        "GaugeChart",
        "RadarChart",
        "Heatmap",
        "FunnelChart",
        "TreeMap",
        "PipelineGraph",
    ]
    assert payloads[0]["props"]["click"] in registry
    assert payloads[-1]["props"]["nodeClick"] in registry


def test_databricks_components_serialize_server_driven_state_and_events():
    catalog = db.CatalogBrowser(
        catalogs=[
            {
                "name": "main",
                "schemas": [
                    {
                        "name": "default",
                        "tables": [{"name": "events", "full_name": "main.default.events"}],
                    }
                ],
            }
        ],
        selected={"catalog": "main", "schema": "default", "table": "events"},
        on_select=lambda value: value,
        loading=True,
    )
    warehouse = db.WarehouseSelector(
        warehouses=[{"id": "w1", "name": "Starter", "state": "RUNNING"}],
        selected_id="w1",
        on_select=lambda value: value,
        error="Permission denied",
    )
    job = db.JobTrigger(
        "42",
        on_trigger=lambda value: value,
        status="QUEUED",
        run_id="99",
        disabled=True,
    )
    registry = {}

    catalog_payload = catalog.serialize(registry)
    warehouse_payload = warehouse.serialize(registry)
    job_payload = job.serialize(registry)

    assert catalog_payload["props"]["catalogs"][0]["name"] == "main"
    assert catalog_payload["props"]["loading"] is True
    assert catalog_payload["props"]["select"] in registry
    assert warehouse_payload["props"]["warehouses"][0]["id"] == "w1"
    assert warehouse_payload["props"]["error"] == "Permission denied"
    assert warehouse_payload["props"]["select"] in registry
    assert job_payload["props"]["status"] == "QUEUED"
    assert job_payload["props"]["runId"] == "99"
    assert job_payload["props"]["disabled"] is True
    assert job_payload["props"]["trigger"] in registry


def test_frontend_maps_every_python_component():
    repo_root = Path(__file__).resolve().parents[1]
    python_source = (repo_root / "brickflowui" / "components.py").read_text(encoding="utf-8")
    renderer_source = (repo_root / "frontend" / "src" / "Renderer.tsx").read_text(
        encoding="utf-8"
    )

    python_types = set(re.findall(r'VNode\(\s*type="([^"]+)"', python_source))
    renderer_types = set(re.findall(r"case '([^']+)'", renderer_source))
    assert python_types - renderer_types == set()
