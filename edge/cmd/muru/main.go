package main

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/catalog"
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
	bootstrap, err := catalog.LoadBootstrap()
	if err != nil {
		fmt.Fprintln(os.Stderr, "embedded model catalog failed verification:", err)
		os.Exit(1)
	}
	models := catalog.NewLocalModels(bootstrap, catalog.NewCache(filepath.Join(paths.Cache, "models")), nil)
	cmd := cli.NewRoot(cli.Dependencies{
		Version: version,
		Out:     os.Stdout,
		ErrOut:  os.Stderr,
		Models:  models,
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
		IdleProbe: func(ctx context.Context, duration time.Duration) error {
			hardware, err := platform.Discover(ctx, paths)
			if err != nil {
				return err
			}
			return cli.IdleWorkspace(ctx, duration, hardware)
		},
	})
	if err := cmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
