package panes

import (
	"fmt"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

func RunStream(events []contracts.Event, selected, width, height int, focused bool) string {
	lines := make([]string, 0, len(events)+1)
	if len(events) == 0 {
		lines = append(lines, "Waiting for a local run…")
	}
	start := max(0, len(events)-(height-3))
	for index := start; index < len(events); index++ {
		marker := " "
		if index == selected {
			marker = "›"
		}
		event := events[index]
		lines = append(lines, fmt.Sprintf("%s #%03d %-22s %v", marker, event.Sequence, event.Type, event.Payload))
	}
	return Box("Run stream", lines, width, height, focused)
}
