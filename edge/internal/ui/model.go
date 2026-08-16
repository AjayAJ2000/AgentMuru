package ui

import (
	tea "charm.land/bubbletea/v2"
	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

type Dependencies struct {
	Events        <-chan contracts.Event
	Hardware      contracts.HardwareProfile
	SessionPath   string
	RequestAction func(string) error
}

type RuntimeEventMsg struct {
	Event contracts.Event
}

type sessionSavedMsg struct {
	err error
}

type actionResultMsg struct {
	action string
	err    error
}

type Mode string

const (
	ModeNavigate    Mode = "navigate"
	ModeFilter      Mode = "filter"
	ModeConfirmQuit Mode = "confirm-quit"
)

var paneOrder = []string{"agent-map", "run-stream", "inspector", "resources"}

type Model struct {
	dependencies    Dependencies
	width           int
	height          int
	events          []contracts.Event
	agentStatuses   map[string]string
	focusedPane     string
	activeTab       string
	selectedEvent   int
	selectedEventID string
	sessionID       string
	mode            Mode
	paletteOpen     bool
	paletteQuery    string
	helpOpen        bool
	whichKeyOpen    bool
}

func New(dependencies Dependencies) *Model {
	model := &Model{
		dependencies:  dependencies,
		agentStatuses: make(map[string]string),
		focusedPane:   paneOrder[0],
		activeTab:     paneOrder[0],
		selectedEvent: -1,
		mode:          ModeNavigate,
	}
	if dependencies.SessionPath != "" {
		snapshot, warning := loadSession(dependencies.SessionPath)
		model.restore(snapshot)
		if warning != "" {
			model.events = append(model.events, contracts.Event{
				Type:    "workspace.warning",
				Payload: map[string]any{"message": warning},
			})
		}
	}
	return model
}

func (model *Model) Init() tea.Cmd {
	return model.waitForEvent()
}

func (model *Model) waitForEvent() tea.Cmd {
	if model.dependencies.Events == nil {
		return nil
	}
	return func() tea.Msg {
		event, ok := <-model.dependencies.Events
		if !ok {
			return nil
		}
		return RuntimeEventMsg{Event: event}
	}
}

func (model *Model) AgentStatus(agent string) string {
	return model.agentStatuses[agent]
}

func (model *Model) PaletteOpen() bool {
	return model.paletteOpen
}

func (model *Model) HelpOpen() bool {
	return model.helpOpen
}

func (model *Model) WhichKeyOpen() bool {
	return model.whichKeyOpen
}

func (model *Model) FocusedPane() string {
	return model.focusedPane
}

func (model *Model) Mode() Mode {
	return model.mode
}
