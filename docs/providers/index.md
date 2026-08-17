# Choose a provider

AgentMuru 0.3 ships three adapters built on the official provider SDKs. They translate provider
messages and streams into the same runtime events, so tool governance and persistence remain
provider-neutral.

| Provider | Extra | Default model | Guide |
| --- | --- | --- | --- |
| OpenAI Responses | `agentmuru[openai]` | `gpt-5.6-terra` | [Configure OpenAI](openai.md) |
| Anthropic Messages | `agentmuru[anthropic]` | `claude-sonnet-5` | [Configure Anthropic](anthropic.md) |
| Google Gen AI | `agentmuru[google]` | `gemini-3.5-flash` | [Configure Google](google.md) |
| Deterministic local fake | Core package | `fake` | [Agents and models](../concepts/agents-and-models.md#deterministic-models) |

## Stable runtime contract

All adapters:

- stream `TextDelta` events;
- emit `ToolCall` only with complete object arguments;
- report normalized input and output token usage;
- map provider failures to stable, secret-safe `ModelFailed` codes;
- propagate cancellation and close active streams;
- preserve prior assistant tool calls and tool results on the next turn.

## Install one SDK

```powershell
python -m pip install "agentmuru[openai]>=0.3,<0.4"
```

Use `agentmuru[providers]` only when one environment must exercise every adapter. Keeping one
provider extra in an application reduces its dependency and update surface.

## Switch providers

Change the import and model constructor. Do not change the agent, tools, runtime, or stores.

```python
from agentmuru.integrations.openai import OpenAIModel

agent = Agent(
    name="assistant",
    instructions="Answer clearly.",
    model=OpenAIModel(),
)
```

Each model constructor accepts an explicit model ID. Tests may inject a provider client to avoid
credentials and network calls.

## Errors

Authentication, permission, rate limit, timeout, invalid request, unavailable service, invalid
tool arguments, and unclassified provider failures map to documented AgentMuru codes. Provider
response bodies and API keys never become public failure messages.

See the [provider contract reference](../reference/providers.md) for normalized settings and
error codes.
