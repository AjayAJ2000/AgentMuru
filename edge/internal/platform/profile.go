package platform

import (
	"context"
	"errors"
	"os"
	"path/filepath"
	"runtime"
	"sort"
	"strings"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/config"
	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
	"github.com/shirou/gopsutil/v4/cpu"
	"github.com/shirou/gopsutil/v4/disk"
	"github.com/shirou/gopsutil/v4/host"
	"github.com/shirou/gopsutil/v4/mem"
	syscpu "golang.org/x/sys/cpu"
)

const (
	minimumMemory = uint64(8 << 30)
	minimumDisk   = uint64(2 << 30)
)

type Classification struct {
	Level           contracts.SupportLevel
	Reasons         []string
	RuntimeVariants []string
}

func Classify(profile contracts.HardwareProfile) Classification {
	variants := []string{"windows-x64-baseline"}
	flags := make(map[string]bool, len(profile.CPU.Flags))
	for _, flag := range profile.CPU.Flags {
		flags[flag] = true
	}
	if flags["avx"] || flags["avx2"] {
		variants = append(variants, "windows-x64-avx")
	}
	if flags["avx2"] {
		variants = append(variants, "windows-x64-avx2")
	}

	reasons := make([]string, 0, 3)
	level := contracts.SupportSupported
	if profile.OS.Name != "windows" || profile.OS.Architecture != "amd64" {
		level = contracts.SupportUnsupported
		reasons = append(reasons, "the first release supports Windows x64 only")
	}
	if profile.Memory.TotalBytes < minimumMemory {
		level = contracts.SupportUnsupported
		reasons = append(reasons, "at least 8 GB of installed RAM is required")
	}
	if profile.Storage.FreeBytes < minimumDisk {
		level = contracts.SupportUnsupported
		reasons = append(reasons, "at least 2 GB of free cache storage is required")
	}
	if level != contracts.SupportUnsupported && !flags["avx2"] {
		level = contracts.SupportExperimental
		reasons = append(reasons, "AVX2 is unavailable; reference qualification is required")
	}
	if len(reasons) == 0 {
		reasons = append(reasons, "hardware meets the first-release compatibility floor")
	}
	return Classification{Level: level, Reasons: reasons, RuntimeVariants: variants}
}

func Discover(ctx context.Context, paths config.Paths) (contracts.HardwareProfile, error) {
	hostInfo, err := host.InfoWithContext(ctx)
	if err != nil {
		return contracts.HardwareProfile{}, err
	}
	memory, err := mem.VirtualMemoryWithContext(ctx)
	if err != nil {
		return contracts.HardwareProfile{}, err
	}
	logical, err := cpu.CountsWithContext(ctx, true)
	if err != nil {
		return contracts.HardwareProfile{}, err
	}
	physical, err := cpu.CountsWithContext(ctx, false)
	if err != nil {
		return contracts.HardwareProfile{}, err
	}
	cpuInfo, err := cpu.InfoWithContext(ctx)
	if err != nil {
		return contracts.HardwareProfile{}, err
	}
	storageRoot, err := existingAncestor(paths.Cache)
	if err != nil {
		return contracts.HardwareProfile{}, err
	}
	storage, err := disk.UsageWithContext(ctx, storageRoot)
	if err != nil {
		return contracts.HardwareProfile{}, err
	}

	processor := cpu.InfoStat{}
	if len(cpuInfo) > 0 {
		processor = cpuInfo[0]
	}
	profile := contracts.HardwareProfile{
		SchemaVersion: contracts.HardwareSchemaV1,
		OS: contracts.OSInfo{
			Name:         runtime.GOOS,
			Version:      hostInfo.PlatformVersion,
			Architecture: runtime.GOARCH,
		},
		CPU: contracts.CPUInfo{
			Vendor:        processor.VendorID,
			Model:         processor.ModelName,
			PhysicalCores: physical,
			LogicalCores:  logical,
			Flags:         normalizeCPUFlags(processor.Flags, nativeX86Features()),
		},
		Memory: contracts.MemoryInfo{
			TotalBytes:     memory.Total,
			AvailableBytes: memory.Available,
		},
		Storage: contracts.StorageInfo{
			CachePath: paths.Cache,
			FreeBytes: storage.Free,
		},
		Terminal: DiscoverTerminal(os.Stdout),
	}
	classification := Classify(profile)
	profile.RuntimeVariants = classification.RuntimeVariants
	profile.Support = contracts.SupportInfo{
		Level: classification.Level, Reasons: classification.Reasons,
	}
	return profile, nil
}

type x86Features struct {
	SSE42 bool
	AVX   bool
	AVX2  bool
	FMA   bool
	F16C  bool
	BMI2  bool
}

func nativeX86Features() x86Features {
	return x86Features{
		SSE42: syscpu.X86.HasSSE42,
		AVX:   syscpu.X86.HasAVX,
		AVX2:  syscpu.X86.HasAVX2,
		FMA:   syscpu.X86.HasFMA,
		BMI2:  syscpu.X86.HasBMI2,
	}
}

func normalizeCPUFlags(flags []string, features x86Features) []string {
	normalized := make(map[string]struct{}, len(flags))
	for _, flag := range flags {
		flag = strings.ToLower(strings.TrimSpace(flag))
		flag = strings.ReplaceAll(flag, "sse4_", "sse4.")
		if flag != "" {
			normalized[flag] = struct{}{}
		}
	}
	featureFlags := map[string]bool{
		"sse4.2": features.SSE42,
		"avx":    features.AVX,
		"avx2":   features.AVX2,
		"fma":    features.FMA,
		"f16c":   features.F16C,
		"bmi2":   features.BMI2,
	}
	for flag, enabled := range featureFlags {
		if enabled {
			normalized[flag] = struct{}{}
		}
	}
	result := make([]string, 0, len(normalized))
	for flag := range normalized {
		result = append(result, flag)
	}
	sort.Strings(result)
	return result
}

func existingAncestor(path string) (string, error) {
	current := filepath.Clean(path)
	for {
		if _, err := os.Stat(current); err == nil {
			return current, nil
		} else if !errors.Is(err, os.ErrNotExist) {
			return "", err
		}
		parent := filepath.Dir(current)
		if parent == current {
			return "", errors.New("no existing storage ancestor")
		}
		current = parent
	}
}
