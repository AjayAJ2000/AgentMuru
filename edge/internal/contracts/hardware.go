package contracts

const HardwareSchemaV1 = "hardware.agentmuru.dev/v1"

type SupportLevel string

const (
	SupportSupported    SupportLevel = "supported"
	SupportExperimental SupportLevel = "experimental"
	SupportUnsupported  SupportLevel = "unsupported"
)

type HardwareProfile struct {
	SchemaVersion   string       `json:"schema_version"`
	OS              OSInfo       `json:"os"`
	CPU             CPUInfo      `json:"cpu"`
	Memory          MemoryInfo   `json:"memory"`
	Storage         StorageInfo  `json:"storage"`
	Terminal        TerminalInfo `json:"terminal"`
	RuntimeVariants []string     `json:"runtime_variants"`
	Support         SupportInfo  `json:"support"`
}

type OSInfo struct {
	Name         string `json:"name"`
	Version      string `json:"version"`
	Architecture string `json:"architecture"`
}

type CPUInfo struct {
	Vendor        string   `json:"vendor"`
	Model         string   `json:"model"`
	PhysicalCores int      `json:"physical_cores"`
	LogicalCores  int      `json:"logical_cores"`
	Flags         []string `json:"flags"`
}

type MemoryInfo struct {
	TotalBytes     uint64 `json:"total_bytes"`
	AvailableBytes uint64 `json:"available_bytes"`
}

type StorageInfo struct {
	CachePath string `json:"cache_path"`
	FreeBytes uint64 `json:"free_bytes"`
}

type TerminalInfo struct {
	Interactive bool `json:"interactive"`
	TrueColor   bool `json:"true_color"`
	Mouse       bool `json:"mouse"`
	Width       int  `json:"width"`
}

type SupportInfo struct {
	Level   SupportLevel `json:"level"`
	Reasons []string     `json:"reasons"`
}
