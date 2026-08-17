# Use a real model

Generate a starter with one official provider. The CLI writes the correct optional dependency
and provider constructor, but it never writes an API key.

## OpenAI

```powershell
muru init openai-agent --provider openai
$env:OPENAI_API_KEY = "your-key"
cd openai-agent
python -m pip install -r requirements.txt
muru run app:application
```

The starter uses `OpenAIModel` with `gpt-5.6-terra`. See the [OpenAI guide](../providers/openai.md)
for model overrides and request translation.

## Anthropic

```powershell
muru init anthropic-agent --provider anthropic
$env:ANTHROPIC_API_KEY = "your-key"
cd anthropic-agent
python -m pip install -r requirements.txt
muru run app:application
```

The starter uses `AnthropicModel` with `claude-sonnet-5`. See the
[Anthropic guide](../providers/anthropic.md).

## Google

```powershell
muru init google-agent --provider google
$env:GOOGLE_API_KEY = "your-key"
cd google-agent
python -m pip install -r requirements.txt
muru run app:application
```

The starter uses `GoogleGenAIModel` with `gemini-3.5-flash`. See the
[Google Gen AI guide](../providers/google.md).

## Keep credentials outside source

Provider SDKs read their standard environment variables when the first run starts. Do not put
keys in `app.py`, generated files, session metadata, tool arguments, or committed `.env` files.

## Keep the runtime portable

Only the provider import and model constructor differ among these starters. Agents, tools,
permissions, approval handling, sessions, events, and Workspace behavior stay on the same
AgentMuru contract.
