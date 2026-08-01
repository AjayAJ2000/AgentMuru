# Release Checklist

Use this checklist for every BrickflowUI release. A release is ready only when the exact source commit, generated frontend, package artifacts, browser behavior, and published PyPI version agree.

## 1. Confirm release scope

- verify the branch contains only intended changes with `git status -sb` and `git diff --check`
- update `pyproject.toml`, `brickflowui/version.py`, changelog, migration notes, example requirements, and scaffold requirements to the same version
- remove obsolete examples only when a maintained example covers the same purpose
- regenerate component references and reject undocumented public component drift

## 2. Frontend gates

From `frontend/`:

```bash
npm ci
npm test -- --run
npm run lint
npm run typecheck
npm audit --audit-level=high
npm run build
```

Confirm the build replaces old hashed bundles instead of accumulating them.

## 3. Python and documentation gates

From the repository root:

```bash
python -m pytest -q -p no:cacheprovider
python scripts/generate_component_reference.py
git diff --exit-code -- docs/components/reference
python -m mkdocs build --strict
```

All example apps must compile. Flagship examples must also render in the browser acceptance matrix.

## 4. Browser acceptance matrix

Run a representative multi-page app from the repository root so Python imports the checkout being released:

```bash
python -c "from examples.data_pipeline_command_center.app import app; app.run()"
```

Verify:

- initial load and WebSocket connection
- event-driven state patching
- direct deep links
- `/ → /analytics → /users → Back → Back` without duplicate history entries
- forced WebSocket reconnect and full-tree recovery
- table sorting, pagination, and CSV download
- CSV download lifecycle coverage: link attachment, click, cleanup, and deferred object-URL revocation
- standalone and table progress indicators at representative values such as 25, 85, and 100
- ChatInput submission, final change/submit ordering, and IME composition behavior
- theme switching
- desktop and narrow viewports
- no uncaught browser-console errors

## 5. Package gates

Clean old artifacts, then build and inspect:

```bash
python -m build
python -m twine check dist/*
python -m zipfile -l dist/brickflowui-0.1.17-py3-none-any.whl
```

The wheel must contain exactly one current `index.html`, its referenced hashed JavaScript/CSS assets, and the Python runtime modules.

Install the wheel in a fresh environment and verify import, version, and a minimal ASGI response before publishing.

## 6. Publish and verify

1. Push the release branch and open a PR to `main`.
2. Require CI and review before merge.
3. Create and publish tag/release `v0.1.17` from the merged commit.
4. Let `.github/workflows/publish.yml` publish through PyPI trusted publishing.
5. Verify `https://pypi.org/pypi/brickflowui/0.1.17/json`.
6. Install with `python -m pip install --no-cache-dir brickflowui==0.1.17` in a fresh environment.
7. Confirm `brickflowui.__version__ == "0.1.17"` and bundled frontend assets are present.

## 7. Record evidence

Store the exact commands, exit codes, test counts, dependency-audit results, browser matrix, wheel contents, GitHub workflow URL, and PyPI endpoint in the release verification report. Do not replace a failed or skipped gate with an assumption.
