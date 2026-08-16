package cli

import (
	"encoding/json"
	"fmt"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
	"github.com/spf13/cobra"
)

func newDoctorCommand(deps Dependencies) *cobra.Command {
	var jsonOutput bool
	command := &cobra.Command{
		Use:   "doctor",
		Short: "Inspect local hardware without changing it",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, _ []string) error {
			if deps.DiscoverHardware == nil {
				return fmt.Errorf("hardware discovery is unavailable")
			}
			profile, err := deps.DiscoverHardware(cmd.Context())
			if err != nil {
				return err
			}
			if jsonOutput {
				encoder := json.NewEncoder(cmd.OutOrStdout())
				encoder.SetEscapeHTML(false)
				return encoder.Encode(profile)
			}
			return writeDoctorSummary(cmd, profile)
		},
	}
	command.Flags().BoolVar(&jsonOutput, "json", false, "emit the stable hardware profile as JSON")
	return command
}

func writeDoctorSummary(cmd *cobra.Command, profile contracts.HardwareProfile) error {
	lines := []string{
		fmt.Sprintf("%-12s %s %s (%s)", "OS", profile.OS.Name, profile.OS.Version, profile.OS.Architecture),
		fmt.Sprintf("%-12s %s", "CPU", profile.CPU.Model),
		fmt.Sprintf("%-12s %.1f GB total", "Memory", float64(profile.Memory.TotalBytes)/(1<<30)),
		fmt.Sprintf("%-12s %.1f GB free", "Storage", float64(profile.Storage.FreeBytes)/(1<<30)),
		fmt.Sprintf("%-12s %s", "Support", profile.Support.Level),
	}
	for _, reason := range profile.Support.Reasons {
		lines = append(lines, fmt.Sprintf("%-12s %s", "Reason", reason))
	}
	for _, line := range lines {
		if _, err := fmt.Fprintln(cmd.OutOrStdout(), line); err != nil {
			return err
		}
	}
	return nil
}
