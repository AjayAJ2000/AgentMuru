# Try the adaptive local preview

AgentMuru `0.3.0-alpha.1` is a feedback preview for building small, inspectable agent teams on
Windows and Linux. The native `muru` command profiles the machine, presents a responsive
terminal workspace, validates portable agent packs, and runs their decisions in simulation.

The verified Python `0.2.0` runtime remains the stable package on PyPI. The native preview is
distributed separately through GitHub Releases.

## What works now

- read-only CPU, memory, storage, and terminal discovery with support reasons;
- layouts for narrow, medium, and wide terminals, plus keyboard and mouse navigation;
- a searchable command palette, agent map, run stream, inspector, resource view, and model view;
- strict portable agent packs with agents, typed actions, policy, evaluations, and checksums;
- deterministic requirements-to-pack compilation and a 40-case measured sample;
- durable, redacted run explanations and crash-safe runtime events;
- signed model-catalog verification, atomic GGUF downloads, compatible llama.cpp selection,
  authenticated loopback supervision, constrained JSON decisions, and one-model residency on
  8 GB profiles;
- a trusted-host capability broker that defaults to deny, confines file reads, separates
  executables from exact arguments, requires process approval, and validates HTTPS targets.

## Important preview boundary

Generated packs are forced to simulation. They can propose an action but cannot execute it.
The public model catalog is intentionally empty: no model/runtime pair has passed
both clean-machine and named low-end reference-device qualification. AgentMuru therefore does
not claim automatic production model selection, Android support, Pentium support, tool
containerization, or safe internet retrieval in this preview.

This boundary is deliberate. It lets people evaluate the product experience and pack contract
without mistaking fixture evidence for device or security evidence.

## Install or build

### Install the Windows prerelease

Download the installer script so you can inspect it, then run it:

```powershell
Invoke-WebRequest `
  https://raw.githubusercontent.com/AjayAJ2000/AgentMuru/main/tools/install-native.ps1 `
  -OutFile .\install-agentmuru.ps1
.\install-agentmuru.ps1 -AddToPath
muru doctor --json
```

The installer downloads the versioned x64 archive, verifies its published SHA-256 digest,
copies `muru.exe` under your local application-data directory, and updates only your user PATH
when `-AddToPath` is present.

### Build from source

Install Go 1.25.9 or later, clone AgentMuru, and run:

```powershell
cd edge
go test ./...
go build -trimpath -o ..\.tmp\muru.exe .\cmd\muru
cd ..
```

Inspect the machine without creating AgentMuru state or making a network request:

```powershell
.\.tmp\muru.exe doctor --json
```

Open the workspace:

```powershell
.\.tmp\muru.exe ui
```

After installation, the equivalent command is `muru ui`. Bare `muru` opens the same
workspace. Both commands require interactive input and output;
redirected output receives a stable message pointing to `muru doctor --json`.

## Navigate the workspace

| Input | Result |
| --- | --- |
| `Ctrl+P` | Search the command palette |
| `Tab` / `Shift+Tab` | Move focus between visible panes |
| `g`, then `a`, `r`, `i`, or `s` | Jump to agents, runs, inspector, or resources |
| `/` | Filter the run stream |
| `?` | Open keyboard and mouse help |
| `q` | Quit, with confirmation when an agent is active |
| Mouse click | Focus a pane; every mouse action has a keyboard path |

Below 70 columns the workspace shows one pane. From 70 through 99 columns it uses tabs. At
100 columns and above it renders multiple panes.

Next, [run the measured action-router tutorial](action-router.md).

## Send useful feedback

Include redacted output from `muru doctor --json`, the terminal name and width, the command you
ran, what you expected, and what happened. Do not attach the AgentMuru state directory.
