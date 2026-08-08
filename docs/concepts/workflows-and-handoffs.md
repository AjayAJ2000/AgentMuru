# Workflows and handoffs

AgentMuru workflows are small deterministic graphs of named steps. A step receives typed
state, returns `StepResult`, can retry, can select an explicit next step, and creates a
checkpoint. The workflow runner emits lifecycle events when connected to a session store.

`Runtime.handoff(...)` starts a new run for a registered target agent and emits a typed
handoff event linking source and target runs. Distributed workers, schedules, and parallel
orchestration are intentionally outside the first runtime.
