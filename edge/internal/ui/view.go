package ui

import (
	"fmt"
	"strings"
	"unicode"

	tea "charm.land/bubbletea/v2"
	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
	"github.com/AjayAJ2000/AgentMuru/edge/internal/ui/overlay"
	"github.com/AjayAJ2000/AgentMuru/edge/internal/ui/panes"
	"github.com/charmbracelet/x/ansi"
)

func (model *Model) View() tea.View {
	width := model.width
	if width <= 0 {
		width = 80
	}
	height := model.height
	if height <= 0 {
		height = 24
	}

	var content strings.Builder
	content.WriteString("AgentMuru  LOCAL-FIRST AGENT WORKSPACE\n")
	content.WriteString(model.contextLine(width))
	content.WriteString("\n\n")

	switch SelectLayout(width) {
	case LayoutPanes:
		content.WriteString(model.renderWide(width, height))
	case LayoutTabs:
		content.WriteString(model.renderTabbed(width, height))
	default:
		content.WriteString(model.renderSingle(width, height))
	}
	content.WriteString("\n")
	content.WriteString(model.footer())

	switch {
	case model.paletteOpen:
		content.WriteString("\n\n" + overlay.Palette(model.paletteQuery, width))
	case model.helpOpen:
		content.WriteString("\n\n" + overlay.Help(width))
	case model.whichKeyOpen:
		content.WriteString("\n\n" + overlay.WhichKey(width))
	case model.mode == ModeConfirmQuit:
		content.WriteString("\n\nActive work is running. Quit anyway? [y/N]")
	}

	view := tea.NewView(content.String())
	view.AltScreen = true
	view.MouseMode = tea.MouseModeCellMotion
	view.WindowTitle = "AgentMuru"
	return view
}

func (model *Model) contextLine(width int) string {
	session := model.sessionID
	if session == "" {
		session = "new session"
	}
	line := fmt.Sprintf("%s  ·  %s  ·  %d events  ·  %s", SelectLayout(width), session, len(model.events), model.mode)
	for _, event := range model.events {
		if event.Type == "workspace.warning" {
			line += "  ·  workspace.warning"
			break
		}
	}
	return ansi.Truncate(line, width, "…")
}

func (model *Model) renderWide(width, height int) string {
	left, right := wideColumns(width)
	center := max(24, width-left-right-2)
	topHeight := max(8, height-11)
	safeEvents := sanitizeEvents(model.events)
	safeStatuses := sanitizeStatuses(model.agentStatuses)

	agentMap := panes.AgentMap(safeStatuses, left, topHeight, model.focusedPane == "agent-map")
	runStream := panes.RunStream(safeEvents, model.selectedEvent, center, topHeight, model.focusedPane == "run-stream")
	inspector := panes.Inspector(selectedEvent(safeEvents, model.selectedEvent), right, topHeight, model.focusedPane == "inspector")
	top := joinHorizontal([]string{agentMap, runStream, inspector}, " ")
	resources := panes.Resources(model.dependencies.Hardware, width, 4, model.focusedPane == "resources")
	return top + "\n" + resources
}

func (model *Model) renderTabbed(width, height int) string {
	tabs := model.tabBar()
	pane := model.renderPane(model.activeTab, width, max(8, height-8))
	return tabs + "\n" + pane
}

func (model *Model) renderSingle(width, height int) string {
	return model.renderPane(model.focusedPane, width, max(8, height-7))
}

func (model *Model) renderPane(name string, width, height int) string {
	events := sanitizeEvents(model.events)
	switch name {
	case "run-stream":
		return panes.RunStream(events, model.selectedEvent, width, height, true)
	case "inspector":
		return panes.Inspector(selectedEvent(events, model.selectedEvent), width, height, true)
	case "resources":
		return panes.Resources(model.dependencies.Hardware, width, height, true)
	default:
		return panes.AgentMap(sanitizeStatuses(model.agentStatuses), width, height, true)
	}
}

func (model *Model) tabBar() string {
	parts := make([]string, 0, len(paneOrder))
	for _, pane := range paneOrder {
		label := strings.ReplaceAll(pane, "-", " ")
		if pane == model.activeTab {
			parts = append(parts, "["+label+"]")
		} else {
			parts = append(parts, " "+label+" ")
		}
	}
	return strings.Join(parts, "  ")
}

func (model *Model) footer() string {
	if model.mode == ModeFilter {
		return "/ filter active  ·  Esc navigate"
	}
	return "Ctrl+P commands  ·  ? help  ·  Tab focus  ·  g jump  ·  q quit"
}

func selectedEvent(events []contracts.Event, index int) *contracts.Event {
	if index < 0 || index >= len(events) {
		return nil
	}
	return &events[index]
}

func joinHorizontal(blocks []string, separator string) string {
	lines := make([][]string, len(blocks))
	height := 0
	for index, block := range blocks {
		lines[index] = strings.Split(block, "\n")
		height = max(height, len(lines[index]))
	}
	rows := make([]string, 0, height)
	for row := 0; row < height; row++ {
		parts := make([]string, len(lines))
		for column := range lines {
			if row < len(lines[column]) {
				parts[column] = lines[column][row]
			}
		}
		rows = append(rows, strings.Join(parts, separator))
	}
	return strings.Join(rows, "\n")
}

func sanitizeEvents(events []contracts.Event) []contracts.Event {
	result := make([]contracts.Event, len(events))
	for index, event := range events {
		result[index] = event
		result[index].ID = sanitize(event.ID)
		result[index].Type = sanitize(event.Type)
		result[index].SessionID = sanitize(event.SessionID)
		result[index].Payload = sanitizeMap(event.Payload)
	}
	return result
}

func sanitizeStatuses(statuses map[string]string) map[string]string {
	result := make(map[string]string, len(statuses))
	for agent, status := range statuses {
		result[sanitize(agent)] = sanitize(status)
	}
	return result
}

func sanitizeMap(value map[string]any) map[string]any {
	result := make(map[string]any, len(value))
	for key, item := range value {
		result[sanitize(key)] = sanitizeValue(item)
	}
	return result
}

func sanitizeValue(value any) any {
	switch typed := value.(type) {
	case string:
		return sanitize(typed)
	case map[string]any:
		return sanitizeMap(typed)
	case []any:
		result := make([]any, len(typed))
		for index, item := range typed {
			result[index] = sanitizeValue(item)
		}
		return result
	default:
		return value
	}
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
