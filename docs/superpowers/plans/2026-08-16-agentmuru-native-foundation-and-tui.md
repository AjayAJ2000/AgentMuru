# AgentMuru Native Foundation and Terminal Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a single native `muru` binary with shared contracts, Windows hardware discovery, durable events, and a responsive TUIOS-inspired terminal workspace driven by fake runtime events.

**Architecture:** Create a Go module in `edge/` and versioned JSON schemas in `schemas/`. Use Bubble Tea's Model-View-Update loop for event-driven UI updates, while domain services remain independent of Bubble Tea. Keep the Python CLI unchanged until the native release artifact is ready.

**Tech Stack:** Go 1.25.9, `charm.land/bubbletea/v2` v2.0.8, `charm.land/lipgloss/v2` v2.0.5, Cobra v1.10.2, gopsutil v4.26.6, `golang.org/x/sys`, Python pytest contract checks.

## Global Constraints

- Windows 10/11 x64 and 8 GB RAM are first-class; unsupported hardware produces reasons rather than a crash.
- Bootstrap working set must remain below 150 MB before inference starts.
- Events are appended before publication and monotonic per session.
- Essential information works at 60 columns, without true color, and with redirected output.
- The UI renders on events and input, not a fixed high-frequency ticker.
- Existing Python tests and public imports remain compatible.

---

### Task 1: Define language-neutral contract fixtures

**Files:**
- Create: `schemas/hardware/v1/profile.schema.json`
- Create: `schemas/events/v1/event.schema.json`
- Create: `schemas/agent-pack/v1/manifest.schema.json`
- Create: `schemas/testdata/hardware/pentium-8gb.json`
- Create: `schemas/testdata/events/session-started.json`
- Create: `tests/contracts/test_edge_contract_fixtures.py`

**Interfaces:**
- Produces: JSON field names consumed by both runtimes: `schema_version`, `os`, `cpu`, `memory`, `storage`, `terminal`, `runtime_variants`, `support`, and event-v1 fields matching `RuntimeEvent.to_dict()`.

- [ ] **Step 1: Write failing Python fixture tests**

```python
def test_edge_event_fixture_round_trips() -> None:
    value = json.loads(EVENT_FIXTURE.read_text(encoding="utf-8"))
    event = RuntimeEvent.from_dict(value)
    assert event.to_dict() == value


def test_hardware_fixture_has_explicit_support_reasons() -> None:
    value = json.loads(HARDWARE_FIXTURE.read_text(encoding="utf-8"))
    assert value["schema_version"] == "hardware.agentmuru.dev/v1"
    assert isinstance(value["support"]["reasons"], list)
```

- [ ] **Step 2: Run the tests and confirm missing fixtures fail**

Run: `python -m pytest tests/contracts/test_edge_contract_fixtures.py -q`

Expected: FAIL because the schemas and fixtures do not exist.

- [ ] **Step 3: Add strict schemas and representative fixtures**

Require `additionalProperties: false` at the hardware profile and manifest roots. Keep
event payload open because event types own payload shapes. Represent byte counts as
non-negative integers and CPU flags as lowercase unique strings.

- [ ] **Step 4: Run focused and existing event tests**

Run: `python -m pytest tests/contracts/test_edge_contract_fixtures.py tests/core/test_events.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add schemas tests/contracts
git commit -m "feat: define edge runtime contracts"
```

### Task 2: Bootstrap the native command and configuration paths

**Files:**
- Create: `edge/go.mod`
- Create: `edge/cmd/muru/main.go`
- Create: `edge/internal/cli/root.go`
- Create: `edge/internal/cli/root_test.go`
- Create: `edge/internal/config/paths.go`
- Create: `edge/internal/config/paths_test.go`

**Interfaces:**
- Produces: `cli.NewRoot(version string, out, errOut io.Writer) *cobra.Command`
- Produces: `config.PathsFor(home string) Paths` with `Config`, `Cache`, `Data`, and `State` directories.

- [ ] **Step 1: Write failing command tests**

```go
func TestVersionDoesNotEnterTUI(t *testing.T) {
    var out bytes.Buffer
    cmd := cli.NewRoot("0.3.0-dev", &out, io.Discard)
    cmd.SetArgs([]string{"version"})
    require.NoError(t, cmd.Execute())
    assert.Equal(t, "AgentMuru 0.3.0-dev\n", out.String())
}
```

- [ ] **Step 2: Initialize the module and confirm the test fails**

Run: `cd edge; go mod init github.com/AjayAJ2000/AgentMuru/edge; go test ./internal/cli`

Expected: FAIL because `NewRoot` is undefined.

- [ ] **Step 3: Implement the root command and Windows-safe paths**

`muru` with no arguments calls an injected `OpenWorkspace` function. `version`, `doctor`,
and `ui` are explicit subcommands. Resolve `%LOCALAPPDATA%\AgentMuru` for data/cache/state
on Windows and XDG-equivalent paths elsewhere for development tests. Never write during
path discovery.

- [ ] **Step 4: Run native tests and build**

Run: `cd edge; go test ./...; go build ./cmd/muru`

Expected: PASS and `edge/muru.exe` exists on Windows.

- [ ] **Step 5: Commit**

```powershell
git add edge
git commit -m "feat: bootstrap native muru command"
```

### Task 3: Implement hardware and terminal discovery

**Files:**
- Create: `edge/internal/platform/profile.go`
- Create: `edge/internal/platform/profile_windows.go`
- Create: `edge/internal/platform/profile_other.go`
- Create: `edge/internal/platform/terminal.go`
- Create: `edge/internal/platform/profile_test.go`
- Create: `edge/internal/cli/doctor.go`
- Test: `edge/internal/cli/doctor_test.go`

**Interfaces:**
- Produces: `platform.Discover(ctx context.Context, paths config.Paths) (contracts.HardwareProfile, error)`
- Produces: `platform.Classify(profile HardwareProfile) Support`

- [ ] **Step 1: Write table-driven classification tests**

```go
func TestClassifyBaselineWithoutAVX2(t *testing.T) {
    p := fixtureProfile("windows", "amd64", 8<<30, []string{"sse4.2", "avx"})
    got := platform.Classify(p)
    assert.Equal(t, "experimental", got.Level)
    assert.Contains(t, got.RuntimeVariants, "windows-x64-avx")
}
```

- [ ] **Step 2: Run tests and verify failure**

Run: `cd edge; go test ./internal/platform ./internal/cli -run 'Doctor|Classify'`

Expected: FAIL because discovery and classification are undefined.

- [ ] **Step 3: Implement read-only discovery**

Use gopsutil for memory, disk, and CPU metadata; use `golang.org/x/sys/cpu` for instruction
flags; use `golang.org/x/term` and environment capability hints for terminal reporting.
Sort and deduplicate flags. Classify less than 8 GB as unsupported for the flagship,
baseline/AVX without AVX2 as experimental, and AVX2 with sufficient disk as supported.

- [ ] **Step 4: Implement stable doctor output**

`muru doctor --json` emits only the hardware profile JSON to stdout. The human form prints
status, component, observed value, and reasons. Neither form creates directories or makes
network requests.

- [ ] **Step 5: Run focused tests**

Run: `cd edge; go test ./internal/platform ./internal/cli`

Expected: PASS on Windows and non-Windows CI using injected probes.

- [ ] **Step 6: Commit**

```powershell
git add edge/internal/platform edge/internal/cli
git commit -m "feat: profile edge hardware"
```

### Task 4: Add append-before-publish native events

**Files:**
- Create: `edge/internal/contracts/event.go`
- Create: `edge/internal/events/store.go`
- Create: `edge/internal/events/jsonl.go`
- Create: `edge/internal/events/bus.go`
- Create: `edge/internal/events/events_test.go`

**Interfaces:**
- Produces: `Store.Append(context.Context, Event) (Event, error)` and `Store.Replay(sessionID string, after uint64) ([]Event, error)`
- Produces: `Bus.Publish(context.Context, Event) (Event, error)` where persistence completes before subscribers receive the event.

- [ ] **Step 1: Write ordering and crash-tail tests**

```go
func TestPublishAppendsBeforeSubscriberReceives(t *testing.T) {
    persisted := false
    store := spyStore{afterAppend: func() { persisted = true }}
    bus := events.NewBus(&store)
    got := subscribeOne(t, bus)
    _, err := bus.Publish(context.Background(), fixtureEvent())
    require.NoError(t, err)
    assert.True(t, persisted)
    assert.Equal(t, uint64(1), (<-got).Sequence)
}
```

- [ ] **Step 2: Run tests and verify failure**

Run: `cd edge; go test ./internal/events`

Expected: FAIL because the store and bus do not exist.

- [ ] **Step 3: Implement JSONL persistence and replay**

Write one compact JSON event plus newline under a per-session lock, flush before returning,
and assign the next sequence from the last valid record. Replay ignores one truncated final
line but rejects corruption before the tail. Subscribers receive a copy only after Append
returns successfully.

- [ ] **Step 4: Run event and Python fixture tests**

Run: `cd edge; go test ./internal/events; cd ..; python -m pytest tests/contracts/test_edge_contract_fixtures.py tests/core/test_events.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add edge/internal/contracts edge/internal/events
git commit -m "feat: persist native runtime events"
```

### Task 5: Build the event-driven terminal workspace shell

**Files:**
- Create: `edge/internal/ui/model.go`
- Create: `edge/internal/ui/update.go`
- Create: `edge/internal/ui/view.go`
- Create: `edge/internal/ui/layout.go`
- Create: `edge/internal/ui/theme.go`
- Create: `edge/internal/ui/keymap.go`
- Create: `edge/internal/ui/model_test.go`
- Create: `edge/internal/cli/ui.go`

**Interfaces:**
- Consumes: native event subscription and `HardwareProfile`
- Produces: `ui.New(deps Dependencies) tea.Model`
- Produces: responsive `LayoutMode` values `single`, `tabs`, and `panes`.

- [ ] **Step 1: Write update and responsive-layout tests**

```go
func TestLayoutBreakpoints(t *testing.T) {
    assert.Equal(t, ui.LayoutSingle, ui.SelectLayout(69))
    assert.Equal(t, ui.LayoutTabs, ui.SelectLayout(99))
    assert.Equal(t, ui.LayoutPanes, ui.SelectLayout(100))
}

func TestRuntimeEventUpdatesWithoutTick(t *testing.T) {
    model := ui.New(testDeps())
    next, _ := model.Update(ui.RuntimeEventMsg{Event: agentStarted()})
    assert.Equal(t, "active", next.(ui.Model).AgentStatus("router"))
}
```

- [ ] **Step 2: Run tests and verify failure**

Run: `cd edge; go test ./internal/ui`

Expected: FAIL because the UI package is absent.

- [ ] **Step 3: Implement MVU shell and rendering constraints**

Subscribe through a blocking Bubble Tea command that returns one `RuntimeEventMsg`, then
register the next subscription command. Use timer commands only for user-visible elapsed
time at one-second resolution while work is active. Sanitize runtime strings before
Lipgloss rendering and provide no-color tokens.

- [ ] **Step 4: Wire `muru` and `muru ui`**

Enter alternate-screen mode only when stdin and stdout are terminals. Otherwise print a
single actionable message for bare `muru`, while explicit non-interactive commands retain
stable output.

- [ ] **Step 5: Run tests and build**

Run: `cd edge; go test ./internal/ui ./internal/cli; go build ./cmd/muru`

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add edge/internal/ui edge/internal/cli
git commit -m "feat: add native terminal workspace shell"
```

### Task 6: Add product panes, palette, help, and persistent sessions

**Files:**
- Create: `edge/internal/ui/panes/agentmap.go`
- Create: `edge/internal/ui/panes/runstream.go`
- Create: `edge/internal/ui/panes/inspector.go`
- Create: `edge/internal/ui/panes/resources.go`
- Create: `edge/internal/ui/overlay/palette.go`
- Create: `edge/internal/ui/overlay/help.go`
- Create: `edge/internal/ui/overlay/whichkey.go`
- Create: `edge/internal/ui/session.go`
- Create: `edge/internal/ui/workspace_test.go`
- Create: `edge/internal/ui/testdata/wide.golden`
- Create: `edge/internal/ui/testdata/narrow.golden`

**Interfaces:**
- Produces: palette actions `create`, `run`, `doctor`, `benchmark`, `models`, `permissions`, `explain`, `settings`, and `help`.
- Produces: session snapshot containing focused pane, selected event, active tab, and session ID; never secrets or unredacted arguments.

- [ ] **Step 1: Write golden and keyboard tests**

```go
func TestCtrlPOpensPaletteAndEscapeClosesIt(t *testing.T) {
    m := updateKey(t, newWideModel(), tea.KeyPressMsg{Code: 'p', Mod: tea.ModCtrl})
    assert.True(t, m.PaletteOpen())
    m = updateKey(t, m, tea.KeyPressMsg{Code: tea.KeyEscape})
    assert.False(t, m.PaletteOpen())
}

func TestMouseClickFocusesPaneWithoutChangingMode(t *testing.T) {
    m := updateMouse(t, newWideModel(), clickAt(4, 8))
    assert.Equal(t, "agent-map", m.FocusedPane())
    assert.Equal(t, ui.ModeNavigate, m.Mode())
}
```

- [ ] **Step 2: Run tests and verify failure**

Run: `cd edge; go test ./internal/ui -run 'Palette|Golden|Session'`

Expected: FAIL because panes and overlays are absent.

- [ ] **Step 3: Implement pane projections and overlays**

Render the agent map from typed handoff events, the run stream from ordered events, the
inspector from the selected event, and the resource dock from hardware/resource messages.
The palette uses fuzzy subsequence matching with deterministic alphabetical tie-breaking.
`?` opens help; holding the configured prefix opens a which-key overlay; Tab cycles
panes/tabs; `/` focuses filtering; mouse clicks focus panes and activate visible controls;
`q` requests confirmation when work is active. Every mouse action has a keyboard path.

- [ ] **Step 4: Implement sanitized session snapshots**

Write snapshots atomically under the state directory after navigation changes, restore the
last valid snapshot on startup, and discard unknown fields. A corrupt snapshot produces a
warning event and a fresh workspace.

- [ ] **Step 5: Update golden files and verify**

Run: `cd edge; go test ./internal/ui -update; go test ./internal/ui`

Expected: PASS with committed 160-column and 60-column snapshots.

- [ ] **Step 6: Commit**

```powershell
git add edge/internal/ui
git commit -m "feat: add terminal workspace navigation"
```

### Task 7: Add native CI, documentation, and Gate A verification

**Files:**
- Create: `.github/workflows/edge-ci.yml`
- Create: `docs/getting-started/native-preview.md`
- Modify: `mkdocs.yml`
- Modify: `docs/architecture/target-state.md`
- Modify: `docs/architecture/ai-native-transformation.md`
- Create: `qualification/edge/measure_idle.ps1`

**Interfaces:**
- Produces: Windows and Linux development CI for Go tests/builds; Windows is the release authority.

- [ ] **Step 1: Add a documentation contract test**

```python
def test_native_preview_is_not_documented_as_released() -> None:
    text = (DOCS / "getting-started" / "native-preview.md").read_text(encoding="utf-8")
    assert "not included in the current PyPI release" in text
```

- [ ] **Step 2: Run the test and verify failure**

Run: `python -m pytest tests/test_documentation_contract.py -q`

Expected: FAIL until the preview page and assertion are added.

- [ ] **Step 3: Add CI and honest preview documentation**

CI runs `go test ./...`, `go vet ./...`, and `go build ./cmd/muru` from `edge/` on
`windows-latest` and `ubuntu-latest`. The preview page documents only doctor, fake events,
navigation, breakpoints, and session replay.

- [ ] **Step 4: Measure idle behavior and run Gate A suite**

Run: `powershell -ExecutionPolicy Bypass -File qualification/edge/measure_idle.ps1`

Expected: the script records process working set and CPU samples for 60 idle seconds,
fails if bootstrap working set reaches 150 MB, and writes a JSON report under an ignored
temporary directory.

Run: `python -m pytest -q; cd edge; go test ./...; go vet ./...; go build ./cmd/muru; cd ..; python -m mkdocs build --strict`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add .github/workflows/edge-ci.yml docs mkdocs.yml qualification/edge tests/test_documentation_contract.py
git commit -m "ci: qualify native terminal foundation"
```
