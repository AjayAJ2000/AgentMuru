package cli

import (
	"errors"
	"time"

	"github.com/spf13/cobra"
)

func newQualificationIdleCommand(dependencies Dependencies) *cobra.Command {
	duration := 60 * time.Second
	command := &cobra.Command{
		Use:    "qualification-idle",
		Hidden: true,
		Args:   cobra.NoArgs,
		RunE: func(command *cobra.Command, _ []string) error {
			if dependencies.IdleProbe == nil {
				return errors.New("idle qualification probe is unavailable")
			}
			if duration <= 0 {
				return errors.New("idle qualification duration must be positive")
			}
			return dependencies.IdleProbe(command.Context(), duration)
		},
	}
	command.Flags().DurationVar(&duration, "duration", duration, "idle qualification duration")
	return command
}
