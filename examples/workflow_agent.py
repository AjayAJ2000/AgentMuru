import asyncio
import json

from agentmuru.workflows import Step, StepResult, Workflow, WorkflowRunner


def research(state: dict[str, object]) -> StepResult:
    return StepResult(state={**state, "facts": ["events are replayable", "tools are governed"]})


def summarize(state: dict[str, object]) -> StepResult:
    facts = state["facts"]
    if not isinstance(facts, list):
        raise TypeError("workflow facts must be a list")
    return StepResult(state={**state, "summary": f"AgentMuru verified {len(facts)} facts."})


async def main() -> dict[str, object]:
    workflow = Workflow(
        name="research-report",
        steps=(Step("research", research), Step("summarize", summarize)),
    )
    result = await WorkflowRunner().run(workflow, initial_state={"query": "AgentMuru"})
    return {
        "status": result.status.value,
        "summary": result.state["summary"],
        "checkpoints": [checkpoint.step_name for checkpoint in result.checkpoints],
    }


if __name__ == "__main__":
    print(json.dumps(asyncio.run(main()), indent=2, sort_keys=True))
