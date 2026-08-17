from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest

from agentmuru.integrations.openai import OpenAIModel
from agentmuru.models import ModelCompleted, ModelFailed, ModelRequest, TextDelta, ToolCall, Usage
from agentmuru.sessions import AssistantToolCall, Message, MessageRole


class FakeOpenAIStream:
    def __init__(self, events: list[Any]) -> None:
        self.events = events
        self.closed = False

    def __aiter__(self) -> FakeOpenAIStream:
        self._iterator = iter(self.events)
        return self

    async def __anext__(self) -> Any:
        try:
            return next(self._iterator)
        except StopIteration as exc:
            raise StopAsyncIteration from exc

    async def close(self) -> None:
        self.closed = True


class FakeResponses:
    def __init__(self, stream: FakeOpenAIStream | BaseException) -> None:
        self.stream = stream
        self.request: dict[str, Any] | None = None

    async def create(self, **kwargs: Any) -> FakeOpenAIStream:
        self.request = kwargs
        if isinstance(self.stream, BaseException):
            raise self.stream
        return self.stream


@dataclass
class FakeOpenAIClient:
    responses: FakeResponses


def response_events(arguments: str = '{"query":"muru"}') -> list[Any]:
    return [
        SimpleNamespace(type="response.output_text.delta", delta="Ready"),
        SimpleNamespace(
            type="response.output_item.done",
            item=SimpleNamespace(
                type="function_call",
                call_id="call-2",
                name="lookup",
                arguments=arguments,
            ),
        ),
        SimpleNamespace(
            type="response.completed",
            response=SimpleNamespace(
                usage=SimpleNamespace(input_tokens=12, output_tokens=4)
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
                        id="call-1",
                        name="lookup",
                        arguments={"query": "first"},
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
                "input_schema": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            },
        ),
        settings={"temperature": 0.2, "max_output_tokens": 64},
    )


@pytest.mark.asyncio
async def test_openai_stream_normalizes_text_tool_usage_and_request() -> None:
    stream = FakeOpenAIStream(response_events())
    responses = FakeResponses(stream)
    provider = OpenAIModel(
        model="gpt-5.6-terra",
        client=FakeOpenAIClient(responses=responses),
    )

    events = [event async for event in provider.stream(provider_request())]

    assert events == [
        TextDelta("Ready"),
        ToolCall(id="call-2", name="lookup", arguments={"query": "muru"}),
        ModelCompleted(usage=Usage(input_tokens=12, output_tokens=4)),
    ]
    assert stream.closed is True
    assert responses.request == {
        "model": "gpt-5.6-terra",
        "instructions": "Be concise",
        "input": [
            {"role": "user", "content": "Find Muru"},
            {"role": "assistant", "content": "Checking"},
            {
                "type": "function_call",
                "call_id": "call-1",
                "name": "lookup",
                "arguments": '{"query":"first"}',
            },
            {
                "type": "function_call_output",
                "call_id": "call-1",
                "output": '{"result":"found"}',
            },
        ],
        "tools": [
            {
                "type": "function",
                "name": "lookup",
                "description": "Find one record",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
                "strict": False,
            }
        ],
        "stream": True,
        "store": False,
        "temperature": 0.2,
        "max_output_tokens": 64,
    }
    assert provider.name == "openai"
    assert provider.model_id == "gpt-5.6-terra"


@pytest.mark.asyncio
async def test_openai_stream_fails_safely_for_malformed_tool_arguments() -> None:
    provider = OpenAIModel(
        model="gpt-5.6-terra",
        client=FakeOpenAIClient(
            responses=FakeResponses(FakeOpenAIStream(response_events('["not-an-object"]')))
        ),
    )

    events = [event async for event in provider.stream(provider_request())]

    assert events[-1] == ModelFailed(
        code="model_invalid_tool_arguments",
        message="OpenAI returned invalid tool arguments.",
        retryable=False,
    )
    assert not any(isinstance(event, ToolCall) for event in events)


@pytest.mark.asyncio
async def test_openai_stream_hides_unclassified_provider_error() -> None:
    provider = OpenAIModel(
        model="gpt-5.6-terra",
        client=FakeOpenAIClient(
            responses=FakeResponses(RuntimeError("response body with sk-private"))
        ),
    )

    events = [event async for event in provider.stream(ModelRequest(messages=()))]

    assert events == [
        ModelFailed(
            code="model_provider_error",
            message="OpenAI request failed.",
            retryable=False,
        )
    ]
    assert "sk-private" not in repr(events)
