package contracts

type RuntimeVariant struct {
	ID               string   `json:"id"`
	OS               string   `json:"os"`
	Architecture     string   `json:"architecture"`
	RequiredCPUFlags []string `json:"required_cpu_flags"`
	Rank             int      `json:"rank"`
	Filename         string   `json:"filename"`
	SizeBytes        uint64   `json:"size_bytes"`
	SHA256           string   `json:"sha256"`
}
