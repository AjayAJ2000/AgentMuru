package cli

import (
	"errors"
	"fmt"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/orchestrator"
	"github.com/AjayAJ2000/AgentMuru/edge/internal/pack"
	"github.com/spf13/cobra"
)

func newRunCommand(dependencies Dependencies) *cobra.Command {
	packPath := ""
	input := ""
	jsonOutput := false
	command := &cobra.Command{
		Use: "run", Short: "Run a validated agent pack in its active effect mode", Args: cobra.NoArgs,
		RunE: func(command *cobra.Command, _ []string) error {
			if dependencies.StateDir == "" {
				return errors.New("runtime state directory is unavailable")
			}
			value, err := pack.Load(packPath)
			if err != nil {
				return err
			}
			runID, err := orchestrator.NewEngine(dependencies.StateDir).Submit(command.Context(), value, input)
			if err != nil {
				return err
			}
			if jsonOutput {
				return writeJSON(command.OutOrStdout(), map[string]any{"run_id": runID, "mode": value.Manifest.Effects})
			}
			_, err = fmt.Fprintf(command.OutOrStdout(), "Run %s recorded in %s mode. No effects were executed.\n", runID, value.Manifest.Effects)
			return err
		},
	}
	command.Flags().StringVar(&packPath, "pack", "", "validated agent-pack directory")
	command.Flags().StringVar(&input, "input", "", "user requirement to route")
	command.Flags().BoolVar(&jsonOutput, "json", false, "emit machine-readable JSON")
	_ = command.MarkFlagRequired("pack")
	_ = command.MarkFlagRequired("input")
	return command
}

func newExplainCommand(dependencies Dependencies) *cobra.Command {
	jsonOutput := false
	command := &cobra.Command{
		Use: "explain <run-id>", Short: "Explain a run from its recorded decisions", Args: cobra.ExactArgs(1),
		RunE: func(command *cobra.Command, args []string) error {
			if dependencies.StateDir == "" {
				return errors.New("runtime state directory is unavailable")
			}
			explanation, err := orchestrator.NewEngine(dependencies.StateDir).Explain(args[0])
			if err != nil {
				return err
			}
			if jsonOutput {
				return writeJSON(command.OutOrStdout(), explanation)
			}
			_, err = fmt.Fprintf(command.OutOrStdout(), "Run %s\nPath: %v\nReason: %s\nEffects executed: %d\n", explanation.RunID, explanation.Path, explanation.Reason, explanation.EffectsExecuted)
			return err
		},
	}
	command.Flags().BoolVar(&jsonOutput, "json", false, "emit machine-readable JSON")
	return command
}
