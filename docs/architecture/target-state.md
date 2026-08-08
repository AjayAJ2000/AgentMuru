# AgentMuru architecture

```text
Muru Workspace / CLI / integrations / FastAPI
                       |
                 Application
                       |
            Runtime / workflows / agents
                       |
       events / sessions / tools / protocols
```

Dependencies point inward. Core packages have no browser, server, Databricks, or vendor
model dependency. Runtime state changes are typed events. Session and artifact persistence,
model providers, retrieval, MCP, and exporters are replaceable protocols. The workspace
consumes protocol version 1 and can be rebuilt without changing agent execution.
