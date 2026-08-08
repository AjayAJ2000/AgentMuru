# Agents and models

`Agent` is an immutable, provider-neutral definition containing instructions, model,
tools, permissions, settings, and metadata. A `ModelProvider` emits normalized text,
tool-call, completion, usage, or failure events. Runtime code never imports a vendor SDK.

`FakeModel.responses(...)`, `FakeModel.script(...)`, and `FakeModel.turns(...)` provide
deterministic development and tests. Production adapters should translate vendor payloads
only at the provider boundary.
