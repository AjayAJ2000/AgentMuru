import pytest

from agentmuru import Agent, Application, Runtime, tool
from agentmuru.core.events import EventType
from agentmuru.models import FakeModel, ModelCompleted, TextDelta, ToolCall
from agentmuru.sessions import MessageRole, RunStatus


@pytest.mark.asyncio
async def test_runtime_executes_a_tool_and_continues_the_model_loop() -> None:
    calls: list[str] = []

    @tool(permission="customer.read")
    def lookup(customer_id: str) -> dict[str, str]:
        calls.append(customer_id)
        return {"status": "active"}

    model = FakeModel.turns(
        [ToolCall(id="call-1", name="lookup", arguments={"customer_id": "c-1"}), ModelCompleted()],
        [TextDelta("Customer is active"), ModelCompleted()],
    )
    runtime = Runtime(
        Application(
            agent=Agent(
                name="analyst",
                instructions="Use tools",
                model=model,
                tools=(lookup,),
                permissions=frozenset({"customer.read"}),
            )
        )
    )
    session = runtime.create_session()

    run = await runtime.submit(session.id, "check customer")
    completed = await runtime.wait(run.id)

    assert completed.status is RunStatus.COMPLETED
    assert calls == ["c-1"]
    assert any(message.role is MessageRole.TOOL and "active" in message.content for message in session.messages)
    assert len(model.requests) == 2
    assert EventType.TOOL_CALL_COMPLETED in [event.type for event in session.events]


@pytest.mark.asyncio
async def test_runtime_denies_a_tool_without_declared_agent_permission() -> None:
    @tool(permission="database.write")
    def mutate(value: str) -> str:
        raise AssertionError("denied tool executed")

    model = FakeModel.script(
        [ToolCall(id="call-1", name="mutate", arguments={"value": "x"}), ModelCompleted()]
    )
    runtime = Runtime(
        Application(agent=Agent(name="restricted", instructions="", model=model, tools=(mutate,)))
    )
    session = runtime.create_session()

    completed = await runtime.wait((await runtime.submit(session.id, "change it")).id)

    assert completed.status is RunStatus.FAILED
    failure = next(event for event in session.events if event.type is EventType.TOOL_CALL_FAILED)
    assert failure.payload["code"] == "permission_denied"


@pytest.mark.asyncio
async def test_runtime_does_not_expose_tool_exception_details_in_public_events() -> None:
    @tool
    def explode() -> str:
        raise RuntimeError("provider secret: sk-private")

    runtime = Runtime(
        Application(
            agent=Agent(
                name="safe",
                instructions="",
                model=FakeModel.script(
                    [ToolCall(id="call-1", name="explode", arguments={}), ModelCompleted()]
                ),
                tools=(explode,),
            )
        )
    )
    session = runtime.create_session()

    await runtime.wait((await runtime.submit(session.id, "run it")).id)

    serialized = " ".join(str(event.to_dict()) for event in session.events)
    assert "sk-private" not in serialized
    assert "Tool execution failed" in serialized
