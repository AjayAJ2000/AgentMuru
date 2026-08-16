package ui

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"

	tea "charm.land/bubbletea/v2"
	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

const sessionSnapshotVersion = 1

type sessionSnapshot struct {
	Version         int    `json:"version"`
	FocusedPane     string `json:"focused_pane"`
	SelectedEventID string `json:"selected_event_id"`
	ActiveTab       string `json:"active_tab"`
	SessionID       string `json:"session_id"`
}

func (model *Model) snapshot() sessionSnapshot {
	selectedEventID := ""
	if model.selectedEvent >= 0 && model.selectedEvent < len(model.events) {
		selectedEventID = model.events[model.selectedEvent].ID
	}
	return sessionSnapshot{
		Version:         sessionSnapshotVersion,
		FocusedPane:     model.focusedPane,
		SelectedEventID: selectedEventID,
		ActiveTab:       model.activeTab,
		SessionID:       model.sessionID,
	}
}

func (model *Model) restore(snapshot sessionSnapshot) {
	if snapshot.Version != sessionSnapshotVersion {
		return
	}
	model.focus(snapshot.FocusedPane)
	if isPane(snapshot.ActiveTab) {
		model.activeTab = snapshot.ActiveTab
	}
	model.sessionID = snapshot.SessionID
	model.selectedEventID = snapshot.SelectedEventID
}

func (model *Model) persistSession() tea.Cmd {
	if model.dependencies.SessionPath == "" {
		return nil
	}
	path := model.dependencies.SessionPath
	snapshot := model.snapshot()
	return func() tea.Msg {
		return sessionSavedMsg{err: saveSession(path, snapshot)}
	}
}

func saveSession(path string, snapshot sessionSnapshot) error {
	if path == "" {
		return errors.New("session path is empty")
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		return fmt.Errorf("create session directory: %w", err)
	}
	temporary, err := os.CreateTemp(filepath.Dir(path), ".workspace-*.tmp")
	if err != nil {
		return fmt.Errorf("create session snapshot: %w", err)
	}
	temporaryPath := temporary.Name()
	defer os.Remove(temporaryPath)

	encoder := json.NewEncoder(temporary)
	encoder.SetEscapeHTML(true)
	if err := encoder.Encode(snapshot); err != nil {
		temporary.Close()
		return fmt.Errorf("encode session snapshot: %w", err)
	}
	if err := temporary.Sync(); err != nil {
		temporary.Close()
		return fmt.Errorf("flush session snapshot: %w", err)
	}
	if err := temporary.Close(); err != nil {
		return fmt.Errorf("close session snapshot: %w", err)
	}
	if err := replaceFile(temporaryPath, path); err != nil {
		return fmt.Errorf("replace session snapshot: %w", err)
	}
	return nil
}

func loadSession(path string) (sessionSnapshot, string) {
	raw, err := os.ReadFile(path)
	if errors.Is(err, os.ErrNotExist) {
		return sessionSnapshot{}, ""
	}
	if err != nil {
		return sessionSnapshot{}, "could not read the previous workspace; started fresh"
	}
	var snapshot sessionSnapshot
	if err := json.Unmarshal(raw, &snapshot); err != nil || snapshot.Version != sessionSnapshotVersion {
		return sessionSnapshot{}, "the previous workspace state was corrupt; started fresh"
	}
	if !isPane(snapshot.FocusedPane) || !isPane(snapshot.ActiveTab) {
		return sessionSnapshot{}, "the previous workspace state was invalid; started fresh"
	}
	return snapshot, ""
}

func isPane(value string) bool {
	for _, pane := range paneOrder {
		if value == pane {
			return true
		}
	}
	return false
}

func warningEvent(message string) contracts.Event {
	return contracts.Event{Type: "workspace.warning", Payload: map[string]any{"message": message}}
}
