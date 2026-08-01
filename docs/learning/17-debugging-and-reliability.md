# 17. Debugging And Reliability

## Learning Goal

Diagnose common issues and make apps reliable.

## App Shows "Connecting To Runtime"

Check:

- Is the Python server running?
- Did the websocket connect?
- Are frontend assets present in the installed package?
- Is the app using the right `requirements.txt` version?
- Are browser console errors related to CSP, missing assets, or websocket failure?

## Frontend Assets Missing

The package must include:

- [`brickflowui/frontend/dist/index.html`](https://github.com/AjayAJ2000/brickflowUI/blob/main/brickflowui/frontend/dist/index.html)
- [`brickflowui/frontend/dist/assets/*.js`](https://github.com/AjayAJ2000/brickflowUI/tree/main/brickflowui/frontend/dist/assets)
- [`brickflowui/frontend/dist/assets/*.css`](https://github.com/AjayAJ2000/brickflowUI/tree/main/brickflowui/frontend/dist/assets)

If you changed frontend code:

```bash
cd frontend
npm run build
```

Then check the wheel:

```bash
python -m zipfile -l dist/brickflowui-0.1.13-py3-none-any.whl
```

## User Input Not Updating

Check:

- Does the component receive `value=...` or `checked=...` from state?
- Does it have `on_change=...`?
- Is the setter updating the correct state variable?
- Are you mutating a list/dict in place?

## Table Or Chart Empty

Check:

- Are filters too strict?
- Are data keys spelled correctly?
- Does the chart use the same key names as the rows?
- Did SQL return records in the expected shape?
- Did you provide an `empty_message`?

## Build Issues

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

On Windows, prefer:

```bash
python -m mkdocs build
```

instead of relying on `mkdocs` being on PATH.

## Common Mistakes

- Publishing without rebuilding frontend assets.
- Forgetting to commit generated package assets.
- Cleaning untracked files with `git clean -fd` and deleting new docs/examples before staging.
- Treating root `dist/` as source.
- Pushing cache folders.

## Exercise

Create a broken chart by using the wrong `y_key`. Then fix it by matching the key to the data.

## Checkpoint

You should be able to debug connection, asset, state, data, and build issues methodically.



