from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Mapping, Sequence
from typing import Any

try:
    import openai
except ModuleNotFoundError as exc:  # pragma: no cover - exercised without the extra installed
    from agentmuru.integrations.providers._common import dependency_error

    raise dependency_error("openai", "openai") from exc

from agentmuru.integrations.providers import ProviderConfigurationError
from agentmuru.integrations.providers._common import parse_tool_arguments, validate_settings
from agentmuru.models import (
    ModelCapabilities,
    ModelCompleted,
    ModelEvent,
    ModelFailed,
    ModelRequest,
    TextDelta,
    ToolCall,
    Usage,
)
from agentmuru.sessions import Message, MessageRole


class OpenAIModel:
    """AgentMuru model provider backed by OpenAI's Responses API."""

    name = "openai"
    capabilities = ModelCapabilities(tool_calling=True)

    def __init__(
        self,
        model: str = "gpt-5.6-terra",
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        client: Any | None = None,
    ) -> None:
        if not model.strip():
            raise ProviderConfigurationError("model must not be empty")
        self.model_id = model
        self._client = client
        self._client_options = {"api_key": api_key, "base_url": base_url, "max_retries": 0}

    async def stream(self, request: ModelRequest) -> AsyncIterator[ModelEvent]:
        kwargs = self._request_kwargs(request)
        provider_stream: Any | None = None
        try:
            if self._client is None:
                self._client = openai.AsyncOpenAI(**self._client_options)
            provider_stream = await self._client.responses.create(**kwargs)
            async for event in provider_stream:
                event_type = getattr(event, "type", "")
                if event_type == "response.output_text.delta":
                    delta = getattr(event, "delta", "")
                    if delta:
                        yield TextDelta(delta)
                    continue
                if event_type == "response.output_item.done":
                    item = getattr(event, "item", None)
                    if getattr(item, "type", "") != "function_call":
                        continue
                    try:
                        arguments = parse_tool_arguments(item.arguments)
                    except ProviderConfigurationError:
                        yield ModelFailed(
                            code="model_invalid_tool_arguments",
                            message="OpenAI returned invalid tool arguments.",
                            retryable=False,
                        )
                        return
                    yield ToolCall(id=item.call_id, name=item.name, arguments=arguments)
                    continue
                if event_type == "response.completed":
                    usage = getattr(getattr(event, "response", None), "usage", None)
                    yield ModelCompleted(
                        usage=Usage(
                            input_tokens=int(getattr(usage, "input_tokens", 0) or 0),
                            output_tokens=int(getattr(usage, "output_tokens", 0) or 0),
                        )
                    )
        except (asyncio.CancelledError, KeyboardInterrupt, SystemExit):
            raise
        except BaseException as exc:
            if isinstance(exc, GeneratorExit):
                raise
            yield self._failure_for(exc)
        finally:
            if provider_stream is not None:
                await provider_stream.close()

    def _request_kwargs(self, request: ModelRequest) -> dict[str, Any]:
        common, provider_options = validate_settings(request.settings)
        if "stop" in common:
            raise ProviderConfigurationError(
                "OpenAI Responses does not support the normalized 'stop' setting"
            )

        kwargs: dict[str, Any] = {
            "model": self.model_id,
            "input": _openai_input(request.messages),
            "stream": True,
            "store": False,
        }
        if request.instructions:
            kwargs["instructions"] = request.instructions
        if request.tools:
            kwargs["tools"] = _openai_tools(request.tools)
        kwargs.update(common)
        kwargs.update(provider_options)
        return kwargs

    @staticmethod
    def _failure_for(exc: BaseException) -> ModelFailed:
        if isinstance(exc, openai.AuthenticationError):
            return ModelFailed(
                "model_authentication", "OpenAI authentication failed.", False
            )
        if isinstance(exc, openai.PermissionDeniedError):
            return ModelFailed("model_permission", "OpenAI access was denied.", False)
        if isinstance(exc, openai.RateLimitError):
            return ModelFailed("model_rate_limit", "OpenAI rate limit reached.", True)
        if isinstance(exc, openai.APITimeoutError):
            return ModelFailed("model_timeout", "OpenAI request timed out.", True)
        if isinstance(exc, (openai.BadRequestError, openai.UnprocessableEntityError)):
            return ModelFailed("model_invalid_request", "OpenAI rejected the request.", False)
        if isinstance(exc, (openai.APIConnectionError, openai.InternalServerError)):
            return ModelFailed("model_unavailable", "OpenAI is temporarily unavailable.", True)
        return ModelFailed("model_provider_error", "OpenAI request failed.", False)


def _openai_input(messages: Sequence[Message]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for message in messages:
        if message.role == MessageRole.TOOL:
            if not message.tool_call_id:
                raise ProviderConfigurationError("tool message must include tool_call_id")
            items.append(
                {
                    "type": "function_call_output",
                    "call_id": message.tool_call_id,
                    "output": message.content,
                }
            )
            continue

        if message.content:
            items.append({"role": message.role.value, "content": message.content})
        if message.role == MessageRole.ASSISTANT:
            for tool_call in message.tool_calls:
                items.append(
                    {
                        "type": "function_call",
                        "call_id": tool_call.id,
                        "name": tool_call.name,
                        "arguments": json.dumps(
                            dict(tool_call.arguments),
                            ensure_ascii=False,
                            separators=(",", ":"),
                        ),
                    }
                )
    return items


def _openai_tools(tools: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "name": tool["name"],
            "description": tool.get("description", ""),
            "parameters": tool.get("input_schema", {"type": "object"}),
            "strict": False,
        }
        for tool in tools
    ]
