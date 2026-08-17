# Create artifacts

The executable scenario is `examples.artifact_agent`.

```powershell
python examples/artifact_agent.py
```

It completes a run and records Markdown, JSON, table, code, and file artifacts against that run.

## Create one output

```python
from agentmuru import ArtifactKind

artifact = runtime.create_artifact(
    session_id=session.id,
    run_id=run.id,
    kind=ArtifactKind.REPORT,
    name="account-review.md",
    content="# Account review\n\nNo unresolved issues.",
    mime_type="text/markdown",
    creator="support-agent",
    metadata={"customer_id": "cust-1842"},
)
```

The runtime emits `artifact.created`. Session snapshots expose artifact metadata, and the
artifact endpoint returns content when the operator opens it.

## Choose a kind and MIME type

Use the kind for presentation intent and MIME type for content encoding. A table represented as
JSON can use `ArtifactKind.TABLE` with `application/json`. Binary files can use
`ArtifactKind.FILE` and a suitable media type.

Do not put credentials, provider request bodies, or unrestricted user uploads into artifact
metadata. Metadata is expected to remain JSON-compatible and operator-visible.
