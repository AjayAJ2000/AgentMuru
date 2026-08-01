# Examples

BrickflowUI ships with a few examples that cover different levels of complexity.

Use this page when you want to skip the docs theory and start from something runnable.

## Flagship example set

These are the examples we actively want evaluators, buyers, and engineering teams to judge BrickflowUI by.

| Example | Path | Best for |
|---|---|---|
| Acme Analytics Command Center | [`examples/acme_analytics_command_center/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/acme_analytics_command_center/app.py) | Premium SaaS-style analytics shell with theme modes and richer table presentation |
| Data Pipeline Command Center | [`examples/data_pipeline_command_center/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/data_pipeline_command_center/app.py) | Data and AI platform monitoring with freshness, SLAs, cost, and Databricks SQL handoff |
| Component Studio | [`examples/component_studio/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/component_studio/app.py) | Interactive documentation-style lab that exercises the broadest component surface |
| Clinical Trial Command Center | [`examples/clinical_trial_command_center/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/clinical_trial_command_center/app.py) | Regulated, auth-aware, Plotly-enabled study operations portal |
| Secure Internal Tools | [`examples/secure_internal_tools/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/secure_internal_tools/app.py) | Governance, protected sections, role-aware views, and internal operations flows |
| Workspace Studio | [`examples/workspace_studio/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/workspace_studio/app.py) | Broad end-to-end portal with top nav, filters, forms, charts, tabs, tables, and a themes page |

## Recommended starting points

| Example | Path | Best for |
|---|---|---|
| Counter | [`examples/counter/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/counter/app.py) | Fastest possible sanity check |
| Local Playground | [`examples/local_playground/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/local_playground/app.py) | Best place to validate typing, loading, media, theme switching, and responsiveness locally |
| Auth Portal | [`examples/auth_portal/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/auth_portal/app.py) | Login, access control, protected routes |
| Operations + Finance Portal | [`examples/operations_finance_portal/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/operations_finance_portal/app.py) | Executive dashboard with a traditional top nav |
| Acme Analytics Command Center | [`examples/acme_analytics_command_center/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/acme_analytics_command_center/app.py) | Dark SaaS-style analytics shell with responsive navigation, rich tables, and theme modes |
| Data Pipeline Command Center | [`examples/data_pipeline_command_center/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/data_pipeline_command_center/app.py) | Industry-style data engineering monitoring with filters, SLA controls, cost, freshness, and Databricks SQL handoff |
| Pipeline Observability 0.1.13 | [`examples/pipeline_observability_015/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/pipeline_observability_015/app.py) | 0.1.13 showcase with pipeline graph, chatbot UI, heatmap, treemap, funnel, radar, gauge, kanban, and table export |
| Geometric Signal Lab | [`examples/geometric_signal_lab/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/geometric_signal_lab/app.py) | Glassmorphism-heavy geometric UI showcase with a rounded shell, hero art, rotating recent-work cards, and branded loading |
| Component Studio | [`examples/component_studio/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/component_studio/app.py) | Interactive all-components app that doubles as documentation |
| Clinical Trial Command Center | [`examples/clinical_trial_command_center/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/clinical_trial_command_center/app.py) | Auth-gated study operations portal with Unity Catalog query patterns and Plotly |
| Secure Internal Tools | [`examples/secure_internal_tools/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/secure_internal_tools/app.py) | Role-aware internal tools portal focused on governance and restricted views |
| Chatbot Workspace | [`examples/chatbot_workspace/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/chatbot_workspace/app.py) | Assistant-style UI with drawers, toast, timelines, and multi-value inputs |
| Landing Site | [`examples/landing_site/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/landing_site/app.py) | Product-style landing page and launch-site composition |
| Workspace Studio | [`examples/workspace_studio/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/workspace_studio/app.py) | Rich app structure with filters, tables, tabs, forms, modal flows, charts, and a dedicated themes page |

## Lightweight and legacy examples

These are still useful for sanity checks, experiments, or backwards-compatibility coverage, but they are not the primary product proof points we recommend leading with.

| Example | Path | Why it still exists |
|---|---|---|
| Counter | [`examples/counter/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/counter/app.py) | Fastest install/runtime sanity check |
| Demo App | [`examples/demo_app/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/demo_app/app.py) | Small generic demo for low-risk experimentation |
| Showcase | [`examples/showcase/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/showcase/app.py) | Older visual reference while the newer flagship apps continue to replace it |
| Weather Dashboard | [`examples/weather_dashboard/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/weather_dashboard/app.py) | Simple chart-and-filter example for lightweight tutorials |

## Data Pipeline Command Center

Use this example when your goal is to connect a real Databricks ingestion or transformation pipeline to an operations dashboard.

- [`examples/data_pipeline_command_center/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/data_pipeline_command_center/app.py)
- [`examples/data_pipeline_command_center/app.yaml`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/data_pipeline_command_center/app.yaml)
- [`examples/data_pipeline_command_center/requirements.txt`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/data_pipeline_command_center/requirements.txt)

It demonstrates:

- multiple live controls on one dashboard
- source switching between mock data and Databricks SQL
- top navigation across executive, health, cost, and data model views
- KPI cards for throughput, freshness, cost, and reliability
- charts for SLA trend, incident mix, and cost concentration
- guardrail controls like minimum success-rate threshold and critical-only filtering
- a practical SQL shape for your pipeline metrics table

This is a good starting point for:

- lakehouse ingestion monitoring
- bronze/silver/gold pipeline visibility
- engineering + analytics stakeholder review dashboards
- free-edition Databricks prototypes that later grow into team dashboards

## Local Playground

Use this example when you want a fast, low-risk place to validate framework behavior during development.

- [`examples/local_playground/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/local_playground/app.py)
- [`examples/local_playground/requirements.txt`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/local_playground/requirements.txt)

It demonstrates:

- debounced local-first `Input` behavior
- `MultiSelect` and `DateRangePicker` filter controls
- `ThemeToggle` and light-first theme behavior
- loading-aware buttons and live state echoing
- charts, tables, and media in one compact page
- a realistic pre-commit regression sandbox for local work

## Acme Analytics Command Center

Use this example when you want to prove BrickflowUI can build the kind of dark, premium analytics portal teams usually expect from a dedicated frontend stack.

- [`examples/acme_analytics_command_center/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/acme_analytics_command_center/app.py)

It demonstrates:

- multi-page branded shell with sidebar navigation
- built-in dark/light mode switching
- responsive page composition that stays usable on mobile
- KPI cards and hero composition
- richer table cells with badge, currency, progress, and status formatting
- a screenshot-style operational dashboard surface you can extend into a real product

## Pipeline Observability 0.1.13

Use this example when you want to test the newest visual toolkit and confirm user inputs drive real state changes.

- [`examples/pipeline_observability_015/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/pipeline_observability_015/app.py)
- [`examples/pipeline_observability_015/app.yaml`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/pipeline_observability_015/app.yaml)
- [`examples/pipeline_observability_015/requirements.txt`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/pipeline_observability_015/requirements.txt)

It demonstrates:

- `PipelineGraph` with node click drilldowns
- `ChatMessage` and `ChatInput` for a copilot-style dashboard assistant
- `StatusStrip`, `Hero`, and `SectionHeader` for polished dashboard composition
- `ComposedChart`, `ScatterChart`, `GaugeChart`, `RadarChart`, `Heatmap`, `FunnelChart`, and `TreeMap`
- `KanbanBoard` for operational triage
- multiple controls driving charts, tables, graph, and chat output
- `Table(exportable=True)` for CSV export

## Geometric Signal Lab

Use this example when your goal is to prove BrickflowUI can build a premium,
geometry-led product surface rather than a traditional analytics dashboard.

- [`examples/geometric_signal_lab/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/geometric_signal_lab/app.py)
- [`examples/geometric_signal_lab/assets/`](https://github.com/AjayAJ2000/brickflowUI/tree/main/examples/geometric_signal_lab/assets)

It demonstrates:

- rounded shell composition with a top pill navigation rail
- large editorial hero typography
- local SVG hero artwork and recent-work visuals
- rotating "recent works" state driven by real interactions
- branded loading assets for light and dark mode
- a practical pattern for premium geometric UI built in pure Python

Read the deeper capability analysis in [Geometric UI And Glassmorphism](./GEOMETRIC_UI.md).

Run it locally:

```bash
cd examples/geometric_signal_lab
python app.py
```

## Component Studio

Use this example when you want one app that teaches the framework while also stress-testing it.

- [`examples/component_studio/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/component_studio/app.py)
- [`examples/component_studio/app.yaml`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/component_studio/app.yaml)
- [`examples/component_studio/requirements.txt`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/component_studio/requirements.txt)

It demonstrates:

- highly interactive tabs that act as documentation chapters
- local and remote media rendering through `Image` and `Video`
- custom loading branding
- charts, plotly, pipeline graph, kanban, timeline, and chat surfaces
- toast, popup, modal, and drawer flows in one example
- component-level animation props in realistic usage

## Clinical Trial Command Center

Use this example when you want a more domain-specific, enterprise-style portal.

- [`examples/clinical_trial_command_center/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/clinical_trial_command_center/app.py)
- [`examples/clinical_trial_command_center/app.yaml`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/clinical_trial_command_center/app.yaml)
- [`examples/clinical_trial_command_center/requirements.txt`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/clinical_trial_command_center/requirements.txt)

It demonstrates:

- auth-gated trial views with role-aware pages
- Unity Catalog and Databricks SQL query patterns with mock fallback
- native Plotly integration via `Plot`
- safety heatmaps, enrollment trend charts, and pipeline flows
- a page split that feels like a real study operations portal

Local testing note:

```text
Set x-brickflow-user-id and x-brickflow-user-roles headers when testing secured pages.
```

## Secure Internal Tools

Use this example when your main priority is governance, access boundaries, and multi-role internal tooling.

- [`examples/secure_internal_tools/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/secure_internal_tools/app.py)
- [`examples/secure_internal_tools/app.yaml`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/secure_internal_tools/app.yaml)
- [`examples/secure_internal_tools/requirements.txt`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/secure_internal_tools/requirements.txt)

It demonstrates:

- per-page role requirements
- governance-aware operational surfaces
- workflow overlays like drawers and popups
- security documentation embedded directly in the UI patterns

## Workspace Studio

The most complete example right now is:

- [`examples/workspace_studio/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/workspace_studio/app.py)
- [`examples/workspace_studio/app.yaml`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/workspace_studio/app.yaml)
- [`examples/workspace_studio/requirements.txt`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/workspace_studio/requirements.txt)

It demonstrates:

- traditional top navigation instead of a sidebar-only layout
- reusable KPI cards
- `use_state` for page-level interactivity
- filters with `Input`, `Select`, `Checkbox`, `Toggle`, and `Slider`
- `AreaChart`, `BarChart`, `LineChart`, and `DonutChart`
- multi-section views switched with state
- `Tabs` for sub-workflows inside a page
- `Table` for operational and release data
- `Form` posting to a custom `@app.route(...)`
- `Modal` for secondary flows without leaving the current page
- a dedicated `Themes` section that shows token mapping and theme-driven UI behavior
- inline theming for Databricks-friendly deployment

## Chatbot Workspace

Use this example when you want to prove BrickflowUI can power assistant-style interfaces as well as dashboards.

- [`examples/chatbot_workspace/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/chatbot_workspace/app.py)
- [`examples/chatbot_workspace/app.yaml`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/chatbot_workspace/app.yaml)
- [`examples/chatbot_workspace/requirements.txt`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/chatbot_workspace/requirements.txt)

It demonstrates:

- conversation layouts built with standard cards and rows
- `DateRangePicker` for structured prompt scope
- `MultiSelect` for answer mode selection
- `Toast` for interaction feedback
- `Drawer` for sources, trace, or tool output
- `Timeline` for execution trace storytelling
- `Accordion` for prompt guidance and tool context

## Landing Site

Use this example when you want a product or launch-style page rather than a traditional dashboard.

- [`examples/landing_site/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/landing_site/app.py)
- [`examples/landing_site/app.yaml`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/landing_site/app.yaml)
- [`examples/landing_site/requirements.txt`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/landing_site/requirements.txt)

It demonstrates:

- hero-card composition
- feature grids with elevated surfaces
- FAQ via `Accordion`
- roadmap storytelling via `Timeline`
- launch feedback via `Toast`
- supporting narrative in a `Drawer`

## Run Workspace Studio locally

```bash
cd examples/workspace_studio
python app.py
```

Open:

```text
http://127.0.0.1:8050
```

## Run Workspace Studio in Databricks Apps

Put these three files in your Databricks App project:

- `app.py`
- `requirements.txt`
- `app.yaml`

`requirements.txt`:

```text
brickflowui>=0.1.13
```

For the 0.1.13 visualization showcase, use:

```text
brickflowui>=0.1.13
```

`app.yaml`:

```yaml
command:
  - python
  - app.py

env:
  - name: BRICKFLOWUI_ENV
    value: production
```

## How to use an example as a template

The most effective pattern is:

1. Copy the example closest to your real use case.
2. Replace the mock data lists with your Databricks SQL or Unity Catalog data.
3. Keep the page structure and component composition.
4. Move repeated UI patterns into helper functions.
5. Add auth and route protection once the page flow is stable.

## Which example should I choose?

- Choose `counter` if you just want to verify installation and runtime.
- Choose `auth_portal` if your main concern is access control and protected pages.
- Choose `operations_finance_portal` if you want a polished dashboard-style shell quickly.
- Choose `acme_analytics_command_center` if you want a premium analytics dashboard aesthetic with richer table presentation.
- Choose `chatbot_workspace` if you want an assistant-style interface with real UI controls around it.
- Choose `landing_site` if you want a cleaner marketing or internal product-launch layout.
- Choose `workspace_studio` if you want the broadest example of how the library fits together.
- Choose `data_pipeline_command_center` if your real goal is pipeline observability and operational dashboarding on Databricks.
- Choose `pipeline_observability_015` if you want the newest chart, pipeline graph, kanban, and chatbot UI primitives.
- Choose `component_studio` if you want an example that behaves like documentation and showcases nearly every UI surface.
- Choose `clinical_trial_command_center` if you want a highly regulated, analytics-heavy portal pattern.
- Choose `secure_internal_tools` if you want security, identity governance, and role-aware page design patterns first.


