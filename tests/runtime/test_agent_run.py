import pytest

from agentmuru import Agent, Application, FakeModel, Runtime
from agentmuru.core.events import EventType
from agentmuru.sessions import MessageRole, RunStatus


@pytest.mark.asyncio
async def test_runtime_streams_and_persists_a_complete_agent_run() -> None:
    runtime = Runtime(
        Application(
            agent=Agent(
                name="assistant",
                instructions="Be helpful",
                model=FakeModel.responses("Hello from Muru"),
            )
        )
    )
    session = runtime.create_session()

    run = await runtime.submit(session.id, "hello")
    completed = await runtime.wait(run.id)

    assert completed.status is RunStatus.COMPLETED
    assert [(message.role, message.content) for message in session.messages] == [
        (MessageRole.USER, "hello"),
        (MessageRole.ASSISTANT, "Hello from Muru"),
    ]
    event_types = [event.type for event in session.events]
    assert event_types[0] is EventType.SESSION_STARTED
    assert EventType.MODEL_TOKEN_DELTA in event_types
    assert event_types[-1] is EventType.RUN_COMPLETED
    assert runtime.tracer.traces_for_run(run.id)[0].status == "completed"


@pytest.mark.asyncio
async def test_submit_is_idempotent_for_a_session_key() -> None:
    runtime = Runtime(
        Application(agent=Agent(name="assistant", instructions="", model=FakeModel.responses("ok")))
    )
    session = runtime.create_session()

    first = await runtime.submit(session.id, "hello", idempotency_key="request-1")
    second = await runtime.submit(session.id, "hello", idempotency_key="request-1")

    assert first.id == second.id
    await runtime.wait(first.id)
    assert len([message for message in session.messages if message.role is MessageRole.USER]) == 1
