import asyncio

from agentmuru.workflows import Step, StepResult, Workflow, WorkflowRunner


def research(state: dict[str, object]) -> StepResult:
    return StepResult(state={**state, "facts": ["events are replayable", "tools are governed"]})


def summarize(state: dict[str, object]) -> StepResult:
    facts = state["facts"]
    if not isinstance(facts, list):
        raise TypeError("workflow facts must be a list")
    return StepResult(state={**state, "summary": f"AgentMuru verified {len(facts)} facts."})


async def main() -> None:
    workflow = Workflow(
        name="research-report",
        steps=(Step("research", research), Step("summarize", summarize)),
    )
    result = await WorkflowRunner().run(workflow, initial_state={"query": "AgentMuru"})
    print(result.state["summary"])


if __name__ == "__main__":
    asyncio.run(main())
