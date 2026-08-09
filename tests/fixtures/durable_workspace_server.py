from __future__ import annotations

import argparse
from pathlib import Path

import uvicorn

from agentmuru import Agent, Application, FakeModel, Runtime, SQLitePersistence
from agentmuru.server import create_asgi_app


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()

    persistence = SQLitePersistence(args.database)
    application = Application(
        agent=Agent(
            name="durable-assistant",
            instructions="Respond deterministically for browser qualification.",
            model=FakeModel.responses("Durable AgentMuru history restored."),
        ),
        title="Durable AgentMuru",
        session_store=persistence.sessions,
        artifact_store=persistence.artifacts,
    )
    runtime = Runtime(application, approvals=persistence.approval_service())
    uvicorn.run(
        create_asgi_app(application, runtime=runtime),
        host="127.0.0.1",
        port=args.port,
        log_level="warning",
    )


if __name__ == "__main__":
    main()

