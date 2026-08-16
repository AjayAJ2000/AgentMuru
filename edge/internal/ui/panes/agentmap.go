package panes

import (
	"fmt"
	"sort"
)

func AgentMap(statuses map[string]string, width, height int, focused bool) string {
	agents := make([]string, 0, len(statuses))
	for agent := range statuses {
		agents = append(agents, agent)
	}
	sort.Strings(agents)
	lines := []string{"local team"}
	if len(agents) == 0 {
		lines = append(lines, "No agents yet", "Create one with Ctrl+P")
	}
	for index, agent := range agents {
		connector := "├─"
		if index == len(agents)-1 {
			connector = "└─"
		}
		lines = append(lines, fmt.Sprintf("%s %-14s %s", connector, agent, statusToken(statuses[agent])))
	}
	return Box("Agent map", lines, width, height, focused)
}

func statusToken(status string) string {
	switch status {
	case "active", "running":
		return "RUN"
	case "completed":
		return "OK"
	case "failed":
		return "ERR"
	default:
		return "WAIT"
	}
}
