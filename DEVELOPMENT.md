# BrickflowUI Development Notes

## Local workflow

Install the package in editable mode from the repo root:

```bash
pip install -e ".[dev]"
```

Run the baseline test suite:

```bash
python -m pytest -q
```

Run a single example:

```bash
python examples/counter/app.py
```

Or run a fuller showcase:

```bash
python examples/demo_app/app.py
```

Default app URL:

```text
http://127.0.0.1:8050
```

Use a different port when needed:

```powershell
$env:DATABRICKS_APP_PORT=8061
python examples/demo_app/app.py
```

## Recommended playgrounds

These are the best examples to verify the framework quickly:

```bash
python examples/local_playground/app.py
python examples/component_studio/app.py
python examples/geometric_signal_lab/app.py
```

## Bounded local validation

When packaging or frontend builds are flaky on a local machine, use these
bounded checks instead of waiting on long-running commands:

```bash
python scripts/smoke_examples.py
python -m pytest -q tests/test_examples.py tests/test_app_server.py
python -m mkdocs build --strict -d .site_validation_local
cd frontend
npx tsc --noEmit
```

`scripts/smoke_examples.py` boots each example on an isolated port, waits for a
root HTML response, and then shuts it down. Use this as the main "does the repo
still run?" check before demos and release work.

Exercise the real WebSocket protocol with concurrent, state-changing sessions:

```bash
python scripts/runtime_resilience.py
```

The check starts the counter example on an isolated port, connects 20 sessions,
performs three click-and-render cycles per session, and exits within a bounded
deadline. It fails on protocol errors, incomplete events, or excessive p95
latency. Use `--help` to tune the load, deadline, port, or latency threshold for
slower development machines.

## Frontend build

```bash
cd frontend
npm install
npm run build
```

This writes the packaged frontend bundle to:

```text
brickflowui/frontend/dist/
```

Run the frontend quality gates from `frontend/`:

```bash
npm test -- --run
npm run lint
npm run typecheck
npm run test:bundle
npm run check:bundle
npm run test:e2e
```

The end-user test starts the counter and component studio examples, launches
the pinned Chromium build, exercises real WebSocket interactions, checks a
mobile viewport, and fails on browser errors or serious/critical Axe findings.
Install its browser runtime once with `npx playwright install chromium`.

## Frontend development with hot reload

```bash
# Terminal 1
python examples/demo_app/app.py

# Terminal 2
cd frontend
npm run dev
```

Vite dev server URL:

```text
http://localhost:5173
```

## CLI development

```bash
brickflowui --help
brickflowui new test_app
brickflowui dev
```

## Local cleanup

Use the cleanup script to remove temp validation output, CLI scratch folders,
`__pycache__`, and other local-only artifacts:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\cleanup_local_artifacts.ps1
```

If you also want to remove generated package artifacts and frontend
dependencies, run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\cleanup_local_artifacts.ps1 -IncludeBuildArtifacts
```

Note: if Windows has locked files open, the script will warn and skip those
paths instead of failing the whole cleanup.

## Environment variables

See:

```text
brickflowui/cli/templates/default/.env.example
```

## Component reference maintenance

The component reference pages are generated from the live Python signatures:

```bash
python scripts/generate_component_reference.py
```

## Package structure

```text
brickflowui/                     Python package
|- __init__.py                   Public API
|- app.py                        App class
|- vdom.py                       VNode + diff
|- state.py                      Hooks
|- components.py                 UI primitives
|- server.py                     ASGI server
|- cli/
|  |- main.py                    CLI
|  `- templates/default/         Scaffolding template
|- databricks/
|  |- env.py                     Databricks env helpers
|  |- sql.py                     SQL connector wrappers
|  `- uc.py                      Unity Catalog helpers
`- frontend/dist/                Pre-built React bundle

frontend/                        React source for maintainers
|- src/
|  |- main.tsx                   Entry point
|  |- App.tsx                    WebSocket client + state
|  |- Renderer.tsx               VNode to React renderer
|  |- types.ts                   Wire protocol types
|  `- theme.css                  Design system and runtime styles
|- package.json
`- vite.config.ts

examples/
|- counter/app.py                Minimal example
|- local_playground/app.py       Interactive maintainer playground
|- component_studio/app.py       Broad component coverage
`- geometric_signal_lab/app.py   Premium geometry-led UI showcase
```
