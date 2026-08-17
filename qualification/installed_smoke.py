from __future__ import annotations

import asyncio
import importlib.util
import json
from pathlib import Path

import agentmuru
from agentmuru import (
    Agent,
    Application,
    ArtifactKind,
    FakeModel,
    Runtime,
    SQLitePersistence,
    tool,
)
from agentmuru.approvals import ApprovalDecision
from agentmuru.integrations.anthropic import AnthropicModel
from agentmuru.integrations.google import GoogleGenAIModel
from agentmuru.integrations.openai import OpenAIModel
from agentmuru.models import ModelCompleted, TextDelta, ToolCall
from agentmuru.workflows import Step, StepResult, Workflow, WorkflowRunner


async def qualify() -> dict[str, object]:
    database = Path.cwd() / "installed-agentmuru.db"
    persistence = SQLitePersistence(database)
    application = Application(
        agent=Agent(
            name="installed-assistant",
            instructions="Qualify the installed wheel.",
            model=FakeModel.responses("Installed runtime completed."),
        ),
        session_store=persistence.sessions,
        artifact_store=persistence.artifacts,
    )
    runtime = Runtime(application, approvals=persistence.approval_service())
    session = runtime.create_session(title="installed qualification")
    run = await runtime.submit(session.id, "run from the wheel", idempotency_key="wheel-1")
    run = await runtime.wait(run.id)
    artifact = runtime.create_artifact(
        session_id=session.id,
        run_id=run.id,
        kind=ArtifactKind.REPORT,
        name="installed.md",
        content="# Installed",
        mime_type="text/markdown",
        creator="installed-assistant",
    )

    reopened_persistence = SQLitePersistence(database)
    reopened_application = Application(
        agent=Agent(
            name="installed-assistant",
            instructions="",
            model=FakeModel.responses("unused"),
        ),
        session_store=reopened_persistence.sessions,
        artifact_store=reopened_persistence.artifacts,
    )
    reopened = Runtime(
        reopened_application,
        approvals=reopened_persistence.approval_service(),
    )

    mutations = 0

    @tool(permission="records.write", approval="required", risk="high", side_effects=True)
    def mutate() -> str:
        nonlocal mutations
        mutations += 1
        return "changed"

    governed = Runtime(
        Application(
            agent=Agent(
                name="governed",
                instructions="",
                model=FakeModel.turns(
                    [ToolCall(id="call-1", name="mutate", arguments={}), ModelCompleted()],
                    [TextDelta("Approved."), ModelCompleted()],
                ),
                tools=(mutate,),
                permissions=frozenset({"records.write"}),
            ),
            session_store=reopened_persistence.sessions,
            artifact_store=reopened_persistence.artifacts,
        ),
        approvals=reopened_persistence.approval_service(),
    )
    governed_session = governed.create_session(title="governed installed run")
    governed_run = await governed.submit(governed_session.id, "mutate")
    request = await governed.wait_for_approval(governed_run.id)
    await governed.decide_approval(
        request.id,
        ApprovalDecision.APPROVE,
        actor="qualification",
    )
    governed_run = await governed.wait(governed_run.id)

    researcher = Agent(name="researcher", instructions="", model=FakeModel.responses("facts"))
    writer = Agent(name="writer", instructions="", model=FakeModel.responses("report"))
    handoff_runtime = Runtime(Application(agent=researcher, agents=(writer,)))
    handoff_session = handoff_runtime.create_session()
    source = await handoff_runtime.submit(handoff_session.id, "research")
    await handoff_runtime.wait(source.id)
    target = await handoff_runtime.handoff(source.id, to_agent="writer", reason="write")
    target = await handoff_runtime.wait(target.id)

    workflow = await WorkflowRunner().run(
        Workflow(
            name="installed-workflow",
            steps=(Step("verify", lambda state: StepResult({**state, "verified": True})),),
        ),
        initial_state={},
    )

    package_origin = Path(agentmuru.__file__).resolve()
    providers = (
        OpenAIModel(api_key="qualification"),
        AnthropicModel(api_key="qualification"),
        GoogleGenAIModel(api_key="qualification"),
    )
    return {
        "version": agentmuru.__version__,
        "package_origin": str(package_origin),
        "origin_inside_environment": "site-packages" in package_origin.parts,
        "runtime_status": run.status.value,
        "restored_messages": len(reopened.sessions.get(session.id).messages),
        "restored_artifact": reopened.artifacts.get(artifact.id).name,
        "approval_status": governed_run.status.value,
        "mutations": mutations,
        "handoff_status": target.status.value,
        "workflow_status": workflow.status.value,
        "databricks_sdk": importlib.util.find_spec("databricks.sdk") is not None,
        "databricks_sql": importlib.util.find_spec("databricks.sql") is not None,
        "provider_adapters": [provider.name for provider in providers],
        "provider_sdks": {
            "openai": importlib.util.find_spec("openai") is not None,
            "anthropic": importlib.util.find_spec("anthropic") is not None,
            "google_genai": importlib.util.find_spec("google.genai") is not None,
        },
    }


if __name__ == "__main__":
    print(json.dumps(asyncio.run(qualify()), sort_keys=True))
