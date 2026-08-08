# Artifacts and traces

Artifacts are addressable outputs such as markdown, code, JSON, tables, charts, files,
images, SQL, and reports. Runtime events contain artifact references rather than inlining
potentially large or sensitive content.

Every agent run owns a trace. Model and tool operations are timed spans. Token usage and
optional cost accumulate on the trace and stream to Muru Workspace. Exporters can be added
without changing runtime execution.
