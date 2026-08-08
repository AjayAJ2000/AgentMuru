# Getting started

## Install

```powershell
python -m pip install agentmuru
muru doctor
```

For a source checkout:

```powershell
python -m pip install -e ".[dev,docs]"
```

## Create an application

```powershell
muru init hello-muru --name "Hello Muru"
cd hello-muru
muru run app:application
```

Open `http://127.0.0.1:8000`. The starter uses `FakeModel`, so it runs without credentials.

## Add a tool

```python
from agentmuru import tool

@tool(permission="catalog.read")
def lookup_table(name: str) -> dict[str, str]:
    return {"name": name, "owner": "data-platform"}
```

Grant `catalog.read` on the `Agent`. If a permission is declared but not granted, the
runtime blocks the call. Set `approval="required"` for actions that need a human decision.
