# FAQ

## What is the correct package name?

Use:

- PyPI package: `brickflowui`
- import: `import brickflowui as db`
- CLI: `brickflowui`

## How do I install directly from GitHub?

```bash
pip install "brickflowui @ git+https://github.com/AjayAJ2000/brickflowUI.git@v0.1.13"
```

## How do I put the GitHub version in `requirements.txt`?

```text
brickflowui @ git+https://github.com/AjayAJ2000/brickflowUI.git@v0.1.13
```

## How do I use it in Databricks Apps?

Use:

```yaml
command:
  - python
  - app.py
```

and:

```text
brickflowui>=0.1.13
```

## Does BrickflowUI depend on Nike's Brickflow?

No.

BrickflowUI is an independent project and is not affiliated with Nike's Brickflow workflow framework.

## Why do text inputs feel smoother now?

BrickflowUI now treats `Input` and `ChatInput` as local-first controls by default.

That means:

- typing updates the browser immediately
- changes sync back to Python with a debounce
- the framework avoids a full round-trip for every single character

If you need a different behavior:

- use `change_strategy="immediate"` for every-keystroke backend updates
- use `change_strategy="blur"` for expensive lookups or search flows
- tune `debounce_ms` when you want a slower or faster sync cadence

## Is light mode or dark mode the default?

Light mode is the default unless you explicitly configure `default_mode="dark"`.

If you provide only a light theme file, older apps and new YAML themes should still render safely.



