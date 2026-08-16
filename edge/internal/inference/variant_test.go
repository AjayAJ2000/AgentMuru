package inference

import (
	"errors"
	"testing"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

func TestSelectVariantNeverChoosesAVX2ForAVXCPU(t *testing.T) {
	profile := contracts.HardwareProfile{OS: contracts.OSInfo{Name: "windows", Architecture: "amd64"}, CPU: contracts.CPUInfo{Flags: []string{"sse4.2", "avx"}}}
	got, err := SelectVariant(profile, fixtureVariants())
	if err != nil {
		t.Fatal(err)
	}
	if got.ID != "windows-x64-avx" {
		t.Fatalf("variant = %q, want windows-x64-avx", got.ID)
	}
}

func TestSelectVariantChoosesHighestCompatibleRank(t *testing.T) {
	profile := contracts.HardwareProfile{OS: contracts.OSInfo{Name: "windows", Architecture: "amd64"}, CPU: contracts.CPUInfo{Flags: []string{"sse4.2", "avx", "avx2", "fma", "bmi2"}}}
	got, err := SelectVariant(profile, fixtureVariants())
	if err != nil {
		t.Fatal(err)
	}
	if got.ID != "windows-x64-avx2" {
		t.Fatalf("variant = %q, want windows-x64-avx2", got.ID)
	}
}

func TestSelectVariantDoesNotExecuteToProbeCompatibility(t *testing.T) {
	profile := contracts.HardwareProfile{OS: contracts.OSInfo{Name: "windows", Architecture: "arm64"}}
	_, err := SelectVariant(profile, fixtureVariants())
	if !errors.Is(err, ErrNoCompatibleVariant) {
		t.Fatalf("SelectVariant() error = %v, want ErrNoCompatibleVariant", err)
	}
}

func fixtureVariants() []contracts.RuntimeVariant {
	return []contracts.RuntimeVariant{
		{ID: "windows-x64-avx2", OS: "windows", Architecture: "amd64", RequiredCPUFlags: []string{"avx", "avx2"}, Rank: 30},
		{ID: "windows-x64-baseline", OS: "windows", Architecture: "amd64", RequiredCPUFlags: []string{"sse4.2"}, Rank: 10},
		{ID: "windows-x64-avx", OS: "windows", Architecture: "amd64", RequiredCPUFlags: []string{"avx"}, Rank: 20},
	}
}
