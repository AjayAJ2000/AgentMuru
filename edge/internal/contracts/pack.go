package contracts

const AgentPackSchemaV1 = "agent-pack.agentmuru.dev/v1"

type AgentPack struct {
	Manifest PackManifest   `json:"manifest"`
	Agents   []AgentSpec    `json:"agents"`
	Actions  []PackAction   `json:"actions"`
	Policy   PackPolicy     `json:"policy"`
	Evals    []PackEvalCase `json:"evals"`
}

type PackManifest struct {
	SchemaVersion string `json:"schema_version"`
	ID            string `json:"id"`
	Name          string `json:"name"`
	Version       string `json:"version"`
	EntryAgent    string `json:"entry_agent"`
	MaxHops       int    `json:"max_hops"`
	Effects       string `json:"effects"`
}

type AgentSpec struct {
	ID       string   `json:"id"`
	Role     string   `json:"role"`
	ModelID  string   `json:"model_id,omitempty"`
	Actions  []string `json:"actions"`
	Handoffs []string `json:"handoffs"`
}

type PackAction struct {
	ID           string         `json:"id"`
	Description  string         `json:"description"`
	OwnerAgent   string         `json:"owner_agent"`
	InputSchema  map[string]any `json:"input_schema"`
	OutputSchema map[string]any `json:"output_schema"`
	Capabilities []string       `json:"capabilities"`
	EffectClass  string         `json:"effect_class"`
}

type PackPolicy struct {
	Capabilities map[string][]string `json:"capabilities"`
	NetworkMode  string              `json:"network_mode"`
}

type PackEvalCase struct {
	ID             string `json:"id"`
	Category       string `json:"category"`
	Input          string `json:"input"`
	ExpectedAction string `json:"expected_action,omitempty"`
	ExpectedResult string `json:"expected_result,omitempty"`
}
