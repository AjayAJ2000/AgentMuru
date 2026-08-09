from __future__ import annotations

import asyncio
import json

from agentmuru import Agent, Application, ArtifactKind, FakeModel, Runtime


def build_application() -> Application:
    return Application(
        agent=Agent(
            name="artifact-author",
            instructions="Create small, inspectable outputs.",
            model=FakeModel.responses("Artifact set prepared."),
        ),
        title="Artifact Agent",
    )


application = build_application()


async def main() -> dict[str, object]:
    runtime = Runtime(build_application())
    session = runtime.create_session(title="artifact qualification")
    run = await runtime.submit(session.id, "prepare the artifact set")
    completed = await runtime.wait(run.id)
    values = (
        (ArtifactKind.MARKDOWN, "summary.md", "# Summary", "text/markdown"),
        (ArtifactKind.JSON, "result.json", {"qualified": True}, "application/json"),
        (ArtifactKind.TABLE, "rows.json", [{"id": 1}], "application/json"),
        (ArtifactKind.CODE, "agent.py", "print('muru')", "text/x-python"),
        (ArtifactKind.FILE, "evidence.txt", b"qualified", "text/plain"),
    )
    for kind, name, content, mime_type in values:
        runtime.create_artifact(
            session_id=session.id,
            run_id=run.id,
            kind=kind,
            name=name,
            content=content,
            mime_type=mime_type,
            creator="artifact-author",
        )
    artifacts = runtime.artifacts.list(session_id=session.id)
    return {
        "run_status": completed.status.value,
        "artifact_count": len(artifacts),
        "artifact_kinds": sorted(item.kind.value for item in artifacts),
    }


if __name__ == "__main__":
    print(json.dumps(asyncio.run(main()), indent=2, sort_keys=True))

