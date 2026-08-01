# 02. Install And Run

## Learning Goal

Install BrickflowUI, run a local app, and understand which files are needed for a Databricks App.

## Install

Use:

```bash
pip install brickflowui
```

For local development from this repository:

```bash
pip install -e ".[dev]"
```

For docs work:

```bash
pip install -e ".[docs]"
```

If `mkdocs` is not recognized on Windows, prefer:

```bash
python -m mkdocs serve
```

## Minimal App File

Create `app.py`:

```python
import brickflowui as db

app = db.App(title="Learning App")

@app.page("/", title="Home")
def home():
    return db.Text("BrickflowUI is running", variant="h1")

if __name__ == "__main__":
    app.run()
```

Run:

```bash
python app.py
```

Open:

```text
http://127.0.0.1:8050
```

## Databricks App Files

A Databricks App normally needs:

```text
app.py
app.yaml
requirements.txt
```

Example `requirements.txt`:

```text
brickflowui>=0.1.13
```

Example `app.yaml`:

```yaml
command:
  - python
  - app.py

env:
  - name: BRICKFLOWUI_ENV
    value: production
```

## Local Repo Development

The Python package serves pre-built frontend files from:

- [`brickflowui/frontend/dist/`](https://github.com/AjayAJ2000/brickflowUI/tree/main/brickflowui/frontend/dist)

If you change files under [`frontend/src`](https://github.com/AjayAJ2000/brickflowUI/tree/main/frontend/src), rebuild:

```bash
cd frontend
npm run build
```

Then commit the updated [`brickflowui/frontend/dist`](https://github.com/AjayAJ2000/brickflowUI/tree/main/brickflowui/frontend/dist) assets.

## Common Mistakes

- Installing `brickflowui` in one Python environment and running the app from another.
- Editing frontend source but forgetting to rebuild bundled assets.
- Deleting [`brickflowui/frontend/dist`](https://github.com/AjayAJ2000/brickflowUI/tree/main/brickflowui/frontend/dist) before packaging.
- Pushing [`frontend/node_modules`](https://github.com/AjayAJ2000/brickflowUI/tree/main/frontend/node_modules) to git.
- Expecting root `dist/` or `site/` to be source files. They are generated.

## Exercise

Create a fresh folder with `app.py`, `requirements.txt`, and `app.yaml`.

Run it locally. Then change the title and confirm the browser updates after restart.

## Checkpoint

You should be able to install BrickflowUI, run a local app, and explain why [`brickflowui/frontend/dist`](https://github.com/AjayAJ2000/brickflowUI/tree/main/brickflowui/frontend/dist) is part of the package.



