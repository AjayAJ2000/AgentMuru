<section class="muru-hero">
  <span class="muru-kicker">Python-native agent runtime · 0.2</span>
  <h1>Build agents you can see, steer, and trust.</h1>
  <p>AgentMuru gives engineers an observable runtime, governed tools, durable local history,
  and a replayable Workspace—without moving application logic into the browser.</p>
  <div class="muru-actions">
    <a class="md-button md-button--primary" href="getting-started/">Install AgentMuru</a>
    <a class="md-button" href="guides/sqlite-persistence/">Operate durable sessions</a>
  </div>
</section>

# AgentMuru

Define agents and typed tools in Python. The Runtime coordinates model streams, tool calls,
approvals, sessions, artifacts, workflows, usage, and traces. Muru Workspace projects the
same ordered event history for operators.

```python
from agentmuru import Agent, Application, FakeModel

application = Application(
    agent=Agent(
        name="assistant",
        instructions="Help the user.",
        model=FakeModel.responses("AgentMuru is ready."),
    )
)
```

<div class="muru-feature-grid">
  <article><h3>See</h3><p>Inspect ordered events, model deltas, tools, usage, artifacts, and traces.</p></article>
  <article><h3>Steer</h3><p>Pause risky actions for an explicit approval, rejection, or expiry.</p></article>
  <article><h3>Trust</h3><p>Reopen SQLite-backed sessions with honest interrupted-process semantics.</p></article>
</div>

[Start with the verified quickstart](getting-started.md){ .md-button .md-button--primary }
