package cli

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"

	evaluation "github.com/AjayAJ2000/AgentMuru/edge/internal/eval"
	"github.com/AjayAJ2000/AgentMuru/edge/internal/orchestrator"
	"github.com/AjayAJ2000/AgentMuru/edge/internal/pack"
	"github.com/spf13/cobra"
)

func newBenchmarkCommand(dependencies Dependencies) *cobra.Command {
	packPath := ""
	candidate := "fixture-small"
	artifactBytes := uint64(1)
	output := ""
	fixture := false
	command := &cobra.Command{
		Use: "benchmark", Short: "Evaluate an agent pack candidate against mandatory gates", Args: cobra.NoArgs,
		RunE: func(command *cobra.Command, _ []string) error {
			value, err := pack.Load(packPath)
			if err != nil {
				return err
			}
			if !fixture {
				return errors.New("a real model benchmark requires a qualified runtime; use --fixture only for deterministic simulation")
			}
			if dependencies.StateDir == "" {
				return errors.New("runtime state directory is unavailable")
			}
			report, err := evaluation.EvaluatePack(command.Context(), orchestrator.NewEngine(dependencies.StateDir), value, candidate, artifactBytes)
			if err != nil {
				return err
			}
			gate := evaluation.Evaluate(report, evaluation.DefaultThresholds())
			report.Passed = gate.Passed
			data, _ := json.MarshalIndent(report, "", "  ")
			if output != "" {
				if err := os.WriteFile(output, append(data, '\n'), 0o600); err != nil {
					return err
				}
			}
			_, err = fmt.Fprintf(command.OutOrStdout(), "Benchmarked %d cases for %s: accuracy=%.3f passed=%t (fixture simulation).\n", len(value.Evals), candidate, report.ActionAccuracy, report.Passed)
			return err
		},
	}
	command.Flags().StringVar(&packPath, "pack", "", "validated agent-pack directory")
	command.Flags().StringVar(&candidate, "candidate", candidate, "candidate identifier")
	command.Flags().Uint64Var(&artifactBytes, "artifact-bytes", artifactBytes, "candidate artifact bytes")
	command.Flags().StringVar(&output, "output", "", "write the evaluation report")
	command.Flags().BoolVar(&fixture, "fixture", false, "run deterministic simulation rather than claim model qualification")
	_ = command.MarkFlagRequired("pack")
	return command
}
