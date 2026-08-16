package cli

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"testing"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

func TestDoctorJSONEmitsOnlyStableProfile(t *testing.T) {
	var out bytes.Buffer
	profile := contracts.HardwareProfile{
		SchemaVersion: contracts.HardwareSchemaV1,
		OS:            contracts.OSInfo{Name: "windows", Version: "11", Architecture: "amd64"},
		CPU: contracts.CPUInfo{
			Vendor: "GenuineIntel", Model: "fixture", PhysicalCores: 2, LogicalCores: 2,
		},
		Memory:  contracts.MemoryInfo{TotalBytes: 8 << 30, AvailableBytes: 4 << 30},
		Storage: contracts.StorageInfo{CachePath: `C:\cache`, FreeBytes: 3 << 30},
		Terminal: contracts.TerminalInfo{
			Interactive: true, TrueColor: true, Mouse: true, Width: 120,
		},
		RuntimeVariants: []string{"windows-x64-baseline"},
		Support: contracts.SupportInfo{
			Level: contracts.SupportExperimental, Reasons: []string{"fixture"},
		},
	}
	cmd := NewRoot(Dependencies{
		Version: "test", Out: &out, ErrOut: io.Discard,
		OpenWorkspace: func() error { return nil },
		DiscoverHardware: func(context.Context) (contracts.HardwareProfile, error) {
			return profile, nil
		},
	})
	cmd.SetArgs([]string{"doctor", "--json"})

	if err := cmd.ExecuteContext(context.Background()); err != nil {
		t.Fatalf("ExecuteContext() error = %v", err)
	}
	var got contracts.HardwareProfile
	if err := json.Unmarshal(out.Bytes(), &got); err != nil {
		t.Fatalf("doctor output is not JSON: %v\n%s", err, out.String())
	}
	if got.SchemaVersion != contracts.HardwareSchemaV1 {
		t.Fatalf("SchemaVersion = %q", got.SchemaVersion)
	}
}
