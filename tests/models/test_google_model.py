from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest

from agentmuru.integrations.google import GoogleGenAIModel
from agentmuru.models import ModelCompleted, ModelFailed, ModelRequest, TextDelta, ToolCall, Usage
from agentmuru.sessions import AssistantToolCall, Message, MessageRole


class FakeGoogleStream:
    def __init__(self, chunks: list[Any]) -> None:
        self.chunks = chunks
        self.closed = False

    def __aiter__(self) -> FakeGoogleStream:
        self._iterator = iter(self.chunks)
        return self

    async def __anext__(self) -> Any:
        try:
            return next(self._iterator)
        except StopIteration as exc:
            raise StopAsyncIteration from exc

    async def aclose(self) -> None:
        self.closed = True


class FakeGoogleModels:
    def __init__(self, stream: FakeGoogleStream | BaseException) -> None:
        self.stream = stream
        self.request: dict[str, Any] | None = None

    async def generate_content_stream(self, **kwargs: Any) -> FakeGoogleStream:
        self.request = kwargs
        if isinstance(self.stream, BaseException):
            raise self.stream
        return self.stream


@dataclass
class FakeGoogleAio:
    models: FakeGoogleModels


@dataclass
class FakeGoogleClient:
    aio: FakeGoogleAio


def google_chunks(arguments: Any = None) -> list[Any]:
    if arguments is None:
        arguments = {"query": "muru"}
    return [
        SimpleNamespace(
            candidates=[
                SimpleNamespace(
                    content=SimpleNamespace(
                        parts=[SimpleNamespace(text="Ready", function_call=None)]
                    )
                )
            ],
            usage_metadata=None,
        ),
        SimpleNamespace(
            candidates=[
                SimpleNamespace(
                    content=SimpleNamespace(
                        parts=[
                            SimpleNamespace(
                                text=None,
                                function_call=SimpleNamespace(
                                    id="call-2", name="lookup", args=arguments
                                ),
                            )
                        ]
                    )
                )
            ],
            usage_metadata=SimpleNamespace(
                prompt_token_count=11,
                candidates_token_count=3,
            ),
        ),
    ]


def provider_request() -> ModelRequest:
    return ModelRequest(
        messages=(
            Message(role=MessageRole.USER, content="Find Muru"),
            Message(
                role=MessageRole.ASSISTANT,
                content="Checking",
                tool_calls=(
                    AssistantToolCall(
                        id="call-1", name="lookup", arguments={"query": "first"}
                    ),
                ),
            ),
            Message(
                role=MessageRole.TOOL,
                content='{"result":"found"}',
                name="lookup",
                tool_call_id="call-1",
            ),
        ),
        instructions="Be concise",
        tools=(
            {
                "name": "lookup",
                "description": "Find one record",
                "input_schema": {"type": "object", "properties": {}},
            },
        ),
        settings={"temperature": 0.2, "max_output_tokens": 64},
    )


@pytest.mark.asyncio
async def test_google_stream_normalizes_tool_usage_and_request() -> None:
    stream = FakeGoogleStream(google_chunks())
    models = FakeGoogleModels(stream)
    provider = GoogleGenAIModel(
        model="gemini-3.5-flash",
        client=FakeGoogleClient(aio=FakeGoogleAio(models=models)),
    )

    events = [event async for event in provider.stream(provider_request())]

    assert events == [
        TextDelta("Ready"),
        ToolCall(id="call-2", name="lookup", arguments={"query": "muru"}),
        ModelCompleted(usage=Usage(input_tokens=11, output_tokens=3)),
    ]
    assert stream.closed is True
    assert models.request == {
        "model": "gemini-3.5-flash",
        "contents": [
            {"role": "user", "parts": [{"text": "Find Muru"}]},
            {
                "role": "model",
                "parts": [
                    {"text": "Checking"},
                    {
                        "function_call": {
                            "id": "call-1",
                            "name": "lookup",
                            "args": {"query": "first"},
                        }
                    },
                ],
            },
            {
                "role": "user",
                "parts": [
                    {
                        "function_response": {
                            "id": "call-1",
                            "name": "lookup",
                            "response": {"result": "found"},
                        }
                    }
                ],
            },
        ],
        "config": {
            "system_instruction": "Be concise",
            "tools": [
                {
                    "function_declarations": [
                        {
                            "name": "lookup",
                            "description": "Find one record",
                            "parameters_json_schema": {
                                "type": "object",
                                "properties": {},
                            },
                        }
                    ]
                }
            ],
            "automatic_function_calling": {"disable": True},
            "temperature": 0.2,
            "max_output_tokens": 64,
        },
    }
    assert provider.name == "google"
    assert provider.model_id == "gemini-3.5-flash"


@pytest.mark.asyncio
async def test_google_stream_fails_safely_for_non_object_tool_arguments() -> None:
    provider = GoogleGenAIModel(
        client=FakeGoogleClient(
            aio=FakeGoogleAio(
                models=FakeGoogleModels(FakeGoogleStream(google_chunks(["bad"])))
            )
        )
    )

    events = [event async for event in provider.stream(provider_request())]

    assert events[-1] == ModelFailed(
        "model_invalid_tool_arguments",
        "Google returned invalid tool arguments.",
        False,
    )
    assert not any(isinstance(event, ToolCall) for event in events)


@pytest.mark.asyncio
async def test_google_stream_hides_unclassified_provider_error() -> None:
    provider = GoogleGenAIModel(
        client=FakeGoogleClient(
            aio=FakeGoogleAio(
                models=FakeGoogleModels(RuntimeError("response body with api-key-secret"))
            )
        )
    )

    events = [event async for event in provider.stream(ModelRequest(messages=()))]

    assert events == [ModelFailed("model_provider_error", "Google request failed.", False)]
    assert "api-key-secret" not in repr(events)
