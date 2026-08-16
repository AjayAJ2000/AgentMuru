# Try the native Windows workspace preview

The native AgentMuru preview is for evaluating hardware discovery and the new local-first
terminal workspace on Windows. It is built from source and is **not included in the current PyPI release**.

Use the [verified Python quickstart](quickstart.md) when you need the released 0.2 runtime.

## What you can evaluate

- read-only CPU, memory, storage, and terminal discovery;
- explicit `supported`, `experimental`, or `unsupported` hardware reasons;
- responsive layouts for narrow, medium, and wide terminals;
- an event-driven agent map, run stream, inspector, and resource dock;
- a `Ctrl+P` command palette, keyboard navigation, help, and mouse focus;
- local session restore without storing tool arguments, prompts, credentials, or event
  payloads.

The preview does not yet download a model, execute generated agents, or isolate tools. Those
capabilities remain gated until their runtime, security, and low-end-device qualification
reports pass.

## Build the preview

Install Go 1.25.9, clone AgentMuru, and run:

```powershell
cd edge
go test ./...
go build -o .\.tmp\muru.exe .\cmd\muru
```

Inspect your machine without creating AgentMuru state or making a network request:

```powershell
.\.tmp\muru.exe doctor --json
```

`muru ui` is the native workspace entrypoint. From this source build, open it with:

```powershell
.\.tmp\muru.exe ui
```

Bare `.\.tmp\muru.exe` opens the same workspace. Both commands require interactive input and
output; redirected output receives one stable message pointing to `muru doctor --json`.

## Navigate the workspace

| Input | Result |
| --- | --- |
| `Ctrl+P` | Search the command palette |
| `Tab` / `Shift+Tab` | Move focus between visible product panes |
| `g`, then `a`, `r`, `i`, or `s` | Jump to the agent map, run stream, inspector, or resources |
| `/` | Enter run-stream filter mode |
| `?` | Open keyboard and mouse help |
| `q` | Quit, with confirmation when an agent is active |
| Mouse click | Focus a visible pane; every mouse action has a keyboard path |

At fewer than 70 columns the workspace shows one focused pane. From 70 through 99 columns it
uses tabs. At 100 columns and above it renders the multi-pane workspace.

## Understand local state

On Windows, navigation state is written atomically to:

```text
%LOCALAPPDATA%\AgentMuru\state\workspace.json
```

The snapshot allowlist contains only the focused pane, active tab, selected event ID, and
session ID. A corrupt snapshot is discarded and surfaced as a warning in a fresh workspace.

## Send useful feedback

Include the output of `muru doctor --json`, terminal name and width, the command you ran, and
what you expected. Remove any machine-specific paths you do not want to share. Do not attach
the local state directory.
