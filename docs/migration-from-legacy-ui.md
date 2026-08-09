# Migration from BrickflowUI

AgentMuru is a clean break. There is no compatibility package, import alias, CLI alias, or
VDOM protocol bridge.

| Former API | Decision | AgentMuru replacement |
| --- | --- | --- |
| `App` pages and mounts | Replaced | `Application` plus `Runtime` |
| `Text`, `Card`, `Row`, `Column` | Removed from public Python API | Muru Workspace projections |
| `Button` callbacks | Replaced | typed runtime actions and approval decisions |
| `ChatMessage`, `ChatInput` | Removed | session messages and workspace conversation |
| chart components | Replaced | typed artifacts and artifact renderers |
| hooks and render context | Removed | explicit sessions, messages, runs, and events |
| VDOM full/patch messages | Removed | protocol version 1 runtime events |
| page routing | Removed | sessions and application metadata endpoints |
| Databricks helpers | Moved | `agentmuru.integrations.databricks` |
| old CLI | Removed | `muru init`, `dev`, `run`, `doctor`, `version` |

Rewrite an application around an `Agent`, typed `@tool` functions, and `Application`.
Move display outputs into artifacts and dangerous callbacks into governed tools. For local
durability, compose `SQLitePersistence` and pass its approval service to Runtime. Custom
stores must implement the explicit 0.2 mutation contract; see
[Migrate custom stores to 0.2](migration-custom-stores-0.2.md).
