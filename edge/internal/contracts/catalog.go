package contracts

const (
	CatalogSchemaV1      = "catalog.agentmuru.dev/v1"
	MaximumArtifactBytes = uint64(700 * 1024 * 1024)
)

type Catalog struct {
	SchemaVersion    string     `json:"schema_version"`
	Revision         string     `json:"revision"`
	MaxArtifactBytes uint64     `json:"max_artifact_bytes"`
	Artifacts        []Artifact `json:"artifacts"`
}

type Artifact struct {
	ID                 string      `json:"id"`
	ModelID            string      `json:"model_id"`
	Revision           string      `json:"revision"`
	Format             string      `json:"format"`
	URL                string      `json:"url"`
	SizeBytes          uint64      `json:"size_bytes"`
	SHA256             string      `json:"sha256"`
	RuntimeVariants    []string    `json:"runtime_variants"`
	MinimumMemoryBytes uint64      `json:"minimum_memory_bytes"`
	License            LicenseInfo `json:"license"`
}

type LicenseInfo struct {
	ID         string `json:"id"`
	Gated      bool   `json:"gated"`
	LicenseURL string `json:"license_url"`
}

func (catalog Catalog) Compatible(profile HardwareProfile) []Artifact {
	available := make(map[string]struct{}, len(profile.RuntimeVariants))
	for _, variant := range profile.RuntimeVariants {
		available[variant] = struct{}{}
	}
	result := make([]Artifact, 0, len(catalog.Artifacts))
	for _, artifact := range catalog.Artifacts {
		if artifact.MinimumMemoryBytes > profile.Memory.TotalBytes {
			continue
		}
		compatible := false
		for _, variant := range artifact.RuntimeVariants {
			if _, ok := available[variant]; ok {
				compatible = true
				break
			}
		}
		if compatible {
			result = append(result, artifact)
		}
	}
	return result
}
