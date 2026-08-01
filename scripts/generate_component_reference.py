from __future__ import annotations

import inspect
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from brickflowui import components as db_components  # noqa: E402 - path bootstrap above

CATALOG_PATH = ROOT / "docs" / "components" / "catalog.md"
REFERENCE_DIR = ROOT / "docs" / "components" / "reference"


COMPONENT_NAMES = [
    "Accordion",
    "AccordionItem",
    "Alert",
    "AreaChart",
    "Badge",
    "BarChart",
    "Breadcrumbs",
    "Button",
    "Card",
    "CatalogBrowser",
    "ChatInput",
    "ChatMessage",
    "Checkbox",
    "Code",
    "Column",
    "ComposedChart",
    "DateRangePicker",
    "Divider",
    "DonutChart",
    "Drawer",
    "Embed",
    "EmptyState",
    "Form",
    "FunnelChart",
    "GaugeChart",
    "Grid",
    "Heatmap",
    "Hero",
    "Image",
    "Input",
    "JobTrigger",
    "KanbanBoard",
    "LineChart",
    "Modal",
    "MultiSelect",
    "NavItem",
    "PipelineGraph",
    "Plot",
    "Popup",
    "Progress",
    "RadarChart",
    "Row",
    "ScatterChart",
    "SectionHeader",
    "Select",
    "Sidebar",
    "Slider",
    "Spacer",
    "SparklineStat",
    "Spinner",
    "Stat",
    "StatusStrip",
    "Stepper",
    "TabItem",
    "Table",
    "Tabs",
    "Text",
    "ThemeToggle",
    "Timeline",
    "Toast",
    "Toggle",
    "TopNav",
    "TreeMap",
    "Video",
    "WarehouseSelector",
]


SPECIAL_NOTES = {
    "Input": [
        "Text-like inputs default to `change_strategy=\"debounce\"`, which keeps typing local and fast while syncing state back to Python after `debounce_ms`.",
        "Use `change_strategy=\"immediate\"` only when every character must trigger backend logic.",
        "Use `change_strategy=\"blur\"` when the input kicks off a heavier query and should only sync once the field loses focus.",
    ],
    "ChatInput": [
        "Chat input uses the same debounced local-first sync model as `Input`, so composing prompts stays smooth.",
        "Call `on_submit` for the actual send action and reserve `on_change` for draft-aware UX, prompt suggestions, or validation.",
    ],
    "MultiSelect": [
        "MultiSelect emits `list[str]` back to Python, which makes it a strong fit for scoped filters and dashboard drilldowns.",
        "Use it together with `Table`, `Heatmap`, `PipelineGraph`, or query builders to control slices of a larger workspace.",
    ],
    "DateRangePicker": [
        "DateRangePicker emits a dictionary shaped like `{\"start\": \"YYYY-MM-DD\", \"end\": \"YYYY-MM-DD\"}`.",
        "Use it for filters, compare-period controls, and data-refresh windows.",
    ],
    "Sidebar": [
        "Sidebar collapses behind a mobile menu automatically and can expose the shared `ThemeToggle` in the shell footer.",
    ],
    "TopNav": [
        "TopNav collapses its route list into a menu button on smaller screens and can host secondary action buttons on the right.",
    ],
    "Image": [
        "Use `variant=\"inline\"` for logos and product marks, `variant=\"avatar\"` for circular profile images, and `variant=\"content\"` for screenshots or larger visuals.",
    ],
    "Hero": [
        "Hero is intentionally designed for product-level first impressions, so it works well at the top of dashboards, landing pages, and admin portals.",
    ],
    "Table": [
        "Table supports loading, export, sorting, pagination, row clicks, and richer cell formats such as `badge`, `status`, `currency`, `progress`, and `image`.",
    ],
    "Progress": [
        "The fill width is calculated as `value / max`, capped at 100 percent.",
        "Friendly colors map to theme tokens: `blue` uses primary, `green` uses success, `orange` or `yellow` uses warning, and `red` uses error.",
        "You can also pass an explicit CSS color such as `#2563eb` or `var(--custom-progress)`.",
    ],
    "Plot": [
        "Plot accepts a Plotly figure or a figure dictionary and is the escape hatch for advanced charting that goes beyond the built-in chart set.",
    ],
}

RESPONSIVE_NOTES = {
    "Sidebar": "Sidebar auto-collapses behind a mobile menu on smaller screens, so keep labels concise and rely on icons plus text rather than icons alone.",
    "TopNav": "TopNav collapses route links into a mobile panel. Keep high-priority actions in the `actions` slot so they remain reachable on dense screens.",
    "Table": "Tables can overflow horizontally on small screens. Keep the most important columns first and use cell formats like `status`, `badge`, and `progress` to reduce wordiness.",
    "Hero": "Hero supports large landing-page presentations but should still keep its subtitle and actions concise enough for tablet and mobile layouts.",
    "Grid": "Prefer fewer columns on dense portal screens. The framework will wrap, but your card content should still read cleanly in a single-column stack.",
    "PipelineGraph": "PipelineGraph is horizontally scrollable on smaller screens. Keep node labels short and use status layers or tooltips for deeper detail.",
}

ACCESSIBILITY_NOTES = {
    "Button": "Use action-oriented labels and avoid relying only on iconography for meaning.",
    "Input": "Always provide `label` for production forms unless the field is purely decorative or already described by adjacent UI copy.",
    "Select": "Pair `label` with concise option labels so screen-reader and keyboard navigation stay predictable.",
    "Checkbox": "Checkbox works best for explicit yes/no or on/off decisions where the label clearly communicates the resulting state.",
    "Toggle": "Prefer Toggle for app-like settings and live feature switches, but keep the label explicit because the visual control alone is ambiguous.",
    "Image": "Always set meaningful `alt` text for informative images. Use empty `alt` only for decorative brand marks that repeat nearby text.",
    "Video": "Use caption or surrounding copy to explain what the user is seeing, especially when the video demonstrates workflow or onboarding steps.",
    "Embed": "Use a descriptive `title` so embedded dashboards and external artifacts remain understandable to assistive technologies.",
}


def slugify(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


def annotation_text(annotation: Any) -> str:
    if annotation is inspect._empty:
        return "Any"
    text = str(annotation).replace("typing.", "")
    text = text.replace("<class 'str'>", "str").replace("<class 'int'>", "int")
    text = text.replace("<class 'float'>", "float").replace("<class 'bool'>", "bool")
    text = text.replace("<class 'dict'>", "dict").replace("<class 'list'>", "list")
    text = text.replace("NoneType", "None")
    return text


def default_text(value: Any) -> str:
    if value is inspect._empty:
        return "required"
    return repr(value)


def read_catalog_descriptions() -> dict[str, str]:
    descriptions: dict[str, str] = {}
    pattern = re.compile(r"- \[(?P<name>[^\]]+)\]\([^)]+\): (?P<description>.+)")
    for line in CATALOG_PATH.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line.strip())
        if match:
            descriptions[match.group("name")] = match.group("description").strip()
    return descriptions


def example_literal(param_name: str) -> str:
    mapping = {
        "label": '"Pipeline health"',
        "title": '"Command center"',
        "subtitle": '"Monitor warehouse freshness and failed jobs."',
        "message": '"Everything is healthy."',
        "value": '"active"',
        "name": '"status"',
        "path": '"/analytics"',
        "icon": '"LayoutDashboard"',
        "placeholder": '"Search pipelines..."',
        "alt": '"Preview"',
        "src": '"assets/preview.png"',
        "image": '"assets/logo.svg"',
        "image_alt": '"Brand mark"',
        "poster": '"assets/poster.png"',
        "height": '"320px"',
        "width": '"100%"',
        "caption": '"Example asset rendered directly from Python."',
        "brand_name": '"Acme Analytics"',
        "tagline": '"Built with BrickflowUI"',
        "submit_label": '"Send"',
        "eyebrow": '"Data platform"',
        "currency": '"USD"',
    }
    return mapping.get(param_name, f'"{param_name}"')


def sample_arg(component_name: str, param_name: str) -> str:
    if param_name.startswith("on_"):
        return f"{param_name}=lambda value=None: None"
    if param_name == "children":
        return 'children=[db.Text("Example content")]'
    if param_name == "items":
        if component_name in {"Tabs"}:
            return 'items=[db.TabItem("Overview", [db.Text("Overview panel")])]'
        if component_name in {"Sidebar", "TopNav"}:
            return 'items=[db.NavItem("Overview", "/")]'
        return 'items=[{"label": "Overview", "path": "/"}]'
    if param_name == "actions":
        return 'actions=[db.Button("Refresh")]'
    if param_name == "badges":
        return 'badges=[db.Badge("Live", color="green")]'
    if param_name == "visual":
        return 'visual=db.Card([db.Text("Right-side visual")])'
    if param_name == "columns":
        if component_name == "Table":
            return 'columns=[{"key": "name", "label": "Name"}]'
        if component_name == "KanbanBoard":
            return 'columns=[{"id": "todo", "label": "Todo", "cards": [{"id": "a", "title": "Investigate SLA drift"}]}]'
    if param_name == "data":
        data_map = {
            "Table": '[{"name": "Pipeline A", "status": "Healthy"}]',
            "AreaChart": '[{"week": "W01", "runs": 24, "failures": 2}]',
            "BarChart": '[{"week": "W01", "runs": 24}]',
            "LineChart": '[{"week": "W01", "latency": 4.2}]',
            "DonutChart": '[{"label": "Healthy", "value": 42}]',
            "ScatterChart": '[{"freshness": 12, "cost": 240}]',
            "ComposedChart": '[{"week": "W01", "runs": 24, "sla": 98}]',
            "RadarChart": '[{"metric": "Freshness", "score": 92}]',
            "Heatmap": '[{"hour": "09", "layer": "Bronze", "value": 2}]',
            "FunnelChart": '[{"label": "Bronze", "value": 120}]',
            "TreeMap": '[{"name": "Storage", "value": 42}]',
            "Timeline": '[{"title": "Job started", "time": "09:00"}]',
            "SparklineStat": '[{"day": "Mon", "value": 14}, {"day": "Tue", "value": 12}]',
            "Plot": '{"data": [{"type": "bar", "x": ["Mon"], "y": [24]}]}',
        }
        default_data = '[{"label": "Item", "value": 1}]'
        return "data=" + data_map.get(component_name, default_data)
    if param_name == "options":
        return 'options=[{"label": "Bronze", "value": "bronze"}, {"label": "Silver", "value": "silver"}]'
    if param_name == "values":
        return 'values=["bronze"]'
    if param_name == "nodes":
        return 'nodes=[{"id": "extract", "label": "Extract", "status": "running"}]'
    if param_name == "edges":
        return 'edges=[]'
    if param_name == "steps":
        return 'steps=[{"label": "Bronze"}, {"label": "Silver"}]'
    if param_name == "figure":
        return 'figure={"data": [{"type": "bar", "x": ["Mon"], "y": [24]}]}'
    if param_name == "role":
        return 'role="assistant"'
    if param_name == "content":
        return 'content="Two jobs are outside SLA."'
    if param_name == "type":
        if component_name == "Input":
            return 'type="search"'
        return 'type="info"'
    if param_name == "min":
        return "min=0"
    if param_name == "max":
        return "max=100"
    if param_name == "step":
        return "step=1"
    if param_name == "start":
        return 'start="2026-05-01"'
    if param_name == "end":
        return 'end="2026-05-07"'
    if param_name in {"x_key", "angle_key"}:
        return f'{param_name}="week"' if component_name != "RadarChart" else 'angle_key="metric"'
    if param_name == "y_key":
        return 'y_key="cost"'
    if param_name == "y_keys":
        return 'y_keys=["runs"]'
    if param_name == "bar_keys":
        return 'bar_keys=["runs"]'
    if param_name == "line_keys":
        return 'line_keys=["sla"]'
    if param_name == "value_key":
        return 'value_key="value"'
    if param_name == "label_key":
        return 'label_key="label"'
    if param_name == "name_key":
        return 'name_key="name"'
    if param_name == "active":
        return "active=1"
    if param_name == "visible":
        return "visible=True"
    if param_name == "checked":
        return "checked=True"
    if param_name == "loading":
        return "loading=False"
    if param_name == "values":
        return 'values=["bronze"]'
    if param_name == "default_open":
        return "default_open=[0]"
    if param_name == "allow_multiple":
        return "allow_multiple=True"
    if param_name == "pagination":
        return "pagination=10"
    if param_name == "src":
        return 'src="https://example.com"'
    if param_name == "title":
        return f'title={example_literal("title")}'
    if param_name == "value":
        if component_name in {"Slider", "GaugeChart"}:
            return "value=72"
        return f"value={example_literal('value')}"
    return f"{param_name}={example_literal(param_name)}"


def build_example(component_name: str, signature: inspect.Signature) -> str:
    specialized = {
        "Column": 'db.Column([db.Text("Pipeline health", variant="h3"), db.Text("Everything is healthy.", muted=True)], gap=2)',
        "Row": 'db.Row([db.Badge("Healthy", color="green"), db.Button("Refresh", variant="secondary")], gap=2, wrap=True)',
        "Card": 'db.Card([db.Text("Warehouse health", variant="h3"), db.Text("Last refresh: 4 minutes ago", muted=True)], bordered=True, elevated=True)',
        "Grid": 'db.Grid([db.Card([db.Text("Runs")]), db.Card([db.Text("Failures")])], cols=2, gap=4)',
        "Text": 'db.Text("Warehouse latency is stable.", variant="body", muted=False)',
        "Code": 'db.Code("SELECT * FROM prod.pipeline_runs LIMIT 10")',
        "Button": 'db.Button("Run refresh", on_click=lambda: None, icon="Sparkles")',
        "Input": 'db.Input(name="search", label="Search", placeholder="Search pipelines...", value="", on_change=lambda value: None, debounce_ms=220)',
        "Select": 'db.Select(name="site", label="Site", options=[{"label": "Toyama", "value": "toyama"}], value="toyama", on_change=lambda value: None)',
        "Checkbox": 'db.Checkbox(name="watch_only", label="Only show watchlist", checked=False, on_change=lambda value: None)',
        "Toggle": 'db.Toggle(name="dark_mode", label="Dark mode", checked=True, on_change=lambda value: None)',
        "Slider": 'db.Slider(name="confidence", label="Confidence", min=0, max=100, step=1, value=72, on_change=lambda value: None)',
        "Progress": 'db.Progress(value=85, label="Pipeline health")',
        "DateRangePicker": 'db.DateRangePicker(name="window", label="Window", start="2026-05-01", end="2026-05-07", on_change=lambda value: None)',
        "MultiSelect": 'db.MultiSelect(name="layers", label="Layers", options=[{"label": "Bronze", "value": "bronze"}, {"label": "Silver", "value": "silver"}], values=["bronze"], on_change=lambda values: None)',
        "Sidebar": 'db.Sidebar([db.NavItem("Dashboard", "/"), db.NavItem("Pipelines", "/pipelines", icon="GitBranch")], brand_name="Acme Analytics", tagline="Built with BrickflowUI")',
        "TopNav": 'db.TopNav([db.NavItem("Dashboard", "/"), db.NavItem("Analytics", "/analytics")], brand_name="Acme Analytics", actions=[db.Button("Export", variant="secondary")], show_theme_toggle=True)',
        "ThemeToggle": 'db.ThemeToggle(label="Theme", light_label="Light", dark_label="Dark")',
        "Hero": 'db.Hero("Pipeline command center", subtitle="Observe jobs, freshness, and cost from one place.", tagline="Built with BrickflowUI", image="assets/logo.svg", actions=[db.Button("Refresh")], badges=[db.Badge("Live", color="green")])',
        "Image": 'db.Image("assets/logo.svg", alt="Acme logo", variant="inline")',
        "Video": 'db.Video("assets/demo.mp4", poster="assets/poster.png", caption="Product walkthrough")',
        "Table": 'db.Table(data=[{"name": "Bronze Orders", "status": "Healthy"}], columns=[{"key": "name", "label": "Name"}, {"key": "status", "label": "Status", "format": "status"}], pagination=10, exportable=True)',
        "Plot": 'db.Plot({"data": [{"type": "bar", "x": ["Mon", "Tue"], "y": [24, 18]}]})',
        "PipelineGraph": 'db.PipelineGraph(nodes=[{"id": "extract", "label": "Extract", "status": "running"}], edges=[], title="Revenue pipeline")',
        "ChatInput": 'db.ChatInput(value="", placeholder="Ask about delayed jobs", on_change=lambda value: None, on_submit=lambda value: None, debounce_ms=200)',
        "ChatMessage": 'db.ChatMessage(role="assistant", content="Two jobs are outside SLA.", name="Ops Copilot")',
    }
    if component_name in specialized:
        return specialized[component_name]

    args = []
    for param_name, param in signature.parameters.items():
        if param_name == "kwargs":
            continue
        if param.kind in {inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD}:
            continue
        if param.default is inspect._empty or param_name in {"label", "title", "message", "value"}:
            args.append(sample_arg(component_name, param_name))
        elif len(args) < 4 and param_name in {"placeholder", "icon", "animated", "variant", "height"}:
            args.append(sample_arg(component_name, param_name))

    return f"db.{component_name}({', '.join(args)})"


def render_page(component_name: str, description: str, signature: inspect.Signature) -> str:
    signature_text = f"db.{component_name}{signature}"
    rows = []
    for param_name, param in signature.parameters.items():
        if param_name == "kwargs":
            continue
        rows.append(
            f"| `{param_name}` | `{annotation_text(param.annotation)}` | `{default_text(param.default)}` | |"
        )
    table = "\n".join(rows) if rows else "| _No direct parameters_ | `-` | `-` | |"
    notes = SPECIAL_NOTES.get(
        component_name,
        [
            "This component composes cleanly with layout primitives such as `Card`, `Grid`, `Row`, and `Column`.",
            "Prefer controlled state from Python when the value matters to your business logic or backend query layer.",
        ],
    )
    note_block = "\n".join(f"- {note}" for note in notes)
    responsive_note = RESPONSIVE_NOTES.get(
        component_name,
        "Check the component inside a realistic layout, not only in isolation, so spacing, overflow, and action density stay comfortable on smaller screens.",
    )
    accessibility_note = ACCESSIBILITY_NOTES.get(
        component_name,
        "Pair this component with clear visible copy and predictable state changes so keyboard and assistive-technology users are not surprised.",
    )
    example = build_example(component_name, signature)
    return f"""# {component_name}

## What It Does

{description}

## Signature

```python
{signature_text}
```

## Parameters

| Name | Type | Default | Notes |
| --- | --- | --- | --- |
{table}

## Example

```python
import brickflowui as db

node = {example}
```

## Integration Notes

{note_block}

## Responsive Notes

{responsive_note}

## Accessibility Notes

{accessibility_note}
"""


def main() -> None:
    descriptions = read_catalog_descriptions()
    for component_name in COMPONENT_NAMES:
        component = getattr(db_components, component_name, None)
        if component is None:
            continue
        signature = inspect.signature(component)
        description = descriptions.get(
            component_name,
            f"{component_name} is part of the BrickflowUI public component surface.",
        )
        page = render_page(component_name, description, signature)
        path = REFERENCE_DIR / f"{slugify(component_name)}.md"
        path.write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main()
