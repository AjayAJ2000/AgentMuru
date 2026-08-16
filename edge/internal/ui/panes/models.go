package panes

import (
	"fmt"
	"sort"
)

type ModelState struct {
	ID          string
	State       string
	Digest      string
	MemoryBytes uint64
	Reason      string
}

func Models(states []ModelState, width, height int, focused bool) string {
	sort.Slice(states, func(left, right int) bool { return states[left].ID < states[right].ID })
	lines := make([]string, 0, len(states))
	if len(states) == 0 {
		lines = append(lines, "No verified models installed · Ctrl+P → models")
	}
	for _, state := range states {
		digest := state.Digest
		if len(digest) > 12 {
			digest = digest[:12]
		}
		memory := ""
		if state.MemoryBytes > 0 {
			memory = fmt.Sprintf(" · %d MiB", state.MemoryBytes>>20)
		}
		reason := ""
		if state.Reason != "" {
			reason = " · " + state.Reason
		}
		lines = append(lines, fmt.Sprintf("%-18s %-12s %s%s%s", state.ID, state.State, digest, memory, reason))
	}
	return Box("Models", lines, width, height, focused)
}
