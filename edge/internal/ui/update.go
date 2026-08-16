package ui

import tea "charm.land/bubbletea/v2"

func (model *Model) Update(message tea.Msg) (tea.Model, tea.Cmd) {
	switch typed := message.(type) {
	case tea.WindowSizeMsg:
		model.width = typed.Width
		model.height = typed.Height
	case RuntimeEventMsg:
		model.events = append(model.events, typed.Event)
		agent, _ := typed.Event.Payload["agent"].(string)
		switch typed.Event.Type {
		case "agent.started":
			if agent != "" {
				model.agentStatuses[agent] = "active"
			}
		case "agent.completed":
			if agent != "" {
				model.agentStatuses[agent] = "completed"
			}
		case "agent.failed":
			if agent != "" {
				model.agentStatuses[agent] = "failed"
			}
		}
		return model, model.waitForEvent()
	}
	return model, nil
}
