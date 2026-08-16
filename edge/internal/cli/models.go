package cli

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/catalog"
	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
	"github.com/spf13/cobra"
)

var (
	ErrLicenseRequired = errors.New("license acceptance is required")
	ErrModelNotFound   = errors.New("model artifact was not found in the verified catalog")
)

type ModelService interface {
	Catalog(context.Context) (contracts.Catalog, error)
	Inventory() ([]catalog.InstalledArtifact, error)
	Install(context.Context, contracts.Artifact, string) error
	Remove(string) error
}

func newModelsCommand(dependencies Dependencies) *cobra.Command {
	command := &cobra.Command{Use: "models", Short: "Inspect and manage verified local models"}
	command.AddCommand(newModelsListCommand(dependencies), newModelsInstallCommand(dependencies), newModelsRemoveCommand(dependencies))
	return command
}

func newModelsListCommand(dependencies Dependencies) *cobra.Command {
	jsonOutput := false
	command := &cobra.Command{
		Use: "list", Short: "List installed verified models", Args: cobra.NoArgs,
		RunE: func(command *cobra.Command, _ []string) error {
			if dependencies.Models == nil {
				return errors.New("model service is unavailable")
			}
			inventory, err := dependencies.Models.Inventory()
			if err != nil {
				return err
			}
			if jsonOutput {
				return writeJSON(command.OutOrStdout(), map[string]any{"models": inventory})
			}
			if len(inventory) == 0 {
				_, err = fmt.Fprintln(command.OutOrStdout(), "No verified models are installed.")
				return err
			}
			for _, installed := range inventory {
				digest := installed.Artifact.SHA256
				if len(digest) > 12 {
					digest = digest[:12]
				}
				if _, err := fmt.Fprintf(command.OutOrStdout(), "%s\t%s\t%s\n", installed.Artifact.ID, installed.Artifact.ModelID, digest); err != nil {
					return err
				}
			}
			return nil
		},
	}
	command.Flags().BoolVar(&jsonOutput, "json", false, "emit machine-readable JSON")
	return command
}

func newModelsInstallCommand(dependencies Dependencies) *cobra.Command {
	acceptedLicense := ""
	jsonOutput := false
	command := &cobra.Command{
		Use: "install <artifact-id>", Short: "Install a catalog-verified GGUF model", Args: cobra.ExactArgs(1),
		RunE: func(command *cobra.Command, args []string) error {
			if dependencies.Models == nil {
				return errors.New("model service is unavailable")
			}
			verified, err := dependencies.Models.Catalog(command.Context())
			if err != nil {
				return err
			}
			artifact, ok := findArtifact(verified, args[0])
			if !ok {
				return ErrModelNotFound
			}
			if artifact.License.Gated && acceptedLicense != artifact.License.ID {
				if jsonOutput {
					_ = writeJSON(command.OutOrStdout(), map[string]any{"error": map[string]any{
						"code": "license_required", "artifact_id": artifact.ID, "license_id": artifact.License.ID, "license_url": artifact.License.LicenseURL,
					}})
				} else {
					_, _ = fmt.Fprintf(command.OutOrStdout(), "License %s: %s\nAccept explicitly with --accept-license %s\n", artifact.License.ID, artifact.License.LicenseURL, artifact.License.ID)
				}
				return ErrLicenseRequired
			}
			if err := dependencies.Models.Install(command.Context(), artifact, acceptedLicense); err != nil {
				return err
			}
			if jsonOutput {
				return writeJSON(command.OutOrStdout(), map[string]any{"installed": artifact.ID, "sha256": artifact.SHA256})
			}
			_, err = fmt.Fprintf(command.OutOrStdout(), "Installed %s (%s)\n", artifact.ID, artifact.SHA256)
			return err
		},
	}
	command.Flags().StringVar(&acceptedLicense, "accept-license", "", "record acceptance of the exact catalog license id")
	command.Flags().BoolVar(&jsonOutput, "json", false, "emit machine-readable JSON and never prompt")
	return command
}

func newModelsRemoveCommand(dependencies Dependencies) *cobra.Command {
	jsonOutput := false
	command := &cobra.Command{
		Use: "remove <artifact-id>", Short: "Remove an installed model", Args: cobra.ExactArgs(1),
		RunE: func(command *cobra.Command, args []string) error {
			if dependencies.Models == nil {
				return errors.New("model service is unavailable")
			}
			if err := dependencies.Models.Remove(args[0]); err != nil {
				return err
			}
			if jsonOutput {
				return writeJSON(command.OutOrStdout(), map[string]any{"removed": args[0]})
			}
			_, err := fmt.Fprintf(command.OutOrStdout(), "Removed %s\n", args[0])
			return err
		},
	}
	command.Flags().BoolVar(&jsonOutput, "json", false, "emit machine-readable JSON")
	return command
}

func findArtifact(value contracts.Catalog, id string) (contracts.Artifact, bool) {
	for _, artifact := range value.Artifacts {
		if artifact.ID == id {
			return artifact, true
		}
	}
	return contracts.Artifact{}, false
}

func writeJSON(writer io.Writer, value any) error {
	encoder := json.NewEncoder(writer)
	encoder.SetEscapeHTML(true)
	return encoder.Encode(value)
}
