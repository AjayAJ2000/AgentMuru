from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path

from agentmuru import Agent, Application, FakeModel, Runtime, SQLitePersistence


def create_application(database_path: Path) -> tuple[Application, SQLitePersistence]:
    persistence = SQLitePersistence(database_path)
    application = Application(
        agent=Agent(
            name="durable-assistant",
            instructions="Keep local history durable and inspectable.",
            model=FakeModel.responses("Durable response."),
        ),
        title="Durable Agent",
        session_store=persistence.sessions,
        artifact_store=persistence.artifacts,
    )
    return application, persistence


async def _run(database_path: Path) -> dict[str, object]:
    first_application, first_persistence = create_application(database_path)
    first = Runtime(
        first_application,
        approvals=first_persistence.approval_service(),
    )
    session = first.create_session(title="durable example")
    run = await first.submit(session.id, "persist this", idempotency_key="example-1")
    await first.wait(run.id)

    second_application, second_persistence = create_application(database_path)
    second = Runtime(
        second_application,
        approvals=second_persistence.approval_service(),
    )
    restored = second.sessions.get(session.id)
    restored_run = second.get_run(run.id)
    return {
        "sessions": len(second.sessions.list()),
        "runs": len(restored.runs),
        "messages": len(restored.messages),
        "events": len(restored.events),
        "status": restored_run.status.value,
    }


async def main(database_path: Path | None = None) -> dict[str, object]:
    if database_path is not None:
        return await _run(database_path)
    with tempfile.TemporaryDirectory(prefix="agentmuru-durable-") as directory:
        return await _run(Path(directory) / "agentmuru.db")


if __name__ == "__main__":
    print(json.dumps(asyncio.run(main()), indent=2, sort_keys=True))

