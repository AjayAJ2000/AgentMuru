import asyncio

import pytest

from agentmuru import Agent, Application, Runtime, tool
from agentmuru.approvals import ApprovalDecision, ApprovalStatus
from agentmuru.models import FakeModel, ModelCompleted, TextDelta, ToolCall
from agentmuru.sessions import RunStatus


@pytest.mark.asyncio
async def test_risky_tool_pauses_and_resumes_after_approval() -> None:
    executed = asyncio.Event()

    @tool(permission="database.write", approval="required", risk="high")
    async def drop_table(name: str) -> str:
        executed.set()
        return f"dropped {name}"

    model = FakeModel.turns(
        [ToolCall(id="call-1", name="drop_table", arguments={"name": "customers"}), ModelCompleted()],
        [TextDelta("Done"), ModelCompleted()],
    )
    runtime = Runtime(
        Application(
            agent=Agent(
                name="ops",
                instructions="",
                model=model,
                tools=(drop_table,),
                permissions=frozenset({"database.write"}),
            )
        )
    )
    session = runtime.create_session()
    run = await runtime.submit(session.id, "clean up")

    approval = await runtime.wait_for_approval(run.id)
    assert approval.status is ApprovalStatus.PENDING
    assert run.status is RunStatus.WAITING_APPROVAL
    assert not executed.is_set()

    decided = await runtime.decide_approval(
        approval.id,
        ApprovalDecision.APPROVE,
        actor="tester",
        reason="reviewed",
    )
    assert decided.status is ApprovalStatus.APPROVED
    assert (await runtime.wait(run.id)).status is RunStatus.COMPLETED
    assert executed.is_set()


@pytest.mark.asyncio
async def test_approval_expires_and_fails_run_without_executing_tool() -> None:
    executed = asyncio.Event()

    @tool(permission="database.write", approval="required", risk="high")
    async def mutate() -> str:
        executed.set()
        return "changed"

    runtime = Runtime(
        Application(
            agent=Agent(
                name="ops",
                instructions="",
                model=FakeModel.turns(
                    [ToolCall(id="call-expiring", name="mutate", arguments={}), ModelCompleted()]
                ),
                tools=(mutate,),
                permissions=frozenset({"database.write"}),
            )
        ),
        approval_timeout=0.01,
    )
    session = runtime.create_session()
    run = await runtime.submit(session.id, "change it")
    approval = await runtime.wait_for_approval(run.id)

    completed = await runtime.wait(run.id)

    assert runtime.approvals.get(approval.id).status is ApprovalStatus.EXPIRED
    assert completed.status is RunStatus.FAILED
    assert completed.error_code == "approval_expired"
    assert not executed.is_set()
    assert any(event.type.value == "approval.expired" for event in session.events)
