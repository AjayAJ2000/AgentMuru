import asyncio

import pytest

from agentmuru import Agent, Application, Runtime, tool
from agentmuru.models import FakeModel, ModelCompleted, ToolCall
from agentmuru.sessions import RunStatus


@pytest.mark.asyncio
async def test_runtime_cancels_an_inflight_tool_run() -> None:
    started = asyncio.Event()

    @tool
    async def wait_forever() -> str:
        started.set()
        await asyncio.Event().wait()
        return "unreachable"

    runtime = Runtime(
        Application(
            agent=Agent(
                name="worker",
                instructions="",
                model=FakeModel.script(
                    [ToolCall(id="call-1", name="wait_forever", arguments={}), ModelCompleted()]
                ),
                tools=(wait_forever,),
            )
        )
    )
    session = runtime.create_session()
    run = await runtime.submit(session.id, "wait")
    await asyncio.wait_for(started.wait(), timeout=0.5)

    await runtime.cancel(run.id)

    assert (await runtime.wait(run.id)).status is RunStatus.CANCELLED
