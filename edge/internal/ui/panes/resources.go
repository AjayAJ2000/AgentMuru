package panes

import (
	"fmt"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

func Resources(profile contracts.HardwareProfile, loadedModels int, modelMemory uint64, width, height int, focused bool) string {
	memoryGiB := float64(profile.Memory.TotalBytes) / float64(uint64(1)<<30)
	line := fmt.Sprintf("CPU %s  ·  RAM %.1f GiB  ·  support %s", profile.CPU.Model, memoryGiB, profile.Support.Level)
	if profile.CPU.Model == "" {
		line = "Hardware profile unavailable · run muru doctor"
	}
	modelLine := fmt.Sprintf("resident models %d  ·  model RAM %d MiB", loadedModels, modelMemory>>20)
	return Box("Resources", []string{line, modelLine}, width, height, focused)
}
