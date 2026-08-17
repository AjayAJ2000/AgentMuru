# Core concepts

AgentMuru separates application intent from provider and transport details. The same agent can
run with a deterministic fake, an official hosted-model adapter, in-memory state, SQLite, the
Python API, or the browser Workspace.

## Application model

An `Application` names one primary `Agent`, optional handoff targets, session and artifact
stores, and user-facing metadata. The `Runtime` executes that definition and owns policy,
approvals, tracing, cancellation, and event production.

```text
Application
  Agent
    ModelProvider
    Tool[]
    permissions
  SessionStore
  ArtifactStore

Runtime
  PermissionPolicy
  ApprovalService
  Tracer
```

## Read by concern

| Concern | Concept |
| --- | --- |
| Define behavior and choose a model | [Agents and models](agents-and-models.md) |
| Connect typed Python functions safely | [Tools and approvals](tools-and-approvals.md) |
| Understand execution order and replay | [Runtime and events](runtime-and-events.md) |
| Keep conversations and runs | [Sessions and memory](sessions-and-memory.md) |
| Store outputs and inspect execution | [Artifacts and traces](artifacts-and-traces.md) |
| Coordinate multi-step behavior | [Workflows and handoffs](workflows-and-handoffs.md) |

## Design rule

Provider output is untrusted input. A model can request a registered tool, but it cannot grant
permissions, approve itself, bypass argument validation, or write directly to a store. The
runtime remains the authority for every side effect.
