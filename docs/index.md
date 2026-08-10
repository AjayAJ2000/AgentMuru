<section class="muru-hero">
  <span class="muru-kicker">Python-native agent runtime · 0.2</span>
  <h1>Build agents you can see, steer, and trust.</h1>
  <p>AgentMuru gives engineers an observable runtime, governed tools, durable local history,
  and a replayable Workspace—without moving application logic into the browser.</p>
  <div class="muru-actions">
    <a class="md-button md-button--primary" href="getting-started/quickstart/">Start locally</a>
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

## Choose your goal

| Goal | Start here |
| --- | --- |
| Evaluate AgentMuru without provider credentials | [Five-minute local quickstart](getting-started/quickstart.md) |
| Add governed tool execution | [Govern tool execution](cookbook/governed-tools.md) |
| Reopen sessions after restart | [Persist sessions with SQLite](guides/sqlite-persistence.md) |
| Operate the server and browser Workspace | [Run the server and Workspace](guides/server-and-workspace.md) |
| Look up a stable import | [Stable public API](reference/public-api.md) |
| Check verified behavior and limitations | [Current capabilities and limits](integration-status.md) |

## How the docs are organized

- **Start** helps you choose a path, install the verified release, and run a local agent.
- **Tutorials** teach complete outcomes with the same runnable examples used in qualification.
- **How-to guides** answer focused implementation and operations questions.
- **Concepts** explain the runtime mental model behind agents, events, tools, sessions,
  artifacts, and workflows.
- **Reference** defines stable imports, current capabilities, release notes, migrations, and
  the product roadmap.

[Choose a starting path](getting-started.md){ .md-button .md-button--primary }
