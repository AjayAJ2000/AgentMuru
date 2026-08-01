# 18. Production Checklist

## Learning Goal

Prepare a BrickflowUI app for serious use by a team.

## UX Checklist

- Every page has a clear title.
- Every control has a label.
- Tables have useful column labels.
- Charts have titles and units.
- Empty states explain what happened.
- Loading states are visible where data may be delayed.
- Important actions are visually distinct.
- Risk states use consistent colors.
- The app works on laptop-sized screens.

## State Checklist

- Inputs are controlled by state.
- Filters drive all relevant tables and charts.
- Row and chart clicks produce useful drilldowns.
- Multi-value controls use lists.
- Date controls use a consistent shape.
- State is not mutated in place.

## Data Checklist

- Mock data shape matches production data shape.
- SQL result columns match component keys.
- Expensive queries are not repeated unnecessarily.
- Errors are surfaced clearly.
- Sensitive data is not displayed accidentally.

## Deployment Checklist

- `requirements.txt` pins an appropriate version.
- `app.yaml` is present.
- Frontend assets are included in the installed package.
- Environment variables are documented.
- Databricks SQL access is tested.
- Auth expectations are clear.

## Repository Checklist

Commit:

- source files
- docs
- examples
- tests
- [`brickflowui/frontend/dist`](https://github.com/AjayAJ2000/brickflowUI/tree/main/brickflowui/frontend/dist)

Do not commit:

- [`frontend/node_modules`](https://github.com/AjayAJ2000/brickflowUI/tree/main/frontend/node_modules)
- root `dist`
- `site`
- `__pycache__`
- `.pytest_cache`
- `pytest-cache-files-*`
- `_tmp_cli_*`
- throwaway `sample_app_*`

## Release Checklist

Run:

```bash
python -m pytest -q
cd frontend
npm run build
cd ..
python -m mkdocs build
python -m build
python -m twine check dist/brickflowui-0.1.13*
```

## Common Mistakes

- Treating examples as an afterthought.
- Shipping a new component without docs.
- Shipping docs without running MkDocs.
- Shipping frontend changes without checking the wheel.

## Exercise

Take one example app and review it against this checklist. Write down the first five improvements you would make.

## Checkpoint

You should be able to judge whether a BrickflowUI app is ready for team use.



