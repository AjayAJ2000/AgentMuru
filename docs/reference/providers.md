# Provider contract

A model provider implements this structural protocol:

```python
class ModelProvider(Protocol):
    name: str
    model_id: str
    capabilities: ModelCapabilities

    def stream(self, request: ModelRequest) -> AsyncIterator[ModelEvent]: ...
```

## Request

`ModelRequest` contains conversation messages, one instructions string, normalized tool schemas,
and settings. Assistant messages can carry complete prior tool calls. Tool messages link to the
call ID they answer.

## Normalized events

- `TextDelta(text)` contains new assistant text.
- `ToolCall(id, name, arguments)` contains one complete object argument mapping.
- `ModelCompleted(usage)` ends a successful request.
- `ModelFailed(code, message, retryable)` ends a provider failure.

Do not emit a `ToolCall` for partial or non-object JSON. Do not include provider response bodies,
request headers, or credentials in `ModelFailed.message`.

## Settings

Official adapters validate these normalized settings:

| Setting | Meaning |
| --- | --- |
| `max_output_tokens` | Maximum provider output tokens |
| `temperature` | Provider sampling temperature |
| `top_p` | Nucleus sampling threshold |
| `stop` | One string or a sequence of strings when supported |
| `tool_choice` | `auto`, `required`, `none`, a tool name, or provider-native value |
| `provider_options` | Provider-specific request options |

Unknown normalized settings fail before a request. `provider_options` must be a mapping. It
cannot replace reserved fields such as API key, base URL, client, model, stream, messages,
instructions, input, or tools.

OpenAI Responses rejects `stop` on this adapter path. Anthropic maps it to `stop_sequences`.
Google maps it into generation config.

## Capabilities

`ModelCapabilities` reports text, streaming, tool calling, structured output, vision, audio,
reasoning, and embeddings. The 0.3 official adapters declare text, streaming, and tool calling.
Use `capabilities.require(name)` when application construction depends on one capability.

## Stable failure codes

| Code | Retryable by default |
| --- | --- |
| `model_authentication` | No |
| `model_permission` | No |
| `model_rate_limit` | Yes |
| `model_timeout` | Yes |
| `model_invalid_request` | No |
| `model_unavailable` | Yes |
| `model_invalid_tool_arguments` | No |
| `model_provider_error` | No |

Application retry policy should use the code and `retryable` flag, plus its own idempotency and
cost constraints.

## Cancellation and resource cleanup

Providers must propagate `asyncio.CancelledError` and close the active SDK stream in a `finally`
path. AgentMuru-owned official clients disable hidden SDK retries. Injected clients retain their
owner's configuration.

## Optional dependency errors

Importing an official adapter without its SDK raises `ProviderDependencyError` with the exact
extra to install, such as `python -m pip install "agentmuru[openai]"`.
