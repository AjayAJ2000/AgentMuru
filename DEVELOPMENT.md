# AgentMuru development

Use Python 3.10 through 3.13 and Node.js 24. Go 1.25.9 is required only for the experimental
Labs runtime under `edge/`.

```powershell
python -m pip install -e ".[dev,docs,providers]"
cd frontend
npm ci
cd ..
python -m pytest -q
```

The deterministic test suite never calls a paid model API. Provider adapter tests use recorded
SDK-shaped fakes, server tests use the ASGI adapter, and frontend tests replay protocol version 1
events.

Run a development workspace:

```powershell
muru dev examples.hello_agent:application
```

Build bundled workspace assets before packaging:

```powershell
cd frontend
npm run build
cd ..
python -m build
```

See `AGENTS.md` for architectural boundaries and the full verification contract.

## Full verification

```powershell
python -m ruff check agentmuru tests qualification examples
python -m mypy agentmuru
cd frontend
npm test -- --run
npm run lint
npm run typecheck
npm run build
npm run test:bundle
npm run check:bundle
cd ..
python -m mkdocs build --strict
python -m build
```
