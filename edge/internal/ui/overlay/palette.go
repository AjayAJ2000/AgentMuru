package overlay

import (
	"sort"
	"strings"
)

var PaletteActions = []string{
	"benchmark",
	"create",
	"doctor",
	"explain",
	"help",
	"models",
	"permissions",
	"run",
	"settings",
}

func FilterActions(query string) []string {
	query = strings.ToLower(strings.TrimSpace(query))
	matches := make([]string, 0, len(PaletteActions))
	for _, action := range PaletteActions {
		if fuzzySubsequence(strings.ToLower(action), query) {
			matches = append(matches, action)
		}
	}
	sort.Strings(matches)
	return matches
}

func Palette(query string, width int) string {
	lines := []string{"COMMAND PALETTE", "> " + query}
	for _, action := range FilterActions(query) {
		lines = append(lines, "  "+action)
	}
	return framed(lines, min(width, 52))
}

func fuzzySubsequence(value, query string) bool {
	if query == "" {
		return true
	}
	position := 0
	for _, character := range value {
		if position < len(query) && byte(character) == query[position] {
			position++
		}
	}
	return position == len(query)
}
