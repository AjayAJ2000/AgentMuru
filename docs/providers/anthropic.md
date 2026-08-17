# Anthropic

`AnthropicModel` uses the official asynchronous Anthropic SDK and Messages streaming API.

## Install

```powershell
python -m pip install "agentmuru[anthropic]>=0.3,<0.4"
$env:ANTHROPIC_API_KEY = "your-key"
```

The SDK reads the environment variable when the first turn starts.

## Configure

```python
from agentmuru import Agent, Application
from agentmuru.integrations.anthropic import AnthropicModel

agent = Agent(
    name="anthropic-assistant",
    instructions="Use tools for external facts.",
    model=AnthropicModel(model="claude-sonnet-5"),
    model_settings={
        "temperature": 0.2,
        "max_output_tokens": 800,
    },
)

application = Application(agent=agent, title="Anthropic Agent")
```

Run the example:

```powershell
muru run examples.providers.anthropic_agent:application
```

## Request translation

Application instructions and system messages become the Messages `system` value. User and
assistant messages keep their roles. Prior assistant tool calls become `tool_use` blocks, and
tool results become user-role `tool_result` blocks linked by tool-use ID.

The adapter collects `input_json_delta` fragments by content-block index. It emits one
`ToolCall` after `content_block_stop` confirms that the accumulated value is a JSON object.
Message start and delta usage become normalized input and output token counts.

## Output limit

Anthropic requires `max_tokens`. AgentMuru maps `max_output_tokens` to that field and uses 1024
when the normalized setting is absent.

## Tool choice

Normalized `auto`, `required`, and `none` map to Anthropic tool-choice objects. Any other string
selects one tool by name. A provider-native object can be supplied when the application needs a
new SDK feature.

AgentMuru-owned clients set `max_retries=0`. Pass `api_key`, `base_url`, or an injected `client`
when application-level configuration is required.

See the [Anthropic models overview](https://docs.anthropic.com/en/docs/about-claude/models) for
current model availability and access requirements.
