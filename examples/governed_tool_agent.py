from __future__ import annotations

import asyncio
import json
from collections.abc import Callable

from agentmuru import Agent, Application, FakeModel, Runtime, tool
from agentmuru.approvals import ApprovalDecision
from agentmuru.models import ModelCompleted, TextDelta, ToolCall


def _tool_model(tool_name: str) -> FakeModel:
    return FakeModel.turns(
        [ToolCall(id=f"{tool_name}-1", name=tool_name, arguments={}), ModelCompleted()],
        [TextDelta("Policy outcome recorded."), ModelCompleted()],
    )


def build_application() -> Application:
    @tool(permission="records.read", description="Read a deterministic record")
    def read_record() -> dict[str, str]:
        return {"status": "ready"}

    return Application(
        agent=Agent(
            name="policy-demo",
            instructions="Demonstrate governed tool execution.",
            model=_tool_model("read_record"),
            tools=(read_record,),
            permissions=frozenset({"records.read"}),
        ),
        title="Governed Tool Agent",
    )


application = build_application()


async def _run_basic(*, granted: bool) -> str:
    @tool(permission="records.read")
    def read_record() -> dict[str, str]:
        return {"status": "ready"}

    runtime = Runtime(
        Application(
            agent=Agent(
                name="policy-demo",
                instructions="",
                model=_tool_model("read_record"),
                tools=(read_record,),
                permissions=frozenset({"records.read"}) if granted else frozenset(),
            )
        )
    )
    session = runtime.create_session()
    run = await runtime.submit(session.id, "read the record")
    completed = await runtime.wait(run.id)
    return completed.status.value if completed.error_code is None else completed.error_code


async def _run_approval(
    outcome: str,
    on_mutation: Callable[[], None],
) -> str:
    @tool(permission="records.write", approval="required", risk="high", side_effects=True)
    def mutate_record() -> dict[str, str]:
        on_mutation()
        return {"status": "changed"}

    runtime = Runtime(
        Application(
            agent=Agent(
                name="policy-demo",
                instructions="",
                model=_tool_model("mutate_record"),
                tools=(mutate_record,),
                permissions=frozenset({"records.write"}),
            )
        ),
        approval_timeout=0.01 if outcome == "expiry" else 2,
    )
    session = runtime.create_session()
    run = await runtime.submit(session.id, "change the record")
    if outcome in {"approve", "reject"}:
        request = await runtime.wait_for_approval(run.id)
        await runtime.decide_approval(
            request.id,
            ApprovalDecision.APPROVE if outcome == "approve" else ApprovalDecision.REJECT,
            actor="example-reviewer",
            reason="deterministic qualification decision",
        )
    completed = await runtime.wait(run.id)
    return completed.status.value if completed.error_code is None else completed.error_code


async def main() -> dict[str, str | int]:
    mutations = 0

    def record_mutation() -> None:
        nonlocal mutations
        mutations += 1

    return {
        "allow": await _run_basic(granted=True),
        "deny": await _run_basic(granted=False),
        "approve": await _run_approval("approve", record_mutation),
        "reject": await _run_approval("reject", record_mutation),
        "expiry": await _run_approval("expiry", record_mutation),
        "mutations": mutations,
    }


if __name__ == "__main__":
    print(json.dumps(asyncio.run(main()), indent=2, sort_keys=True))

