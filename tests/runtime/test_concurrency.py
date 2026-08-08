import pytest

from agentmuru import Agent, Application, FakeModel, Runtime
from agentmuru.sessions import MessageRole


@pytest.mark.asyncio
async def test_concurrent_sessions_keep_messages_and_sequences_isolated() -> None:
    runtime = Runtime(
        Application(
            agent=Agent(
                name="assistant",
                instructions="",
                model=FakeModel.responses("first response", "second response"),
            )
        )
    )
    first = runtime.create_session()
    second = runtime.create_session()

    first_run = await runtime.submit(first.id, "first question")
    second_run = await runtime.submit(second.id, "second question")
    await runtime.wait(first_run.id)
    await runtime.wait(second_run.id)

    assert [message.content for message in first.messages if message.role is MessageRole.USER] == [
        "first question"
    ]
    assert [message.content for message in second.messages if message.role is MessageRole.USER] == [
        "second question"
    ]
    assert first.events[0].sequence == second.events[0].sequence == 1
