package overlay

import (
	"strings"

	"github.com/charmbracelet/x/ansi"
)

func framed(lines []string, width int) string {
	if width < 20 {
		width = 20
	}
	result := []string{"╭" + strings.Repeat("─", width-2) + "╮"}
	for _, line := range lines {
		line = ansi.Truncate(line, width-4, "…")
		result = append(result, "│ "+line+strings.Repeat(" ", max(0, width-4-ansi.StringWidth(line)))+" │")
	}
	result = append(result, "╰"+strings.Repeat("─", width-2)+"╯")
	return strings.Join(result, "\n")
}
