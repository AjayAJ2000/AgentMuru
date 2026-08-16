package platform

import (
	"io"
	"os"
	"strings"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
	"golang.org/x/term"
)

type fdWriter interface {
	io.Writer
	Fd() uintptr
}

func DiscoverTerminal(writer io.Writer) contracts.TerminalInfo {
	file, ok := writer.(fdWriter)
	if !ok {
		return contracts.TerminalInfo{}
	}
	fd := int(file.Fd())
	interactive := term.IsTerminal(fd)
	width := 0
	if interactive {
		if detected, _, err := term.GetSize(fd); err == nil {
			width = detected
		}
	}
	colorTerm := strings.ToLower(os.Getenv("COLORTERM"))
	return contracts.TerminalInfo{
		Interactive: interactive,
		TrueColor:   interactive && (colorTerm == "truecolor" || colorTerm == "24bit"),
		Mouse:       interactive,
		Width:       width,
	}
}
