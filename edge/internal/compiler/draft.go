package compiler

type Draft struct {
	ID               string              `json:"id"`
	Goal             string              `json:"goal"`
	Actions          []DraftAction       `json:"actions"`
	Examples         []Example           `json:"examples"`
	CapabilityScopes map[string][]string `json:"capability_scopes"`
}

type DraftAction struct {
	ID                   string         `json:"id"`
	Description          string         `json:"description"`
	InputSchema          map[string]any `json:"input_schema"`
	OutputSchema         map[string]any `json:"output_schema"`
	Capabilities         []string       `json:"capabilities"`
	StructuredExtraction bool           `json:"structured_extraction"`
}

type Example struct {
	Input          string `json:"input"`
	ExpectedAction string `json:"expected_action"`
}

type Question struct {
	Code   string `json:"code"`
	Prompt string `json:"prompt"`
}
