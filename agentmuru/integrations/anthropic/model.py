from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Mapping, Sequence
from typing import Any

try:
    import anthropic
except ModuleNotFoundError as exc:  # pragma: no cover - exercised without the extra installed
    from agentmuru.integrations.providers._common import dependency_error

    raise dependency_error("anthropic", "anthropic") from exc

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


class AnthropicModel:
    """AgentMuru model provider backed by Anthropic's Messages API."""

    name = "anthropic"
    capabilities = ModelCapabilities(tool_calling=True)

    def __init__(
        self,
        model: str = "claude-sonnet-5",
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        client: Any | None = None,
    ) -> None:
        if not model.strip():
            raise ProviderConfigurationError("model must not be empty")
        self.model_id = model
        self._client = client
        self._api_key = api_key
        self._base_url = base_url

    async def stream(self, request: ModelRequest) -> AsyncIterator[ModelEvent]:
        kwargs = self._request_kwargs(request)
        provider_stream: Any | None = None
        input_tokens = 0
        output_tokens = 0
        tool_blocks: dict[int, dict[str, Any]] = {}
        try:
            if self._client is None:
                self._client = anthropic.AsyncAnthropic(
                    api_key=self._api_key,
                    base_url=self._base_url,
                    max_retries=0,
                )
            provider_stream = await self._client.messages.create(**kwargs)
            async for event in provider_stream:
                event_type = getattr(event, "type", "")
                if event_type == "message_start":
                    usage = getattr(getattr(event, "message", None), "usage", None)
                    input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
                    output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
                    continue
                if event_type == "content_block_start":
                    block = getattr(event, "content_block", None)
                    if block is not None and getattr(block, "type", "") == "tool_use":
                        tool_blocks[event.index] = {
                            "id": block.id,
                            "name": block.name,
                            "input": getattr(block, "input", {}) or {},
                            "json": "",
                        }
                    continue
                if event_type == "content_block_delta":
                    delta = getattr(event, "delta", None)
                    delta_type = getattr(delta, "type", "")
                    if delta_type == "text_delta":
                        text = getattr(delta, "text", "")
                        if text:
                            yield TextDelta(text)
                    elif delta_type == "input_json_delta" and event.index in tool_blocks:
                        tool_blocks[event.index]["json"] += getattr(delta, "partial_json", "")
                    continue
                if event_type == "content_block_stop" and event.index in tool_blocks:
                    block = tool_blocks.pop(event.index)
                    try:
                        arguments = (
                            parse_tool_arguments(block["json"])
                            if block["json"]
                            else _object_arguments(block["input"])
                        )
                    except ProviderConfigurationError:
                        yield ModelFailed(
                            "model_invalid_tool_arguments",
                            "Anthropic returned invalid tool arguments.",
                            False,
                        )
                        return
                    yield ToolCall(
                        id=block["id"],
                        name=block["name"],
                        arguments=arguments,
                    )
                    continue
                if event_type == "message_delta":
                    usage = getattr(event, "usage", None)
                    output_tokens = int(
                        getattr(usage, "output_tokens", output_tokens) or output_tokens
                    )
                    continue
                if event_type == "message_stop":
                    yield ModelCompleted(Usage(input_tokens, output_tokens))
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
        system, messages = _anthropic_messages(request.messages, request.instructions)
        kwargs: dict[str, Any] = {
            "model": self.model_id,
            "messages": messages,
            "stream": True,
            "max_tokens": common.pop("max_output_tokens", 1024),
        }
        if system:
            kwargs["system"] = system
        if request.tools:
            kwargs["tools"] = _anthropic_tools(request.tools)
        if "stop" in common:
            kwargs["stop_sequences"] = _stop_sequences(common.pop("stop"))
        if "tool_choice" in common:
            kwargs["tool_choice"] = _anthropic_tool_choice(common.pop("tool_choice"))
        kwargs.update(common)
        kwargs.update(provider_options)
        return kwargs

    @staticmethod
    def _failure_for(exc: BaseException) -> ModelFailed:
        if isinstance(exc, anthropic.AuthenticationError):
            return ModelFailed(
                "model_authentication", "Anthropic authentication failed.", False
            )
        if isinstance(exc, anthropic.PermissionDeniedError):
            return ModelFailed("model_permission", "Anthropic access was denied.", False)
        if isinstance(exc, anthropic.RateLimitError):
            return ModelFailed("model_rate_limit", "Anthropic rate limit reached.", True)
        if isinstance(exc, anthropic.APITimeoutError):
            return ModelFailed("model_timeout", "Anthropic request timed out.", True)
        if isinstance(exc, (anthropic.BadRequestError, anthropic.UnprocessableEntityError)):
            return ModelFailed(
                "model_invalid_request", "Anthropic rejected the request.", False
            )
        if isinstance(exc, (anthropic.APIConnectionError, anthropic.InternalServerError)):
            return ModelFailed(
                "model_unavailable", "Anthropic is temporarily unavailable.", True
            )
        return ModelFailed("model_provider_error", "Anthropic request failed.", False)


def _anthropic_messages(
    messages: Sequence[Message], instructions: str
) -> tuple[str, list[dict[str, Any]]]:
    system_parts = [instructions] if instructions else []
    translated: list[dict[str, Any]] = []
    for message in messages:
        if message.role == MessageRole.SYSTEM:
            if message.content:
                system_parts.append(message.content)
            continue
        if message.role == MessageRole.TOOL:
            if not message.tool_call_id:
                raise ProviderConfigurationError("tool message must include tool_call_id")
            translated.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": message.tool_call_id,
                            "content": message.content,
                        }
                    ],
                }
            )
            continue
        if message.role == MessageRole.ASSISTANT and message.tool_calls:
            content: list[dict[str, Any]] = []
            if message.content:
                content.append({"type": "text", "text": message.content})
            content.extend(
                {
                    "type": "tool_use",
                    "id": tool_call.id,
                    "name": tool_call.name,
                    "input": dict(tool_call.arguments),
                }
                for tool_call in message.tool_calls
            )
            translated.append({"role": "assistant", "content": content})
            continue
        translated.append({"role": message.role.value, "content": message.content})
    return "\n\n".join(system_parts), translated


def _anthropic_tools(tools: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "name": tool["name"],
            "description": tool.get("description", ""),
            "input_schema": tool.get("input_schema", {"type": "object"}),
        }
        for tool in tools
    ]


def _object_arguments(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ProviderConfigurationError("tool arguments must be a valid JSON object")
    return dict(value)


def _stop_sequences(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Sequence) and all(isinstance(item, str) for item in value):
        return list(value)
    raise ProviderConfigurationError("stop must be a string or sequence of strings")


def _anthropic_tool_choice(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    if value == "required":
        return {"type": "any"}
    if value in {"auto", "none"}:
        return {"type": value}
    return {"type": "tool", "name": value}
