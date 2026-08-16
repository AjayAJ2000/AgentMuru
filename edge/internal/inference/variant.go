package inference

import (
	"errors"
	"sort"
	"strings"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

var ErrNoCompatibleVariant = errors.New("no compatible local inference runtime variant")

func SelectVariant(profile contracts.HardwareProfile, available []contracts.RuntimeVariant) (contracts.RuntimeVariant, error) {
	flags := make(map[string]struct{}, len(profile.CPU.Flags))
	for _, flag := range profile.CPU.Flags {
		flags[strings.ToLower(flag)] = struct{}{}
	}
	osName := strings.ToLower(profile.OS.Name)
	architecture := strings.ToLower(profile.OS.Architecture)
	candidates := make([]contracts.RuntimeVariant, 0, len(available))
	for _, variant := range available {
		if strings.ToLower(variant.OS) != osName || strings.ToLower(variant.Architecture) != architecture {
			continue
		}
		compatible := true
		for _, requirement := range variant.RequiredCPUFlags {
			if _, ok := flags[strings.ToLower(requirement)]; !ok {
				compatible = false
				break
			}
		}
		if compatible {
			candidates = append(candidates, variant)
		}
	}
	if len(candidates) == 0 {
		return contracts.RuntimeVariant{}, ErrNoCompatibleVariant
	}
	sort.Slice(candidates, func(left, right int) bool {
		if candidates[left].Rank == candidates[right].Rank {
			return candidates[left].ID < candidates[right].ID
		}
		return candidates[left].Rank > candidates[right].Rank
	})
	return candidates[0], nil
}
