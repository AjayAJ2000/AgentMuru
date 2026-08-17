# OpenAI

`OpenAIModel` uses the official asynchronous OpenAI SDK and the Responses API.

## Install

```powershell
python -m pip install "agentmuru[openai]>=0.3,<0.4"
$env:OPENAI_API_KEY = "your-key"
```

The environment variable is read by the SDK when the first model turn starts. The provider can
be imported and the application can be inspected before a credential is present.

## Configure

```python
from agentmuru import Agent, Application
from agentmuru.integrations.openai import OpenAIModel

agent = Agent(
    name="openai-assistant",
    instructions="Use tools for external facts.",
    model=OpenAIModel(model="gpt-5.6-terra"),
    model_settings={
        "temperature": 0.2,
        "max_output_tokens": 800,
    },
)

application = Application(agent=agent, title="OpenAI Agent")
```

Run the full example:

```powershell
muru run examples.providers.openai_agent:application
```

## Request translation

AgentMuru sends `instructions`, conversation input, function tools, `stream=True`, and
`store=False` through `AsyncOpenAI.responses.create()`. Assistant tool calls become
`function_call` items, and tool results become `function_call_output` items linked by call ID.

Text delta events map to `TextDelta`. Completed function-call items map to `ToolCall` after JSON
object validation. The completed response supplies input and output token counts.

## Connection options

Pass `api_key` or `base_url` to the constructor when environment discovery is not appropriate:

```python
model = OpenAIModel(
    model="gpt-5.6-terra",
    api_key=secret_from_vault,
    base_url="https://api.openai.com/v1",
)
```

AgentMuru-owned clients set `max_retries=0`. Retry policy belongs at the runtime or application
boundary so one SDK does not hide duplicate model turns. An injected `client` keeps its owner
configuration.

## Settings note

The Responses API adapter supports `max_output_tokens`, `temperature`, `top_p`, and
`tool_choice`. The normalized `stop` setting is rejected because this Responses path does not
accept it. Put supported Responses-specific request fields under `provider_options`.

See the [OpenAI model documentation](https://platform.openai.com/docs/models) for current model
availability and account access.
