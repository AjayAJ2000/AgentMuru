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

## Adaptive edge path

The native `edge/` module now supplies the first target-state layer: versioned cross-runtime
contracts, read-only hardware classification, durable append-before-publish events, and a
responsive event-driven terminal workspace. It is deliberately separated from model
selection, agent compilation, and tool effects so each higher-risk capability can be gated
with its own evidence.

```text
install / launch
      |
hardware profile -> verified runtime + model catalog
      |                         |
      +--------> agent-pack compiler
                           |
                  event-sourced orchestrator
                           |
              policy broker -> isolated effects
```

Windows x64 with 8 GB RAM is the first release authority. Android remains a later target
after the same contracts, model provenance, orchestration limits, and effect policies pass
on the Windows reference tier.
