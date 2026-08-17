# Run workflows and handoffs

Use a workflow for deterministic state transitions and a handoff when another agent definition
owns the next model turn.

## Run a workflow

The executable scenario is `examples.workflow_agent`.

```powershell
python examples/workflow_agent.py
```

```python
workflow = Workflow(
    name="research-report",
    steps=(
        Step("research", research, retries=1),
        Step("summarize", summarize),
    ),
)
result = await WorkflowRunner().run(
    workflow,
    initial_state={"query": "AgentMuru"},
)
```

The result contains terminal status, final state, ordered checkpoints, and an error code when a
step exhausts its retries.

## Hand off a session

The executable scenario is `examples.handoff_agent`.

```powershell
python examples/handoff_agent.py
```

Declare the target in `Application.agents`, complete the source run, and create the target run:

```python
target = await runtime.handoff(
    source.id,
    to_agent="writer",
    reason="Turn verified facts into release copy",
)
target = await runtime.wait(target.id)
```

The target agent uses the same session history. Its own provider, tools, permissions, and model
settings control the new run.
