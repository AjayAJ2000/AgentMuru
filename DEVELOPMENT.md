# AgentMuru development

Requires Python 3.10 or newer and Node.js 20 or newer.

```powershell
python -m pip install -e ".[dev,docs]"
cd frontend
npm install
cd ..
python -m pytest -q
```

The Python core is tested without FastAPI or a browser. Server tests use the ASGI
adapter. Frontend reducer tests replay real protocol event shapes. `FakeModel` is the
only model used by the local and CI suites.

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
