package ui

import (
	"fmt"
	"sort"
	"strings"
	"unicode"

	tea "charm.land/bubbletea/v2"
	"github.com/charmbracelet/x/ansi"
)

func (model *Model) View() tea.View {
	var content strings.Builder
	content.WriteString("AgentMuru  /  local agent workspace\n")
	content.WriteString(fmt.Sprintf("Layout: %s  Size: %dx%d\n", SelectLayout(model.width), model.width, model.height))
	content.WriteString("\nAgents\n")
	agents := make([]string, 0, len(model.agentStatuses))
	for agent := range model.agentStatuses {
		agents = append(agents, agent)
	}
	sort.Strings(agents)
	for _, agent := range agents {
		content.WriteString(fmt.Sprintf("  %-20s %s\n", sanitize(agent), sanitize(model.agentStatuses[agent])))
	}
	content.WriteString("\nRun stream\n")
	for _, event := range model.events {
		content.WriteString(fmt.Sprintf("  #%d %-24s %s\n", event.Sequence, sanitize(event.Type), sanitize(fmt.Sprint(event.Payload))))
	}
	content.WriteString("\nCtrl+P commands  ? help  Tab focus  q quit")
	view := tea.NewView(content.String())
	view.AltScreen = true
	view.MouseMode = tea.MouseModeCellMotion
	view.WindowTitle = "AgentMuru"
	return view
}

func sanitize(value string) string {
	stripped := ansi.Strip(value)
	return strings.Map(func(character rune) rune {
		if character == '\n' || character == '\t' {
			return character
		}
		if unicode.IsControl(character) {
			return -1
		}
		return character
	}, stripped)
}

func containsEscape(value string) bool {
	return strings.ContainsRune(value, '\x1b') || strings.ContainsRune(value, '\a')
}
