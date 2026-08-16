package cli

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"os"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/compiler"
	"github.com/AjayAJ2000/AgentMuru/edge/internal/pack"
	"github.com/spf13/cobra"
)

var ErrDraftIncomplete = errors.New("agent pack draft needs answers")

func newCreateCommand() *cobra.Command {
	from := ""
	output := ""
	plain := false
	command := &cobra.Command{
		Use: "create", Short: "Compile a requirement draft into a safe agent pack", Args: cobra.NoArgs,
		RunE: func(command *cobra.Command, _ []string) error {
			if from == "" || output == "" {
				return errors.New("--from and --output are required")
			}
			data, err := os.ReadFile(from)
			if err != nil {
				return err
			}
			var draft compiler.Draft
			decoder := json.NewDecoder(bytes.NewReader(data))
			decoder.DisallowUnknownFields()
			if err := decoder.Decode(&draft); err != nil {
				return err
			}
			compiled, questions, err := compiler.Compile(draft)
			if err != nil {
				return err
			}
			if len(questions) > 0 {
				if plain {
					_ = writeJSON(command.OutOrStdout(), map[string]any{"error": "draft_incomplete", "questions": questions})
					return ErrDraftIncomplete
				}
				return errors.New("open `muru` for guided answers or rerun with --plain after completing the draft")
			}
			if err := pack.Export(output, compiled); err != nil {
				return err
			}
			_, err = fmt.Fprintf(command.OutOrStdout(), "Created agent pack %s with %d agent(s) in simulation mode.\n", compiled.Manifest.ID, len(compiled.Agents))
			return err
		},
	}
	command.Flags().StringVar(&from, "from", "", "read a strict JSON requirement draft")
	command.Flags().StringVar(&output, "output", "", "write the validated agent-pack directory")
	command.Flags().BoolVar(&plain, "plain", false, "never prompt; return missing questions as JSON")
	return command
}
