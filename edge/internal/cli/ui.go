package cli

import (
	"fmt"
	"io"
	"os"

	tea "charm.land/bubbletea/v2"
	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
	workspace "github.com/AjayAJ2000/AgentMuru/edge/internal/ui"
	"golang.org/x/term"
)

type WorkspaceDependencies struct {
	In                io.Reader
	Out               io.Writer
	Hardware          contracts.HardwareProfile
	Events            <-chan contracts.Event
	SessionPath       string
	InputInteractive  func(io.Reader) bool
	OutputInteractive func(io.Writer) bool
	Run               func(*workspace.Model, io.Reader, io.Writer) error
}

func OpenWorkspace(dependencies WorkspaceDependencies) error {
	if dependencies.In == nil {
		dependencies.In = os.Stdin
	}
	if dependencies.Out == nil {
		dependencies.Out = os.Stdout
	}
	if dependencies.InputInteractive == nil {
		dependencies.InputInteractive = readerIsTerminal
	}
	if dependencies.OutputInteractive == nil {
		dependencies.OutputInteractive = writerIsTerminal
	}
	if dependencies.Run == nil {
		dependencies.Run = runWorkspace
	}

	if !dependencies.InputInteractive(dependencies.In) || !dependencies.OutputInteractive(dependencies.Out) {
		_, err := fmt.Fprintln(dependencies.Out, "AgentMuru's workspace needs an interactive terminal. Run `muru doctor --json` for machine-readable diagnostics.")
		return err
	}

	model := workspace.New(workspace.Dependencies{
		Events:      dependencies.Events,
		Hardware:    dependencies.Hardware,
		SessionPath: dependencies.SessionPath,
	})
	return dependencies.Run(model, dependencies.In, dependencies.Out)
}

func runWorkspace(model *workspace.Model, input io.Reader, output io.Writer) error {
	program := tea.NewProgram(model, tea.WithInput(input), tea.WithOutput(output))
	_, err := program.Run()
	return err
}

func readerIsTerminal(reader io.Reader) bool {
	file, ok := reader.(interface{ Fd() uintptr })
	return ok && term.IsTerminal(int(file.Fd()))
}

func writerIsTerminal(writer io.Writer) bool {
	file, ok := writer.(interface{ Fd() uintptr })
	return ok && term.IsTerminal(int(file.Fd()))
}
