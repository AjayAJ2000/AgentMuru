package panes

import (
	"fmt"
	"sort"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

func Inspector(event *contracts.Event, width, height int, focused bool) string {
	if event == nil {
		return Box("Inspector", []string{"Select a run event"}, width, height, focused)
	}
	lines := []string{
		"type  " + event.Type,
		fmt.Sprintf("seq   %d", event.Sequence),
		"id    " + event.ID,
	}
	keys := make([]string, 0, len(event.Payload))
	for key := range event.Payload {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	if len(keys) > 0 {
		lines = append(lines, "", "payload")
	}
	for _, key := range keys {
		lines = append(lines, fmt.Sprintf("%s: %v", key, event.Payload[key]))
	}
	return Box("Inspector", lines, width, height, focused)
}
