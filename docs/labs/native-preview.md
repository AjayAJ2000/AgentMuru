# Native preview

The Go-native preview profiles a machine, opens a responsive terminal workspace, validates
portable agent packs, and runs their decisions in simulation. It is distributed separately
through GitHub Releases and is not installed by the Python wheel.

## Current boundary

The preview can inspect CPU, memory, storage, architecture, and terminal dimensions without a
network request. Its terminal UI includes agent, run, inspector, resource, and model views plus
a searchable command palette.

Generated packs are forced to simulation. They can propose an action but cannot execute it. The
public model catalog is intentionally empty until a model and runtime pair passes clean-machine
and named low-end reference-device qualification.

## Build from source

Install the Go version declared by `edge/go.mod`, clone the repository, then run:

```powershell
cd edge
go test ./...
go build -trimpath -o ..\.tmp\muru.exe .\cmd\muru
cd ..
```

Profile the machine:

```powershell
.\.tmp\muru.exe doctor --json
```

Open the terminal workspace:

```powershell
.\.tmp\muru.exe ui
```

After a native prerelease installation, use `muru doctor --json` and `muru ui`. Bare `muru`
opens the same terminal workspace when input and output are interactive.

## Navigation

| Input | Result |
| --- | --- |
| `Ctrl+P` | Open the command palette |
| `Tab` and `Shift+Tab` | Move focus |
| `g`, then `a`, `r`, `i`, or `s` | Jump to a major view |
| `/` | Filter the run stream |
| `?` | Open input help |
| `q` | Quit, with confirmation for active work |

Below 70 columns the UI uses one pane. From 70 through 99 columns it uses tabs. At 100 columns
and above it presents multiple panes.

## Report useful feedback

Include redacted `muru doctor --json` output, operating system, architecture, terminal name and
width, exact command, expected result, and observed result. Do not attach the native state
directory or credential material.
