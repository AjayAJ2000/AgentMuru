package ui

import (
	"encoding/json"
	"flag"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	tea "charm.land/bubbletea/v2"
	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

var updateGolden = flag.Bool("update", false, "update terminal workspace golden files")

func TestCtrlPOpensPaletteAndEscapeClosesIt(t *testing.T) {
	model := newWorkspaceModel(160)
	model = updateKey(t, model, tea.KeyPressMsg{Code: 'p', Mod: tea.ModCtrl})
	if !model.PaletteOpen() {
		t.Fatal("Ctrl+P did not open the command palette")
	}

	model = updateKey(t, model, tea.KeyPressMsg{Code: tea.KeyEscape})
	if model.PaletteOpen() {
		t.Fatal("Escape did not close the command palette")
	}
}

func TestPaletteDispatchesTheSelectedAction(t *testing.T) {
	requested := ""
	model := New(Dependencies{RequestAction: func(action string) error {
		requested = action
		return nil
	}})
	model = updateKey(t, model, tea.KeyPressMsg{Code: 'p', Mod: tea.ModCtrl})
	for _, character := range "doctor" {
		model = updateKey(t, model, tea.KeyPressMsg{Code: character})
	}
	next, command := model.Update(tea.KeyPressMsg{Code: tea.KeyEnter})
	model = next.(*Model)
	if command == nil {
		t.Fatal("Enter did not schedule the selected palette action")
	}
	message := command()
	model.Update(message)
	if requested != "doctor" {
		t.Fatalf("requested action = %q, want doctor", requested)
	}
	if model.PaletteOpen() {
		t.Fatal("palette remained open after dispatch")
	}
}

func TestHelpAndWhichKeyOverlaysHaveKeyboardPaths(t *testing.T) {
	model := newWorkspaceModel(100)
	model = updateKey(t, model, tea.KeyPressMsg{Code: '?'})
	if !model.HelpOpen() {
		t.Fatal("? did not open help")
	}
	model = updateKey(t, model, tea.KeyPressMsg{Code: tea.KeyEscape})
	model = updateKey(t, model, tea.KeyPressMsg{Code: 'g'})
	if !model.WhichKeyOpen() {
		t.Fatal("g did not open the which-key overlay")
	}
}

func TestMouseClickFocusesPaneWithoutChangingMode(t *testing.T) {
	model := newWorkspaceModel(160)
	next, _ := model.Update(tea.MouseClickMsg{X: 4, Y: 8, Button: tea.MouseLeft})
	model = next.(*Model)

	if got, want := model.FocusedPane(), "agent-map"; got != want {
		t.Fatalf("FocusedPane() = %q, want %q", got, want)
	}
	if got := model.Mode(); got != ModeNavigate {
		t.Fatalf("Mode() = %q, want %q", got, ModeNavigate)
	}
}

func TestTabCyclesPaneFocus(t *testing.T) {
	model := newWorkspaceModel(160)
	if got := model.FocusedPane(); got != "agent-map" {
		t.Fatalf("initial pane = %q, want agent-map", got)
	}
	model = updateKey(t, model, tea.KeyPressMsg{Code: tea.KeyTab})
	if got := model.FocusedPane(); got != "run-stream" {
		t.Fatalf("pane after Tab = %q, want run-stream", got)
	}
}

func TestNavigationPersistsOnlySanitizedSessionFields(t *testing.T) {
	path := filepath.Join(t.TempDir(), "workspace.json")
	model := New(Dependencies{SessionPath: path})
	model.sessionID = "session-safe"
	model.events = append(model.events, contracts.Event{
		ID: "event-secret", Type: "tool.called", Payload: map[string]any{"arguments": "TOP-SECRET"},
	})

	next, command := model.Update(tea.KeyPressMsg{Code: tea.KeyTab})
	if command == nil {
		t.Fatal("navigation did not schedule a session snapshot")
	}
	_ = command()
	model = next.(*Model)
	next, command = model.Update(tea.KeyPressMsg{Code: tea.KeyTab})
	if command == nil {
		t.Fatal("second navigation did not replace the session snapshot")
	}
	_ = next
	_ = command()

	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("ReadFile() error = %v", err)
	}
	if strings.Contains(string(raw), "TOP-SECRET") || strings.Contains(string(raw), "arguments") {
		t.Fatalf("session snapshot leaked runtime data: %s", raw)
	}
	var value map[string]any
	if err := json.Unmarshal(raw, &value); err != nil {
		t.Fatalf("session snapshot is not JSON: %v", err)
	}
	for _, field := range []string{"version", "focused_pane", "selected_event_id", "active_tab", "session_id"} {
		if _, ok := value[field]; !ok {
			t.Errorf("session snapshot missing %q", field)
		}
	}
	if got, want := value["focused_pane"], "inspector"; got != want {
		t.Fatalf("persisted focus = %v, want %v", got, want)
	}
}

func TestCorruptSessionProducesWarningAndFreshWorkspace(t *testing.T) {
	path := filepath.Join(t.TempDir(), "workspace.json")
	if err := os.WriteFile(path, []byte("{not-json"), 0o600); err != nil {
		t.Fatal(err)
	}

	model := New(Dependencies{SessionPath: path})
	if got := model.FocusedPane(); got != "agent-map" {
		t.Fatalf("focused pane = %q, want fresh agent-map", got)
	}
	if !strings.Contains(model.View().Content, "workspace.warning") {
		t.Fatalf("corrupt session warning not rendered: %q", model.View().Content)
	}
}

func TestSessionRestoreKeepsSelectedEventDuringReplay(t *testing.T) {
	path := filepath.Join(t.TempDir(), "workspace.json")
	raw := []byte(`{"version":1,"focused_pane":"inspector","selected_event_id":"event-1","active_tab":"inspector","session_id":"session-1","unknown":"ignored"}`)
	if err := os.WriteFile(path, raw, 0o600); err != nil {
		t.Fatal(err)
	}
	model := New(Dependencies{SessionPath: path})
	for index, id := range []string{"event-1", "event-2"} {
		next, _ := model.Update(RuntimeEventMsg{Event: contracts.Event{
			ID: id, Type: "tool.completed", SessionID: "session-1", Sequence: uint64(index + 1), Payload: map[string]any{},
		}})
		model = next.(*Model)
	}
	if got, want := model.focusedPane, "inspector"; got != want {
		t.Fatalf("focused pane = %q, want %q", got, want)
	}
	if got, want := model.selectedEvent, 0; got != want {
		t.Fatalf("selected event index = %d, want %d", got, want)
	}
}

func TestWorkspaceGoldenLayouts(t *testing.T) {
	for _, test := range []struct {
		name  string
		width int
	}{
		{name: "wide", width: 160},
		{name: "narrow", width: 60},
	} {
		t.Run(test.name, func(t *testing.T) {
			model := goldenModel(test.width)
			got := model.View().Content
			path := filepath.Join("testdata", test.name+".golden")
			if *updateGolden {
				if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
					t.Fatal(err)
				}
				if err := os.WriteFile(path, []byte(got), 0o600); err != nil {
					t.Fatal(err)
				}
			}
			want, err := os.ReadFile(path)
			if err != nil {
				t.Fatalf("read golden: %v", err)
			}
			if got != string(want) {
				t.Fatalf("workspace does not match %s golden\n--- got ---\n%s\n--- want ---\n%s", test.name, got, want)
			}
		})
	}
}

func newWorkspaceModel(width int) *Model {
	model := New(Dependencies{})
	next, _ := model.Update(tea.WindowSizeMsg{Width: width, Height: 32})
	return next.(*Model)
}

func goldenModel(width int) *Model {
	model := newWorkspaceModel(width)
	model.dependencies.Hardware.CPU.Model = "Intel Pentium Silver N6000"
	model.dependencies.Hardware.Memory.TotalBytes = 8 << 30
	model.dependencies.Hardware.Support.Level = "supported"
	model.sessionID = "demo-session"
	model.events = []contracts.Event{
		{ID: "event-1", SessionID: "demo-session", Sequence: 1, Timestamp: time.Date(2026, 8, 17, 10, 0, 0, 0, time.UTC), Type: "session.started", Payload: map[string]any{"requirement": "Summarize local notes"}},
		{ID: "event-2", SessionID: "demo-session", Sequence: 2, Timestamp: time.Date(2026, 8, 17, 10, 0, 1, 0, time.UTC), Type: "agent.started", Payload: map[string]any{"agent": "router"}},
	}
	model.selectedEvent = 1
	model.agentStatuses["router"] = "active"
	model.agentStatuses["writer"] = "waiting"
	return model
}

func updateKey(t *testing.T, model *Model, key tea.KeyPressMsg) *Model {
	t.Helper()
	next, _ := model.Update(key)
	updated, ok := next.(*Model)
	if !ok {
		t.Fatalf("Update() returned %T, want *Model", next)
	}
	return updated
}
