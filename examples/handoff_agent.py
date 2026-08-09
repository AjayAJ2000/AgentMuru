from __future__ import annotations

import asyncio
import json

from agentmuru import Agent, Application, FakeModel, Runtime
from agentmuru.core.events import EventType


def build_application() -> Application:
    researcher = Agent(
        name="researcher",
        instructions="Collect the relevant facts.",
        model=FakeModel.responses("Research complete."),
    )
    writer = Agent(
        name="writer",
        instructions="Turn facts into a concise report.",
        model=FakeModel.responses("Report complete."),
    )
    return Application(
        agent=researcher,
        agents=(writer,),
        title="Handoff Agent",
    )


application = build_application()


async def main() -> dict[str, object]:
    runtime = Runtime(build_application())
    session = runtime.create_session(title="handoff qualification")
    source = await runtime.submit(session.id, "research AgentMuru")
    source = await runtime.wait(source.id)
    target = await runtime.handoff(
        source.id,
        to_agent="writer",
        reason="turn verified facts into release copy",
    )
    target = await runtime.wait(target.id)
    return {
        "source_agent": source.agent_name,
        "source_status": source.status.value,
        "target_agent": target.agent_name,
        "target_status": target.status.value,
        "handoffs": len(
            [event for event in session.events if event.type is EventType.AGENT_HANDOFF]
        ),
    }


if __name__ == "__main__":
    print(json.dumps(asyncio.run(main()), indent=2, sort_keys=True))

