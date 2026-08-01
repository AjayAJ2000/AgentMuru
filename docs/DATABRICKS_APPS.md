# Databricks Apps Guide

This page is the practical guide for running BrickflowUI inside Databricks Apps.

It is written for the actual questions people ask:

- How do I write `app.yaml`?
- What goes in `requirements.txt`?
- Why do I only see "Connecting to runtime..."?
- How do I install from GitHub instead of PyPI?
- How do I make sure the frontend bundle is included?
- How do I get logos, GIFs, and videos to render correctly?

## Minimum working setup

For a basic Databricks App, you usually need:

- `app.py`
- `requirements.txt`
- `app.yaml`

## Correct `app.yaml`

For BrickflowUI, use Python directly.

```yaml
command:
  - python
  - app.py

env:
  - name: BRICKFLOWUI_ENV
    value: production
```

Important:

- do not use `streamlit run app.py`
- do not hardcode `DATABRICKS_TOKEN` directly in `app.yaml`
- keep the first deployment minimal until the runtime is proven healthy

## Correct `requirements.txt`

Install from PyPI:

```text
brickflowui>=0.1.13
```

Install directly from GitHub:

```text
brickflowui @ git+https://github.com/AjayAJ2000/brickflowUI.git@v0.1.13
```

Install a branch from GitHub:

```text
brickflowui @ git+https://github.com/AjayAJ2000/brickflowUI.git@main
```

## If the app only shows "Connecting to runtime..."

This usually means one of these:

1. the frontend bundle is missing from the installed package
2. the WebSocket did not connect
3. the app process did not start correctly
4. the browser is serving an old cached build

### What to check first

Open browser devtools and check:

- the Network tab
- whether `/events?...` gets a `101` WebSocket upgrade
- whether the frontend asset files load successfully

### Verify the installed package contains the frontend

```python
import pathlib
import brickflowui

pkg = pathlib.Path(brickflowui.__file__).parent
print("index exists:", (pkg / "frontend" / "dist" / "index.html").exists())
print("assets dir exists:", (pkg / "frontend" / "dist" / "assets").exists())
```

Expected:

```python
True
True
```

## Media, Branding, And Loading Assets

You can point loading assets, logos, images, and videos at local files from your app script:

```python
app = db.App(
    theme={
        "branding": {
            "logo": "assets/brand/logo.svg",
            "favicon": "assets/brand/mark.svg",
            "tagline": "Built with BrickflowUI",
        }
    },
    loading={
        "title": "Acme Workspace",
        "subtitle": "Runtime-secure analytics workspace",
        "asset": "assets/brand/loader.gif",
    },
)
```

The runtime serves those files automatically, so this now works in Databricks Apps without asking you to wire a separate static route yourself.



