import pytest

from agentmuru.models import (
    FakeModel,
    ModelCapabilities,
    ModelCompleted,
    ModelRequest,
    TextDelta,
    ToolCall,
    Usage,
)


@pytest.mark.asyncio
async def test_fake_model_streams_scripted_events_deterministically() -> None:
    model = FakeModel.script(
        [
            TextDelta("hello "),
            ToolCall(id="call-1", name="lookup", arguments={"id": "42"}),
            ModelCompleted(usage=Usage(input_tokens=3, output_tokens=2)),
        ]
    )

    events = [event async for event in model.stream(ModelRequest(messages=()))]

    assert events[0] == TextDelta("hello ")
    assert events[1].arguments == {"id": "42"}
    assert events[2].usage.total_tokens == 5
    assert model.capabilities == ModelCapabilities(text=True, streaming=True, tool_calling=True)


@pytest.mark.asyncio
async def test_fake_model_responses_produces_text_and_completion_per_request() -> None:
    model = FakeModel.responses("first", "second")

    first = [event async for event in model.stream(ModelRequest(messages=()))]
    second = [event async for event in model.stream(ModelRequest(messages=()))]

    assert first == [TextDelta("first"), ModelCompleted()]
    assert second == [TextDelta("second"), ModelCompleted()]


def test_model_request_requires_provider_capability() -> None:
    capabilities = ModelCapabilities(text=True, streaming=False)

    with pytest.raises(ValueError, match="streaming"):
        capabilities.require("streaming")
