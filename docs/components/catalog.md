# Component Pages

Use this catalog when you want a page dedicated to one BrickflowUI component.

## Layout

- [Column](reference/column.md): Stacks child components vertically with consistent spacing.
- [Row](reference/row.md): Lays out child components horizontally with optional wrapping and alignment controls.
- [Card](reference/card.md): Creates a surface container for sections, KPIs, or grouped controls.
- [Grid](reference/grid.md): Builds a responsive multi-column layout for cards, charts, or forms.
- [Divider](reference/divider.md): Separates related content blocks visually.
- [Spacer](reference/spacer.md): Adds explicit breathing room between nearby components.

## Typography

- [Text](reference/text.md): Renders headings, body copy, captions, labels, and lightweight code text.
- [Code](reference/code.md): Shows a syntax-friendly code block for docs, debug output, or examples.

## Controls

- [Button](reference/button.md): Triggers actions, navigation, or secondary workflows.
- [Input](reference/input.md): Captures controlled text, search, numeric, date, URL, or textarea input.
- [Select](reference/select.md): Lets the user choose one option from a list.
- [Checkbox](reference/checkbox.md): Toggles a boolean value with an explicit label.
- [Toggle](reference/toggle.md): Switches a boolean state with a more app-like visual treatment.
- [Slider](reference/slider.md): Adjusts numeric values across a bounded range.
- [DateRangePicker](reference/date-range-picker.md): Captures a start and end date in one controlled component.
- [MultiSelect](reference/multi-select.md): Lets users activate multiple tags, scopes, or filters.
- [ChatInput](reference/chat-input.md): Collects assistant-style prompts with change and submit events.

## Feedback

- [Badge](reference/badge.md): Highlights compact status labels such as environment, freshness, or risk.
- [Alert](reference/alert.md): Shows inline information, warnings, successes, or errors.
- [Spinner](reference/spinner.md): Communicates local loading work for buttons, cards, and forms.
- [Progress](reference/progress.md): Displays completion, readiness, or processing percentages.
- [Stat](reference/stat.md): Shows KPI values with optional deltas and motion-friendly counters.
- [Toast](reference/toast.md): Shows dismissible, state-safe notifications in the corner of the app.
- [EmptyState](reference/empty-state.md): Explains why a view has no content and what to do next.
- [Timeline](reference/timeline.md): Narrates chronological events such as incidents, approvals, or jobs.
- [Image](reference/image.md): Renders local or remote images, logos, screenshots, and GIFs from Python.
- [Video](reference/video.md): Renders local or remote videos directly from your BrickflowUI script.
- [Embed](reference/embed.md): Hosts external artifacts, dashboards, and review content inside the page.
- [SparklineStat](reference/sparkline-stat.md): Combines a compact KPI value with a tiny embedded trend line.

## Navigation

- [Tabs](reference/tabs.md): Switches between multiple content sections without leaving the page.
- [TabItem](reference/tab-item.md): Defines one tab label and its corresponding content tree.
- [Sidebar](reference/sidebar.md): Creates the left navigation shell for multi-page apps.
- [TopNav](reference/top-nav.md): Creates a responsive top navigation bar with automatic mobile collapse.
- [NavItem](reference/nav-item.md): Defines one route entry inside a sidebar navigation list.
- [ThemeToggle](reference/theme-toggle.md): Switches between dark and light modes directly in the UI.
- [Modal](reference/modal.md): Shows a centered blocking overlay for heavier workflows.
- [Drawer](reference/drawer.md): Slides contextual detail in from the side without leaving the page.
- [Popup](reference/popup.md): Shows a lightweight confirmation or quick-look overlay.
- [Accordion](reference/accordion.md): Groups expandable sections for FAQs, help, or dense detail.
- [AccordionItem](reference/accordion-item.md): Defines one expandable section inside an accordion.
- [Breadcrumbs](reference/breadcrumbs.md): Shows where the user is inside a multi-step or nested flow.

## Workflow

- [Hero](reference/hero.md): Creates a premium top-of-page introduction for dashboards, portals, or landing pages.
- [SectionHeader](reference/section-header.md): Adds a reusable title block with subtitle and actions.
- [StatusStrip](reference/status-strip.md): Displays a row or grid of operational health and freshness signals.
- [Stepper](reference/stepper.md): Shows progress through onboarding, review, or release stages.
- [KanbanBoard](reference/kanban-board.md): Visualizes work queues grouped by workflow stage.
- [ChatMessage](reference/chat-message.md): Renders one message inside an assistant or copilot transcript.

## Data

- [Table](reference/table.md): Shows rows of structured data with sorting, pagination, and export.
- [Plot](reference/plot.md): Embeds a native Plotly figure for advanced visualizations.
- [AreaChart](reference/area-chart.md): Displays filled trends over time or categories.
- [BarChart](reference/bar-chart.md): Compares volumes or totals across categories.
- [LineChart](reference/line-chart.md): Highlights trends, latency, or rate movement across an x-axis.
- [DonutChart](reference/donut-chart.md): Shows part-to-whole composition in a compact circular chart.
- [ScatterChart](reference/scatter-chart.md): Plots correlations, clusters, or anomaly candidates.
- [ComposedChart](reference/composed-chart.md): Combines bars, lines, and areas in one chart.
- [GaugeChart](reference/gauge-chart.md): Shows readiness, freshness, reliability, or quality as a dial.
- [RadarChart](reference/radar-chart.md): Compares several dimensions around a shared center.
- [Heatmap](reference/heatmap.md): Maps intensity across two dimensions such as week vs signal.
- [FunnelChart](reference/funnel-chart.md): Shows stage conversion or drop-off across a pipeline.
- [TreeMap](reference/tree-map.md): Displays weighted composition as nested rectangles.
- [PipelineGraph](reference/pipeline-graph.md): Renders a pipeline or DAG-like structure inside the portal.

## Forms

- [Form](reference/form.md): Posts named child controls to a backend route as structured JSON.

## Databricks

These components are server-driven: load or mutate Databricks resources in Python, then pass only normalized records and public status messages to the UI. The helpers automatically follow the current app or user identity.

```python
import brickflowui as db
from brickflowui import databricks as dbrx

warehouses = dbrx.list_warehouses()
db.WarehouseSelector(
    warehouses=warehouses,
    selected_id=selected_warehouse,
    on_select=set_selected_warehouse,
    error=public_error,
)

catalogs = dbrx.catalog_tree()
db.CatalogBrowser(catalogs=catalogs, on_select=set_selected_table)

db.JobTrigger(
    job_id="1234567890",
    status=run_status,
    run_id=run_id,
    on_trigger=lambda payload: dbrx.trigger_job(payload["job_id"]),
)
```

Keep raw SDK exceptions in server logs and pass a short actionable message through each component's `error` prop.

- [CatalogBrowser](reference/catalog-browser.md): Browses Unity Catalog catalogs, schemas, and tables.
- [WarehouseSelector](reference/warehouse-selector.md): Selects a Databricks SQL warehouse from the current environment.
- [JobTrigger](reference/job-trigger.md): Starts a Databricks job run from the UI.
