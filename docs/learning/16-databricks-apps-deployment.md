# 16. Databricks Apps Deployment

## Learning Goal

Prepare a BrickflowUI app for Databricks Apps and understand what files and settings matter.

## Required Files

Use this structure:

```text
my_app/
  app.py
  app.yaml
  requirements.txt
```

## `requirements.txt`

```text
brickflowui>=0.1.13
```

If using Databricks SQL or Unity Catalog helpers:

```text
brickflowui[databricks]>=0.1.13
```

## `app.yaml`

```yaml
command:
  - python
  - app.py

env:
  - name: BRICKFLOWUI_ENV
    value: production
```

BrickflowUI reads Databricks runtime environment variables and binds to the port Databricks provides.

## App Entry Point

```python
if __name__ == "__main__":
    app.run()
```

Keep this in `app.py`.

## Databricks SQL Pattern

Start with mock data:

```python
rows = [{"pipeline": "Orders", "status": "Healthy"}]
```

Then replace with SQL:

```python
from brickflowui.databricks import sql

rows = sql.query_to_records("""
SELECT pipeline, status, freshness_min
FROM catalog.schema.pipeline_metrics
""")
```

## Deployment Checklist

- `requirements.txt` references the correct BrickflowUI version.
- `app.yaml` starts `python app.py`.
- The package installed in Databricks includes frontend assets.
- The app does not require local files that were not uploaded.
- Secrets and workspace-specific settings are read from environment variables.
- The app has useful loading and empty states.

## Common Mistakes

- Installing an old PyPI version that does not include the needed frontend assets.
- Forgetting to include `requirements.txt`.
- Using a file path that exists locally but not in Databricks.
- Assuming a cluster-installed library is the same as the app environment.
- Debugging only the Python logs and not checking browser console/network.

## Exercise

Take a local app and create `requirements.txt` and `app.yaml`.

Then explain what each file does.

## Checkpoint

You should understand how to package a BrickflowUI app for Databricks Apps.



