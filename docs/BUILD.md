# Build Guide

## Fastest local setup

From the repo root:

```bash
pip install -e ".[dev]"
```

If you plan to work on the React frontend too:

```bash
cd frontend
npm install
npm run build
cd ..
```

## Run the test suite

```bash
python -m pytest -q
```

## Run a demo app

Auth portal:

```bash
cd examples/auth_portal
python app.py
```

Source: [`examples/auth_portal/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/auth_portal/app.py)

Operations + finance portal:

```bash
cd examples/operations_finance_portal
python app.py
```

Source: [`examples/operations_finance_portal/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/operations_finance_portal/app.py)

By default the server uses `http://127.0.0.1:8050`. To use another port:

```bash
# PowerShell
$env:DATABRICKS_APP_PORT=8061
python app.py
```

## Build a publishable package

Install the release tools once:

```bash
pip install build twine
```

Then from the repo root:

```bash
python -m build
python -m twine check dist/*
```

If the checks pass, upload to PyPI:

```bash
python -m twine upload dist/*
```

## Build the documentation site locally

Install docs tooling:

```bash
pip install -e ".[docs]"
```

Run the docs server:

```bash
python -m mkdocs serve
```

Open:

```text
http://127.0.0.1:8000
```

Build the static docs site:

```bash
python -m mkdocs build
```

If `mkdocs serve` is not recognized, use the `python -m mkdocs ...` form above. That runs MkDocs from the same Python environment where the docs extra was installed and avoids PATH issues on Windows.

If Windows reports access denied while cleaning `site/`, close any process serving the docs and run:

```bash
python -m mkdocs build
```

## What needs rebuilding?

- Python-only changes: reinstall with `pip install -e ".[dev]"` if needed, then run tests.
- Frontend source changes under [`frontend/src`](https://github.com/AjayAJ2000/brickflowUI/tree/main/frontend/src): run `npm run build` so [`brickflowui/frontend/dist`](https://github.com/AjayAJ2000/brickflowUI/tree/main/brickflowui/frontend/dist) is updated before publishing.
- Docs, examples, and tests: no special build step required.
