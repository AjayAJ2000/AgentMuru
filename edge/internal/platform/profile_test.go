package platform

import (
	"testing"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

func fixtureProfile(memory uint64, free uint64, flags ...string) contracts.HardwareProfile {
	return contracts.HardwareProfile{
		SchemaVersion: contracts.HardwareSchemaV1,
		OS: contracts.OSInfo{
			Name:         "windows",
			Version:      "11",
			Architecture: "amd64",
		},
		CPU: contracts.CPUInfo{
			Vendor:        "GenuineIntel",
			Model:         "Pentium fixture",
			PhysicalCores: 2,
			LogicalCores:  2,
			Flags:         flags,
		},
		Memory:  contracts.MemoryInfo{TotalBytes: memory, AvailableBytes: memory / 2},
		Storage: contracts.StorageInfo{CachePath: `C:\cache`, FreeBytes: free},
	}
}

func TestClassifyAVX2MachineAsSupported(t *testing.T) {
	profile := fixtureProfile(8<<30, 3<<30, "sse4.2", "avx", "avx2")

	got := Classify(profile)

	if got.Level != contracts.SupportSupported {
		t.Fatalf("Level = %q, want supported", got.Level)
	}
	assertStrings(t, got.RuntimeVariants, []string{
		"windows-x64-baseline",
		"windows-x64-avx",
		"windows-x64-avx2",
	})
}

func TestClassifyAVXWithoutAVX2AsExperimental(t *testing.T) {
	profile := fixtureProfile(8<<30, 3<<30, "sse4.2", "avx")

	got := Classify(profile)

	if got.Level != contracts.SupportExperimental {
		t.Fatalf("Level = %q, want experimental", got.Level)
	}
	assertStrings(t, got.RuntimeVariants, []string{
		"windows-x64-baseline",
		"windows-x64-avx",
	})
}

func TestClassifyInsufficientMemoryAsUnsupported(t *testing.T) {
	profile := fixtureProfile((8<<30)-1, 3<<30, "avx2")

	got := Classify(profile)

	if got.Level != contracts.SupportUnsupported {
		t.Fatalf("Level = %q, want unsupported", got.Level)
	}
	if len(got.Reasons) == 0 {
		t.Fatal("unsupported classification has no reason")
	}
}

func TestNormalizeCPUFlagsIncludesNativeWindowsFeatures(t *testing.T) {
	got := normalizeCPUFlags(nil, x86Features{
		SSE42: true,
		AVX:   true,
		AVX2:  true,
		FMA:   true,
		F16C:  true,
		BMI2:  true,
	})

	assertStrings(t, got, []string{"avx", "avx2", "bmi2", "f16c", "fma", "sse4.2"})
}

func assertStrings(t *testing.T, got, want []string) {
	t.Helper()
	if len(got) != len(want) {
		t.Fatalf("got %v, want %v", got, want)
	}
	for index := range want {
		if got[index] != want[index] {
			t.Fatalf("got %v, want %v", got, want)
		}
	}
}
