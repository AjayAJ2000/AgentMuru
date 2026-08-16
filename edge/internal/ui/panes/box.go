package panes

import (
	"strings"

	"github.com/charmbracelet/x/ansi"
)

func Box(title string, lines []string, width, height int, focused bool) string {
	if width < 12 {
		width = 12
	}
	if height < 3 {
		height = 3
	}
	marker := "○"
	if focused {
		marker = "●"
	}
	label := "─ " + marker + " " + title + " "
	label = ansi.Truncate(label, width-2, "")
	top := "┌" + label + strings.Repeat("─", max(0, width-2-ansi.StringWidth(label))) + "┐"
	bottom := "└" + strings.Repeat("─", width-2) + "┘"

	result := make([]string, 0, height)
	result = append(result, top)
	for row := 0; row < height-2; row++ {
		line := ""
		if row < len(lines) {
			line = ansi.Truncate(lines[row], width-4, "…")
		}
		padding := strings.Repeat(" ", max(0, width-4-ansi.StringWidth(line)))
		result = append(result, "│ "+line+padding+" │")
	}
	result = append(result, bottom)
	return strings.Join(result, "\n")
}
