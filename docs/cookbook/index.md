# Recipes

These recipes are short, executable paths through one AgentMuru capability. Every page links to
the source file used by the test suite.

| Build | Outcome | Example |
| --- | --- | --- |
| [Govern a tool](governed-tools.md) | Permission, approval, rejection, expiry, and redaction | `examples.governed_tool_agent` |
| [Persist a session](durable-sessions.md) | Reopen messages, runs, and events from SQLite | `examples.durable_agent` |
| [Create artifacts](artifacts.md) | Store typed outputs against a run | `examples.artifact_agent` |
| [Coordinate work](workflows-and-handoffs.md) | Run checkpoints and transfer between agents | `examples.workflow_agent` and `examples.handoff_agent` |

Run examples from the repository root after an editable development install:

```powershell
python -m pip install -e ".[dev,providers]"
```
