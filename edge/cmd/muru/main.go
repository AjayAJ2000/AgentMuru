package main

import (
	"context"
	"fmt"
	"os"
	"path/filepath"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/cli"
	"github.com/AjayAJ2000/AgentMuru/edge/internal/config"
	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
	"github.com/AjayAJ2000/AgentMuru/edge/internal/platform"
)

var version = "0.3.0-dev"

func main() {
	paths, err := config.DiscoverPaths()
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	cmd := cli.NewRoot(cli.Dependencies{
		Version: version,
		Out:     os.Stdout,
		ErrOut:  os.Stderr,
		OpenWorkspace: func() error {
			hardware, err := platform.Discover(context.Background(), paths)
			if err != nil {
				return err
			}
			return cli.OpenWorkspace(cli.WorkspaceDependencies{
				In:          os.Stdin,
				Out:         os.Stdout,
				Hardware:    hardware,
				SessionPath: filepath.Join(paths.State, "workspace.json"),
			})
		},
		DiscoverHardware: func(ctx context.Context) (contracts.HardwareProfile, error) {
			return platform.Discover(ctx, paths)
		},
	})
	if err := cmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
