# AgentMuru

AgentMuru is a Python-native runtime and workspace for observable, human-governed AI
applications. Define agents and typed tools in Python. The runtime coordinates model
streams, tool calls, approvals, sessions, artifacts, workflows, usage, and traces. Muru
Workspace renders that state without owning application logic.

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

[Get started](getting-started.md){ .md-button .md-button--primary }
