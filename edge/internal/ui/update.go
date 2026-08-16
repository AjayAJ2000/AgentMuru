package ui

import (
	"unicode"

	tea "charm.land/bubbletea/v2"
	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
	"github.com/AjayAJ2000/AgentMuru/edge/internal/ui/overlay"
)

func (model *Model) Update(message tea.Msg) (tea.Model, tea.Cmd) {
	switch typed := message.(type) {
	case tea.WindowSizeMsg:
		model.width = typed.Width
		model.height = typed.Height
	case RuntimeEventMsg:
		model.events = append(model.events, typed.Event)
		if model.sessionID == "" {
			model.sessionID = typed.Event.SessionID
		}
		if model.selectedEventID == "" || typed.Event.ID == model.selectedEventID {
			model.selectedEvent = len(model.events) - 1
		}
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
	case tea.KeyPressMsg:
		return model.updateKey(typed)
	case tea.MouseClickMsg:
		return model.updateMouse(typed)
	case sessionSavedMsg:
		if typed.err != nil {
			model.events = append(model.events, warningEvent("could not save workspace state: "+typed.err.Error()))
		}
	case actionResultMsg:
		eventType := "workspace.action.completed"
		payload := map[string]any{"action": typed.action}
		if typed.err != nil {
			eventType = "workspace.action.failed"
			payload["error"] = typed.err.Error()
		}
		model.events = append(model.events, contracts.Event{Type: eventType, Payload: payload})
	}
	return model, nil
}

func (model *Model) updateKey(key tea.KeyPressMsg) (tea.Model, tea.Cmd) {
	stroke := key.Keystroke()
	if model.paletteOpen {
		switch stroke {
		case "esc":
			model.paletteOpen = false
			model.paletteQuery = ""
		case "enter":
			matches := overlay.FilterActions(model.paletteQuery)
			if len(matches) == 0 {
				return model, nil
			}
			action := matches[0]
			model.paletteOpen = false
			model.paletteQuery = ""
			if model.dependencies.RequestAction == nil {
				model.events = append(model.events, contracts.Event{
					Type: "workspace.action.requested", Payload: map[string]any{"action": action},
				})
				return model, nil
			}
			return model, func() tea.Msg {
				return actionResultMsg{action: action, err: model.dependencies.RequestAction(action)}
			}
		case "backspace":
			if runes := []rune(model.paletteQuery); len(runes) > 0 {
				model.paletteQuery = string(runes[:len(runes)-1])
			}
		default:
			if key.Code > 0 && unicode.IsPrint(key.Code) && key.Mod == 0 {
				model.paletteQuery += string(key.Code)
			}
		}
		return model, nil
	}
	if model.helpOpen {
		if stroke == "esc" || stroke == "?" {
			model.helpOpen = false
		}
		return model, nil
	}
	if model.whichKeyOpen {
		if pane, ok := whichKeyPane(stroke); ok {
			model.focus(pane)
			model.whichKeyOpen = false
			return model, model.persistSession()
		}
		if stroke == "esc" {
			model.whichKeyOpen = false
		}
		return model, nil
	}
	if model.mode == ModeConfirmQuit {
		switch stroke {
		case "y":
			return model, tea.Quit
		case "n", "esc":
			model.mode = ModeNavigate
		}
		return model, nil
	}

	switch stroke {
	case "ctrl+p":
		model.paletteOpen = true
	case "?":
		model.helpOpen = true
	case "g":
		model.whichKeyOpen = true
	case "tab":
		model.cycleFocus(1)
		return model, model.persistSession()
	case "shift+tab":
		model.cycleFocus(-1)
		return model, model.persistSession()
	case "/":
		model.mode = ModeFilter
	case "esc":
		model.mode = ModeNavigate
	case "q":
		if model.hasActiveWork() {
			model.mode = ModeConfirmQuit
			return model, nil
		}
		return model, tea.Quit
	}
	return model, nil
}

func (model *Model) updateMouse(message tea.MouseClickMsg) (tea.Model, tea.Cmd) {
	if message.Button != tea.MouseLeft {
		return model, nil
	}
	if SelectLayout(model.width) == LayoutPanes {
		if message.Y >= model.height-6 {
			model.focus("resources")
		} else {
			left, right := wideColumns(model.width)
			switch {
			case message.X < left:
				model.focus("agent-map")
			case message.X >= model.width-right:
				model.focus("inspector")
			default:
				model.focus("run-stream")
			}
		}
		return model, model.persistSession()
	}
	return model, nil
}

func (model *Model) focus(pane string) {
	for _, candidate := range paneOrder {
		if candidate == pane {
			model.focusedPane = pane
			model.activeTab = pane
			return
		}
	}
}

func (model *Model) cycleFocus(delta int) {
	index := 0
	for candidate, pane := range paneOrder {
		if pane == model.focusedPane {
			index = candidate
			break
		}
	}
	index = (index + delta + len(paneOrder)) % len(paneOrder)
	model.focus(paneOrder[index])
}

func (model *Model) hasActiveWork() bool {
	for _, status := range model.agentStatuses {
		if status == "active" || status == "running" {
			return true
		}
	}
	return false
}

func whichKeyPane(stroke string) (string, bool) {
	panes := map[string]string{"a": "agent-map", "r": "run-stream", "i": "inspector", "s": "resources"}
	pane, ok := panes[stroke]
	return pane, ok
}

func wideColumns(width int) (left int, right int) {
	left = 30
	right = 34
	if width < 120 {
		left = 26
		right = 28
	}
	return left, right
}
