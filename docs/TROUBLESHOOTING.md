# Troubleshooting

This page collects the most common problems users hit while installing, running, publishing, and deploying BrickflowUI.

## I only see "Connecting to runtime..."

This means the HTML shell loaded, but the app did not finish its runtime connection.

Common causes:

- the frontend bundle was not present in the installed package
- the WebSocket route did not connect
- the browser is using a stale cached asset bundle
- the app process crashed before sending the first UI payload

## The page is blank in Databricks Apps

Recommended fixes:

- use `brickflowui>=0.1.13`
- hard refresh the page
- keep `app.yaml` minimal
- avoid relying on third-party frontend assets

## `pip install brickflowui` does not work

Try one of these:

```bash
pip install brickflowui
```

or:

```bash
pip install "brickflowui @ git+https://github.com/AjayAJ2000/brickflowUI.git@v0.1.13"
```

## I changed frontend code, but my package still behaves the same

You need to rebuild the frontend bundle before packaging.

```bash
cd frontend
npm install
npm run build
cd ..
python -m build
```

## Typing in `db.Input` or `db.ChatInput` still feels slow

BrickflowUI now defaults these controls to debounced local-first syncing, so the browser should stay responsive even when Python owns the state.

Check these things:

- make sure you are on `brickflowui>=0.1.13`
- rebuild the frontend bundle after changing runtime input behavior
- avoid `change_strategy="immediate"` unless you truly need every keystroke in Python
- use the local playground example to confirm the framework behavior before debugging your own app logic

Recommended validation:

```bash
python examples/local_playground/app.py
```

## `python -m build` fails around frontend assets

Before publishing, always verify the wheel contains:

- [`brickflowui/frontend/dist/index.html`](https://github.com/AjayAJ2000/brickflowUI/blob/main/brickflowui/frontend/dist/index.html)
- [`brickflowui/frontend/dist/assets/...`](https://github.com/AjayAJ2000/brickflowUI/tree/main/brickflowui/frontend/dist/assets)



