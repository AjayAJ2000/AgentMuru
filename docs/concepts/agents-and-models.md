# Agents and models

An `Agent` combines instructions, one model provider, tools, granted permissions, and model
settings. It is immutable after construction, which makes the runtime definition inspectable.

```python
from agentmuru import Agent, FakeModel

agent = Agent(
    name="support",
    description="Answers product support questions",
    instructions="Use tools for account facts. Never invent account state.",
    model=FakeModel.responses("The account is active."),
    tools=(),
    permissions=frozenset(),
    model_settings={"temperature": 0.2, "max_output_tokens": 300},
)
```

## Model provider contract

A provider exposes `name`, `model_id`, `capabilities`, and an async `stream()` method. The
stream yields only AgentMuru events:

- `TextDelta` for assistant text.
- `ToolCall` after arguments form a complete object.
- `ModelCompleted` with normalized usage.
- `ModelFailed` with a safe, stable error code.

Official providers translate their native APIs at this boundary. The runtime never depends on
OpenAI, Anthropic, or Google response classes.

## Deterministic models

`FakeModel` is a real implementation of the same provider protocol. Use `responses()` for
fixed text or `turns()` for explicit text, tool-call, completion, and failure sequences. It is
the preferred model for tests and the default generated starter.

## Settings

`Agent.model_settings` is copied into each `ModelRequest`. The official adapters accept the
normalized settings documented in the [provider contract](../reference/providers.md). Put
provider-specific options under `provider_options`; reserved connection and request fields are
rejected before a request starts.

## Multiple agents

`Application.agent` is the primary agent. Put handoff targets in `Application.agents`. Names
must be unique across the complete application, and every handoff resolves a declared target by
name.
