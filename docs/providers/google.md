# Google Gen AI

`GoogleGenAIModel` uses the official `google-genai` SDK and asynchronous content streaming.

## Install

```powershell
python -m pip install "agentmuru[google]>=0.3,<0.4"
$env:GOOGLE_API_KEY = "your-key"
```

The client is created on the first model turn, so importing an application does not require a
credential or request the network.

## Configure

```python
from agentmuru import Agent, Application
from agentmuru.integrations.google import GoogleGenAIModel

agent = Agent(
    name="google-assistant",
    instructions="Use tools for external facts.",
    model=GoogleGenAIModel(model="gemini-3.5-flash"),
    model_settings={
        "temperature": 0.2,
        "max_output_tokens": 800,
    },
)

application = Application(agent=agent, title="Google Agent")
```

Run the example:

```powershell
muru run examples.providers.google_agent:application
```

## Request translation

System messages and application instructions become `system_instruction`. User messages use
the `user` role, while assistant messages use `model`. Prior tool calls become `function_call`
parts and tool results become `function_response` parts.

AgentMuru sends function declarations through the generation config and disables SDK automatic
function calling. This keeps permission, approval, execution, and persistence inside the
AgentMuru runtime.

Function-call parts map to `ToolCall` after object validation. When Google omits a call ID, the
adapter creates a stable local ID for that stream. Final usage metadata supplies prompt and
candidate token counts.

## Provider options

Google-specific `provider_options` merge into the generation config. Normalized `stop` maps to
`stop_sequences`. Normalized tool choice maps to the function-calling config.

Pass `api_key` directly or inject an initialized `client` when application configuration should
not use `GOOGLE_API_KEY`.

See the [Gemini models documentation](https://ai.google.dev/gemini-api/docs/models) for current
model availability, regions, and quotas.
