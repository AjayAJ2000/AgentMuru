import pytest

from agentmuru.core.events import EventType
from agentmuru.sessions import InMemorySessionStore
from agentmuru.workflows import Step, StepResult, Workflow, WorkflowRunner, WorkflowStatus


@pytest.mark.asyncio
async def test_workflow_runs_ordered_steps_and_emits_checkpoints() -> None:
    store = InMemorySessionStore()
    session = store.create()

    async def collect(state: dict[str, object]) -> StepResult:
        return StepResult(state={**state, "facts": ["a", "b"]})

    def summarize(state: dict[str, object]) -> StepResult:
        return StepResult(state={**state, "summary": "2 facts"})

    workflow = Workflow(
        name="research",
        steps=(Step("collect", collect), Step("summarize", summarize)),
    )

    result = await WorkflowRunner(store).run(
        workflow,
        initial_state={"query": "muru"},
        session_id=session.id,
        run_id="run-1",
    )

    assert result.status is WorkflowStatus.COMPLETED
    assert result.state["summary"] == "2 facts"
    assert [checkpoint.step_name for checkpoint in result.checkpoints] == ["collect", "summarize"]
    assert EventType.WORKFLOW_COMPLETED in [event.type for event in session.events]


@pytest.mark.asyncio
async def test_workflow_supports_conditional_next_step() -> None:
    def route(state: dict[str, object]) -> StepResult:
        return StepResult(state=state, next_step="finish")

    def skipped(state: dict[str, object]) -> StepResult:
        raise AssertionError("conditional route did not skip this step")

    def finish(state: dict[str, object]) -> StepResult:
        return StepResult(state={**state, "done": True})

    workflow = Workflow(
        name="conditional",
        steps=(Step("route", route), Step("skipped", skipped), Step("finish", finish)),
    )

    result = await WorkflowRunner().run(workflow, initial_state={})

    assert result.state == {"done": True}


@pytest.mark.asyncio
async def test_workflow_retries_then_reports_failure() -> None:
    attempts = 0

    def unstable(state: dict[str, object]) -> StepResult:
        nonlocal attempts
        attempts += 1
        raise RuntimeError("nope")

    result = await WorkflowRunner().run(
        Workflow(name="failing", steps=(Step("unstable", unstable, retries=2),)),
        initial_state={},
    )

    assert attempts == 3
    assert result.status is WorkflowStatus.FAILED
    assert result.error_code == "workflow_step_failed"
