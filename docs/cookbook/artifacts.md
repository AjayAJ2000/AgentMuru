# Create artifacts

**Outcome:** create markdown, JSON, table, code, and file outputs with stable IDs.

Module: `examples.artifact_agent`

```powershell
python examples/artifact_agent.py
```

Expected result: a completed run, five artifacts, and the kinds `code`, `file`, `json`,
`markdown`, and `table`. Muru Workspace lists metadata without inlining large content;
the artifact endpoint retrieves the content by ID.

Text, bytes, and finite JSON are supported. Objects, NaN/Infinity, or invalid metadata fail
before insert with a safe serialization error.

Qualified by `tests/qualification/test_scenarios.py::test_artifact_scenario_creates_reopenable_supported_artifacts`
and the shared in-memory/SQLite artifact contracts.
