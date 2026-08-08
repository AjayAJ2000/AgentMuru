import pytest

from agentmuru import Agent, Application, FakeModel, Runtime
from agentmuru.core.events import EventType
from agentmuru.sessions import RunStatus


@pytest.mark.asyncio
async def test_runtime_handoff_starts_an_explicit_target_agent_run() -> None:
    researcher = Agent(name="researcher", instructions="", model=FakeModel.responses("facts"))
    writer = Agent(name="writer", instructions="", model=FakeModel.responses("report"))
    runtime = Runtime(Application(agent=researcher, agents=(writer,)))
    session = runtime.create_session()
    first = await runtime.submit(session.id, "investigate")
    await runtime.wait(first.id)

    second = await runtime.handoff(first.id, to_agent="writer", reason="write the report")
    completed = await runtime.wait(second.id)

    assert completed.agent_name == "writer"
    assert completed.status is RunStatus.COMPLETED
    handoff = next(event for event in session.events if event.type is EventType.AGENT_HANDOFF)
    assert handoff.payload == {
        "from_agent": "researcher",
        "to_agent": "writer",
        "reason": "write the report",
        "target_run_id": second.id,
    }
