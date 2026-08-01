# Examples

BrickflowUI ships six maintained examples. From a clean clone, run `python -m pip install -e ".[all]"`, then run every local command below from the repository root. Each example includes the deployment trio Databricks Apps expects: `app.py`, `app.yaml`, and `requirements.txt`.

The suggested learning path is: `counter` → `component_studio` → a workflow example → the governed and assistant examples.

## Counter

**Purpose.** The smallest installation and runtime sanity check.

**Capabilities proven.** A page route, local state, button events, badges, and rerendering.

**Local command.** `python examples/counter/app.py`

**Deployment files.** [`app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/counter/app.py), [`app.yaml`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/counter/app.yaml), and [`requirements.txt`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/counter/requirements.txt).

**Expected auth mode.** Application mode with an anonymous public page for local use.

**Learning path.** Start here to verify the install before exploring layout or data workflows.

## Component Studio

**Purpose.** The maintained interactive catalog for BrickflowUI components and visual states.

**Capabilities proven.** Layouts, controlled inputs, tables, charts, pipeline views, media, loading, motion, modals, drawers, popups, toasts, and assistant-style UI.

**Local command.** `python examples/component_studio/app.py`

**Deployment files.** [`app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/component_studio/app.py), [`app.yaml`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/component_studio/app.yaml), [`requirements.txt`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/component_studio/requirements.txt), and the local [`assets`](https://github.com/AjayAJ2000/brickflowUI/tree/main/examples/component_studio/assets) directory.

**Expected auth mode.** Application mode with an anonymous public page.

**Learning path.** Continue here after `counter`; use it as the default reference while building and styling an app.

## Data Pipeline Command Center

**Purpose.** The flagship production-data operations workflow.

**Capabilities proven.** Mock and Databricks SQL sources, filters, operational KPIs, dependency graphs, reliability charts, triage, simulated job actions, safe fallback behavior, and an assistant view.

**Local command.** `python -m examples.data_pipeline_command_center.app`

**Deployment files.** [`app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/data_pipeline_command_center/app.py), [`app.yaml`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/data_pipeline_command_center/app.yaml), and [`requirements.txt`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/data_pipeline_command_center/requirements.txt).

**Expected auth mode.** Application mode with an anonymous public page; mock data works locally, while the SQL option expects Databricks configuration.

**Learning path.** Use this after Component Studio to learn how components combine into a realistic data application.

## Clinical Trial Command Center

**Purpose.** A governed, regulated-industry operations portal.

**Capabilities proven.** Multi-page navigation, header authentication, clinician and operations roles, Unity Catalog patterns, Plotly, pipeline topology, and study dashboards.

**Local command.** `python examples/clinical_trial_command_center/app.py`

**Deployment files.** [`app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/clinical_trial_command_center/app.py), [`app.yaml`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/clinical_trial_command_center/app.yaml), [`requirements.txt`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/clinical_trial_command_center/requirements.txt), and the local [`assets`](https://github.com/AjayAJ2000/brickflowUI/tree/main/examples/clinical_trial_command_center/assets) directory.

**Expected auth mode.** User mode with anonymous access disabled. Local requests need `x-brickflow-user-id` and role headers; the manifest provides smoke-test values.

**Learning path.** Study this after the flagship example when adding identity, roles, and governed data access.

## Auth Portal

**Purpose.** A focused authentication, session, API, and access-control reference.

**Capabilities proven.** Hybrid identity, demo cookie sessions, login and logout routes, protected user and application pages, role checks, access denial, and a themed portal.

**Local command.** `python examples/auth_portal/app.py`

**Deployment files.** [`app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/auth_portal/app.py), [`app.yaml`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/auth_portal/app.yaml), [`requirements.txt`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/auth_portal/requirements.txt), and [`theme.yaml`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/auth_portal/theme.yaml).

**Expected auth mode.** Hybrid mode with anonymous access to the home page and local demo-cookie sign-in for protected routes.

**Learning path.** Use this focused reference before replacing local demo identity with a platform authentication provider.

## Chatbot Workspace

**Purpose.** An assistant workspace for composing, reviewing, and tracing responses.

**Capabilities proven.** Chat messages, composition-safe input, pending and completion states, prompt controls, drawers, timelines, metadata, and toast feedback.

**Local command.** `python examples/chatbot_workspace/app.py`

**Deployment files.** [`app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/chatbot_workspace/app.py), [`app.yaml`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/chatbot_workspace/app.yaml), and [`requirements.txt`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/chatbot_workspace/requirements.txt).

**Expected auth mode.** Application mode with an anonymous public page.

**Learning path.** Finish here when the product needs conversational UI, asynchronous feedback, or agent traces.
