package contracts

type DecisionRequest struct {
	Messages        []DecisionMessage  `json:"messages"`
	Actions         []ActionDescriptor `json:"actions"`
	MaxOutputTokens int                `json:"max_output_tokens"`
}

type DecisionMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type ActionDescriptor struct {
	Name        string                        `json:"name"`
	Description string                        `json:"description"`
	Arguments   map[string]ArgumentDescriptor `json:"arguments"`
	Required    []string                      `json:"required"`
}

type ArgumentDescriptor struct {
	Type string `json:"type"`
	Enum []any  `json:"enum,omitempty"`
}

type ActionDecision struct {
	Action        string         `json:"action"`
	Arguments     map[string]any `json:"arguments"`
	AbstainReason string         `json:"abstain_reason,omitempty"`
}

type Usage struct {
	InputTokens  int `json:"input_tokens"`
	OutputTokens int `json:"output_tokens"`
}
