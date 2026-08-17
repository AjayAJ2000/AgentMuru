# Artifacts and traces

Artifacts record useful outputs. Traces record how a run produced them. They are separate so an
application can retain a report without treating internal timing details as report content.

## Artifacts

An `Artifact` belongs to one session and can optionally belong to a run. It has a kind, name,
content, MIME type, creator, metadata, and creation and update timestamps.

Supported `ArtifactKind` values are Markdown, code, JSON, table, chart, file, image, SQL, and
report. Stores do not interpret the content; the kind and MIME type tell the Workspace or
another consumer how to present it.

Create an artifact through `Runtime.create_artifact()` so the runtime validates the session,
persists the output, and emits `artifact.created`.

## Traces

Each run starts a `Trace`. A trace contains named spans with kind, parent, status, UTC timing,
duration, and application-defined attributes. The runtime creates model and tool spans as work
progresses.

`Usage` aggregates input tokens, output tokens, and optional cost. Providers always normalize
token counts when their SDK supplies usage. Cost remains `None` unless an application or
provider supplies it.

## Operator access

The server exposes run traces at `/api/v1/runs/{run_id}/traces` and individual artifact content
at `/api/v1/artifacts/{artifact_id}`. Session snapshots list artifact metadata without loading
every content payload.

## Retention

In-memory traces last for the runtime process. SQLite persists artifacts but the default tracer
is in memory. Export or replace trace storage when operational retention is required.
