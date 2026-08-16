package cli

import (
	"context"
	"errors"
	"fmt"
	"io"
	"os"
	"time"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
	"github.com/spf13/cobra"
)

type Dependencies struct {
	Version          string
	Out              io.Writer
	ErrOut           io.Writer
	OpenWorkspace    func() error
	DiscoverHardware func(context.Context) (contracts.HardwareProfile, error)
	IdleProbe        func(context.Context, time.Duration) error
	Models           ModelService
}

func NewRoot(deps Dependencies) *cobra.Command {
	if deps.Out == nil {
		deps.Out = os.Stdout
	}
	if deps.ErrOut == nil {
		deps.ErrOut = os.Stderr
	}

	root := &cobra.Command{
		Use:           "muru",
		Short:         "Build and run measured local agent teams",
		SilenceUsage:  true,
		SilenceErrors: true,
		RunE: func(_ *cobra.Command, _ []string) error {
			if deps.OpenWorkspace == nil {
				return errors.New("terminal workspace is unavailable")
			}
			return deps.OpenWorkspace()
		},
	}
	root.SetOut(deps.Out)
	root.SetErr(deps.ErrOut)
	root.AddCommand(newDoctorCommand(deps))
	root.AddCommand(newModelsCommand(deps))
	root.AddCommand(newQualificationIdleCommand(deps))
	root.AddCommand(&cobra.Command{
		Use:   "ui",
		Short: "Open the local agent workspace",
		Args:  cobra.NoArgs,
		RunE: func(_ *cobra.Command, _ []string) error {
			if deps.OpenWorkspace == nil {
				return errors.New("terminal workspace is unavailable")
			}
			return deps.OpenWorkspace()
		},
	})
	root.AddCommand(&cobra.Command{
		Use:   "version",
		Short: "Print the AgentMuru version",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, _ []string) error {
			_, err := fmt.Fprintf(cmd.OutOrStdout(), "AgentMuru %s\n", deps.Version)
			return err
		},
	})
	return root
}
