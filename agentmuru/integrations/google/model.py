from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Mapping, Sequence
from typing import Any

try:
    from google import genai
    from google.genai import errors as genai_errors
except (ImportError, ModuleNotFoundError) as exc:  # pragma: no cover - no extra installed
    from agentmuru.integrations.providers._common import dependency_error

    raise dependency_error("google", "google-genai") from exc

from agentmuru.integrations.providers import ProviderConfigurationError
from agentmuru.integrations.providers._common import validate_settings
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


class GoogleGenAIModel:
    """AgentMuru model provider backed by Google's Gen AI SDK."""

    name = "google"
    capabilities = ModelCapabilities(tool_calling=True)

    def __init__(
        self,
        model: str = "gemini-3.5-flash",
        *,
        api_key: str | None = None,
        client: Any | None = None,
    ) -> None:
        if not model.strip():
            raise ProviderConfigurationError("model must not be empty")
        self.model_id = model
        self._client = client
        self._api_key = api_key

    async def stream(self, request: ModelRequest) -> AsyncIterator[ModelEvent]:
        kwargs = self._request_kwargs(request)
        provider_stream: Any | None = None
        input_tokens = 0
        output_tokens = 0
        generated_call_id = 0
        try:
            if self._client is None:
                self._client = genai.Client(api_key=self._api_key)
            provider_stream = await self._client.aio.models.generate_content_stream(**kwargs)
            async for chunk in provider_stream:
                for candidate in getattr(chunk, "candidates", None) or []:
                    content = getattr(candidate, "content", None)
                    for part in getattr(content, "parts", None) or []:
                        text = getattr(part, "text", None)
                        if text:
                            yield TextDelta(text)
                        function_call = getattr(part, "function_call", None)
                        if function_call is None:
                            continue
                        arguments = getattr(function_call, "args", None)
                        if not isinstance(arguments, Mapping):
                            yield ModelFailed(
                                "model_invalid_tool_arguments",
                                "Google returned invalid tool arguments.",
                                False,
                            )
                            return
                        generated_call_id += 1
                        call_id = getattr(function_call, "id", None)
                        yield ToolCall(
                            id=call_id or f"google-call-{generated_call_id}",
                            name=function_call.name,
                            arguments=dict(arguments),
                        )
                usage = getattr(chunk, "usage_metadata", None)
                if usage is not None:
                    input_tokens = int(
                        getattr(usage, "prompt_token_count", input_tokens) or input_tokens
                    )
                    output_tokens = int(
                        getattr(usage, "candidates_token_count", output_tokens)
                        or output_tokens
                    )
            yield ModelCompleted(Usage(input_tokens, output_tokens))
        except (asyncio.CancelledError, KeyboardInterrupt, SystemExit):
            raise
        except BaseException as exc:
            if isinstance(exc, GeneratorExit):
                raise
            yield self._failure_for(exc)
        finally:
            if provider_stream is not None:
                close = getattr(provider_stream, "aclose", None)
                if close is not None:
                    await close()

    def _request_kwargs(self, request: ModelRequest) -> dict[str, Any]:
        common, provider_options = validate_settings(request.settings)
        system, contents = _google_contents(request.messages, request.instructions)
        config: dict[str, Any] = dict(provider_options)
        if system:
            config["system_instruction"] = system
        if request.tools:
            config["tools"] = _google_tools(request.tools)
            config["automatic_function_calling"] = {"disable": True}
        if "stop" in common:
            config["stop_sequences"] = _stop_sequences(common.pop("stop"))
        if "tool_choice" in common:
            config["tool_config"] = _google_tool_choice(common.pop("tool_choice"))
        config.update(common)
        return {"model": self.model_id, "contents": contents, "config": config}

    @staticmethod
    def _failure_for(exc: BaseException) -> ModelFailed:
        if isinstance(exc, genai_errors.ClientError):
            code = getattr(exc, "code", None)
            if code == 401:
                return ModelFailed(
                    "model_authentication", "Google authentication failed.", False
                )
            if code == 403:
                return ModelFailed("model_permission", "Google access was denied.", False)
            if code == 429:
                return ModelFailed("model_rate_limit", "Google rate limit reached.", True)
            if code in {408, 504}:
                return ModelFailed("model_timeout", "Google request timed out.", True)
            return ModelFailed("model_invalid_request", "Google rejected the request.", False)
        if isinstance(exc, genai_errors.ServerError):
            return ModelFailed(
                "model_unavailable", "Google is temporarily unavailable.", True
            )
        return ModelFailed("model_provider_error", "Google request failed.", False)


def _google_contents(
    messages: Sequence[Message], instructions: str
) -> tuple[str, list[dict[str, Any]]]:
    system_parts = [instructions] if instructions else []
    contents: list[dict[str, Any]] = []
    for message in messages:
        if message.role == MessageRole.SYSTEM:
            if message.content:
                system_parts.append(message.content)
            continue
        if message.role == MessageRole.TOOL:
            if not message.tool_call_id:
                raise ProviderConfigurationError("tool message must include tool_call_id")
            if not message.name:
                raise ProviderConfigurationError("tool message must include name")
            contents.append(
                {
                    "role": "user",
                    "parts": [
                        {
                            "function_response": {
                                "id": message.tool_call_id,
                                "name": message.name,
                                "response": _tool_response(message.content),
                            }
                        }
                    ],
                }
            )
            continue
        parts: list[dict[str, Any]] = []
        if message.content:
            parts.append({"text": message.content})
        if message.role == MessageRole.ASSISTANT:
            parts.extend(
                {
                    "function_call": {
                        "id": tool_call.id,
                        "name": tool_call.name,
                        "args": dict(tool_call.arguments),
                    }
                }
                for tool_call in message.tool_calls
            )
        contents.append(
            {
                "role": "model" if message.role == MessageRole.ASSISTANT else "user",
                "parts": parts,
            }
        )
    return "\n\n".join(system_parts), contents


def _google_tools(tools: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "function_declarations": [
                {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters_json_schema": tool.get(
                        "input_schema", {"type": "object"}
                    ),
                }
                for tool in tools
            ]
        }
    ]


def _tool_response(content: str) -> dict[str, Any]:
    try:
        decoded = json.loads(content)
    except json.JSONDecodeError:
        return {"output": content}
    return decoded if isinstance(decoded, dict) else {"output": decoded}


def _stop_sequences(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Sequence) and all(isinstance(item, str) for item in value):
        return list(value)
    raise ProviderConfigurationError("stop must be a string or sequence of strings")


def _google_tool_choice(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    modes = {"auto": "AUTO", "required": "ANY", "none": "NONE"}
    function_calling_config: dict[str, Any] = {"mode": modes.get(value, "ANY")}
    if value not in modes:
        function_calling_config["allowed_function_names"] = [value]
    return {"function_calling_config": function_calling_config}
