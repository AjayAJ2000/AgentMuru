package main

import (
	"fmt"
	"os"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/cli"
)

var version = "0.3.0-dev"

func main() {
	cmd := cli.NewRoot(cli.Dependencies{
		Version: version,
		Out:     os.Stdout,
		ErrOut:  os.Stderr,
		OpenWorkspace: func() error {
			_, err := fmt.Fprintln(os.Stdout, "AgentMuru terminal workspace is starting soon.")
			return err
		},
	})
	if err := cmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
