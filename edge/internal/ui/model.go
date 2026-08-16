package ui

import (
	tea "charm.land/bubbletea/v2"
	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

type Dependencies struct {
	Events   <-chan contracts.Event
	Hardware contracts.HardwareProfile
}

type RuntimeEventMsg struct {
	Event contracts.Event
}

type Model struct {
	dependencies  Dependencies
	width         int
	height        int
	events        []contracts.Event
	agentStatuses map[string]string
}

func New(dependencies Dependencies) *Model {
	return &Model{
		dependencies:  dependencies,
		agentStatuses: make(map[string]string),
	}
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
