# Choose a starting path

AgentMuru can be evaluated locally without provider credentials. Choose the shortest path
that matches what you need to accomplish.

## Before you begin

You need Python 3.10 or later and a terminal. Git is required only if you plan to
contribute or run examples directly from the source repository.

## Choose your path

| Goal | Start here |
| --- | --- |
| Install the verified 0.2 release | [Install AgentMuru](getting-started/installation.md) |
| Build and run a local agent | [Five-minute local quickstart](getting-started/quickstart.md) |
| Learn with complete runnable examples | [Choose a tutorial](cookbook/index.md) |
| Add restart-safe local history | [Persist sessions with SQLite](guides/sqlite-persistence.md) |
| Operate the server and browser Workspace | [Run the server and Workspace](guides/server-and-workspace.md) |
| Check supported integrations and limits | [Current capabilities and limits](integration-status.md) |
| Look up a stable import | [Stable public API](reference/public-api.md) |

## Understand the 0.2 boundary

AgentMuru 0.2 includes the Python runtime, governed tools and approvals, replayable session
events, artifacts, workflows, the browser Workspace, and SQLite persistence for one local
runtime process with modest write concurrency. Production model providers and PostgreSQL
persistence remain planned. Review [current capabilities and limits](integration-status.md)
before choosing a deployment shape.
