# Get started

The first AgentMuru run is deliberately local and deterministic. Start with `FakeModel` to
learn the runtime and Workspace, then switch the generated project to one official provider.

## Recommended path

1. [Install AgentMuru](getting-started/installation.md) and run the environment checks.
2. [Complete the quickstart](getting-started/quickstart.md) with a credential-free model.
3. [Tour the Workspace](getting-started/workspace-tour.md) and learn what each panel means.
4. [Use a real model](getting-started/real-model.md) from OpenAI, Anthropic, or Google.
5. [Govern a tool](cookbook/governed-tools.md) before connecting side effects.

## Choose another entry point

| Goal | Start here |
| --- | --- |
| Add AgentMuru to an existing Python project | [Installation](getting-started/installation.md#install-into-an-existing-project) |
| Create a durable local application | [SQLite persistence](operations/sqlite.md) |
| Implement a custom model adapter | [Provider contract](reference/providers.md) |
| Deploy the HTTP and WebSocket server | [Deployment](operations/deployment.md) |
| Explore the Go-native experiments | [Labs](labs/index.md) |

## What you will have

At the end of the recommended path you will have a Python module exporting one
`Application`, a browser Workspace at `http://127.0.0.1:8000`, and a model provider that can
stream text and tool calls into the same runtime contract.
