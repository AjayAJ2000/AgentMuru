# Workflows and handoffs

Workflows coordinate deterministic steps. Handoffs transfer a session to another declared
agent. They solve different problems and can be used together.

## Workflows

A `Workflow` is an ordered tuple of named `Step` objects. Each handler receives the current
state and returns a `StepResult` with new state and an optional next-step name.

`WorkflowRunner` records a checkpoint after every completed step. A step may declare retries.
Duplicate step names, empty workflows, unknown next-step targets, and negative retry counts fail
before or during execution with explicit results.

Use a workflow when control flow should remain deterministic and model-independent.

## Handoffs

`Runtime.handoff()` creates a new run in the same session for an agent listed in
`Application.agents`. It emits `agent.handoff` with source agent, target agent, reason, and
target run ID.

The target sees the shared session conversation. It uses its own instructions, model, tools,
permissions, and settings.

Use a handoff when another agent definition owns the next decision, such as transferring
research to a writer or intake to a specialist.

## Choosing the boundary

| Need | Use |
| --- | --- |
| Fixed sequence of application steps | Workflow |
| Retry and checkpoint deterministic state | Workflow |
| Change instructions, model, tools, or permissions | Handoff |
| Preserve one session while changing agent ownership | Handoff |

See [workflows and handoffs](../cookbook/workflows-and-handoffs.md) for executable examples.
