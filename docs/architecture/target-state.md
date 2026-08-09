# AgentMuru architecture

```text
Muru Workspace / CLI / integrations / FastAPI
                       |
                 Application
                       |
            Runtime / workflows / agents
                       |
       events / store protocols / tools / approvals
                       |
         SQLite adapters / future PostgreSQL
```

Dependencies point inward. Core packages have no browser, server, Databricks, or vendor
model dependency. Runtime state changes are typed events and explicit store operations.
SQLite is the implemented durable local adapter; production model providers and PostgreSQL
are planned adapters. Retrieval, MCP, and exporters remain provider-neutral seams. The
Workspace consumes protocol version 1 and can be rebuilt without changing execution.
