from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest

from agentmuru.integrations.anthropic import AnthropicModel
from agentmuru.models import ModelCompleted, ModelFailed, ModelRequest, TextDelta, ToolCall, Usage
from agentmuru.sessions import AssistantToolCall, Message, MessageRole


class FakeAnthropicStream:
    def __init__(self, events: list[Any]) -> None:
        self.events = events
        self.closed = False

    def __aiter__(self) -> FakeAnthropicStream:
        self._iterator = iter(self.events)
        return self

    async def __anext__(self) -> Any:
        try:
            return next(self._iterator)
        except StopIteration as exc:
            raise StopAsyncIteration from exc

    async def close(self) -> None:
        self.closed = True


class FakeMessages:
    def __init__(self, stream: FakeAnthropicStream | BaseException) -> None:
        self.stream = stream
        self.request: dict[str, Any] | None = None

    async def create(self, **kwargs: Any) -> FakeAnthropicStream:
        self.request = kwargs
        if isinstance(self.stream, BaseException):
            raise self.stream
        return self.stream


@dataclass
class FakeAnthropicClient:
    messages: FakeMessages


def anthropic_events(arguments: tuple[str, ...] = ('{"query":', '"muru"}')) -> list[Any]:
    events: list[Any] = [
        SimpleNamespace(
            type="message_start",
            message=SimpleNamespace(
                usage=SimpleNamespace(input_tokens=10, output_tokens=0)
            ),
        ),
        SimpleNamespace(
            type="content_block_delta",
            index=0,
            delta=SimpleNamespace(type="text_delta", text="Ready"),
        ),
        SimpleNamespace(
            type="content_block_start",
            index=1,
            content_block=SimpleNamespace(
                type="tool_use", id="call-2", name="lookup", input={}
            ),
        ),
    ]
    events.extend(
        SimpleNamespace(
            type="content_block_delta",
            index=1,
            delta=SimpleNamespace(type="input_json_delta", partial_json=part),
        )
        for part in arguments
    )
    events.extend(
        [
            SimpleNamespace(type="content_block_stop", index=1),
            SimpleNamespace(
                type="message_delta",
                usage=SimpleNamespace(output_tokens=5),
            ),
            SimpleNamespace(type="message_stop"),
        ]
    )
    return events


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
async def test_anthropic_stream_normalizes_tool_arguments_usage_and_request() -> None:
    stream = FakeAnthropicStream(anthropic_events())
    messages = FakeMessages(stream)
    provider = AnthropicModel(
        model="claude-sonnet-5",
        client=FakeAnthropicClient(messages=messages),
    )

    events = [event async for event in provider.stream(provider_request())]

    assert events == [
        TextDelta("Ready"),
        ToolCall(id="call-2", name="lookup", arguments={"query": "muru"}),
        ModelCompleted(usage=Usage(input_tokens=10, output_tokens=5)),
    ]
    assert stream.closed is True
    assert messages.request == {
        "model": "claude-sonnet-5",
        "system": "Be concise",
        "messages": [
            {"role": "user", "content": "Find Muru"},
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "Checking"},
                    {
                        "type": "tool_use",
                        "id": "call-1",
                        "name": "lookup",
                        "input": {"query": "first"},
                    },
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "call-1",
                        "content": '{"result":"found"}',
                    }
                ],
            },
        ],
        "tools": [
            {
                "name": "lookup",
                "description": "Find one record",
                "input_schema": {"type": "object", "properties": {}},
            }
        ],
        "stream": True,
        "temperature": 0.2,
        "max_tokens": 64,
    }
    assert provider.name == "anthropic"
    assert provider.model_id == "claude-sonnet-5"


@pytest.mark.asyncio
async def test_anthropic_stream_fails_safely_for_malformed_tool_arguments() -> None:
    provider = AnthropicModel(
        client=FakeAnthropicClient(
            messages=FakeMessages(
                FakeAnthropicStream(anthropic_events(arguments=('["bad"]',)))
            )
        )
    )

    events = [event async for event in provider.stream(provider_request())]

    assert events[-1] == ModelFailed(
        "model_invalid_tool_arguments",
        "Anthropic returned invalid tool arguments.",
        False,
    )
    assert not any(isinstance(event, ToolCall) for event in events)


@pytest.mark.asyncio
async def test_anthropic_stream_hides_unclassified_provider_error() -> None:
    provider = AnthropicModel(
        client=FakeAnthropicClient(
            messages=FakeMessages(RuntimeError("response body with sk-ant-secret"))
        )
    )

    events = [event async for event in provider.stream(ModelRequest(messages=()))]

    assert events == [ModelFailed("model_provider_error", "Anthropic request failed.", False)]
    assert "sk-ant-secret" not in repr(events)
