package pack

import (
	"fmt"
	"regexp"
	"sort"
	"strings"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

type Violation struct {
	Code    string `json:"code"`
	Path    string `json:"path"`
	Message string `json:"message"`
}

var packIDPattern = regexp.MustCompile(`^[a-z][a-z0-9-]{0,63}$`)
var actionIDPattern = regexp.MustCompile(`^[a-z][a-z0-9_]{0,63}$`)

func Validate(value contracts.AgentPack) []Violation {
	violations := []Violation{}
	add := func(code, path, message string) {
		violations = append(violations, Violation{Code: code, Path: path, Message: message})
	}
	if value.Manifest.SchemaVersion != contracts.AgentPackSchemaV1 {
		add("unsupported_schema", "manifest.schema_version", "agent-pack v1 is required")
	}
	if !packIDPattern.MatchString(value.Manifest.ID) || value.Manifest.Version == "" {
		add("invalid_manifest", "manifest", "stable id and version are required")
	}
	if value.Manifest.MaxHops < 1 || value.Manifest.MaxHops > 32 {
		add("invalid_hop_limit", "manifest.max_hops", "max_hops must be 1 through 32")
	}
	if value.Manifest.Effects != "simulate" && value.Manifest.Effects != "execute" {
		add("invalid_effect_mode", "manifest.effects", "effects must be simulate or execute")
	}
	agents := map[string]contracts.AgentSpec{}
	for index, agent := range value.Agents {
		if _, duplicate := agents[agent.ID]; duplicate || !packIDPattern.MatchString(agent.ID) {
			add("invalid_agent", fmt.Sprintf("agents[%d]", index), "agent ids must be unique and stable")
		}
		agents[agent.ID] = agent
	}
	if _, ok := agents[value.Manifest.EntryAgent]; !ok {
		add("missing_entry_agent", "manifest.entry_agent", "entry agent does not exist")
	}
	for _, agent := range value.Agents {
		for _, target := range agent.Handoffs {
			if _, ok := agents[target]; !ok {
				add("broken_handoff", "agents."+agent.ID, "handoff target does not exist")
			}
		}
	}
	actions := map[string]contracts.PackAction{}
	assigned := map[string]bool{}
	for _, agent := range value.Agents {
		for _, action := range agent.Actions {
			assigned[action] = true
		}
	}
	for index, action := range value.Actions {
		path := fmt.Sprintf("actions[%d]", index)
		if _, duplicate := actions[action.ID]; duplicate || !actionIDPattern.MatchString(action.ID) {
			add("invalid_action", path, "action ids must be unique and stable")
		}
		actions[action.ID] = action
		if _, ok := agents[action.OwnerAgent]; !ok || !assigned[action.ID] {
			add("unassigned_action", path, "action must have an existing owner and agent assignment")
		}
		if len(action.InputSchema) == 0 || len(action.OutputSchema) == 0 {
			add("missing_action_schema", path, "strict input and output schemas are required")
		}
		for _, capability := range action.Capabilities {
			if _, ok := value.Policy.Capabilities[capability]; !ok {
				add("undeclared_capability", path+".capabilities", "policy does not grant "+capability)
			}
		}
		if containsSecretField(action.InputSchema) || containsSecretField(action.OutputSchema) {
			add("plaintext_secret_field", path, "secret-like schema fields are not allowed")
		}
	}
	for action := range assigned {
		if _, ok := actions[action]; !ok {
			add("missing_action", "agents.actions", "assigned action does not exist")
		}
	}
	categories := map[string]bool{}
	for _, eval := range value.Evals {
		categories[eval.Category] = true
	}
	for _, required := range []string{"accepted", "ambiguous", "rejected", "unsafe"} {
		if !categories[required] {
			add("missing_eval_category", "evals", "missing "+required+" cases")
		}
	}
	sort.Slice(violations, func(left, right int) bool {
		if violations[left].Code == violations[right].Code {
			return violations[left].Path < violations[right].Path
		}
		return violations[left].Code < violations[right].Code
	})
	return violations
}

func containsSecretField(value any) bool {
	switch typed := value.(type) {
	case map[string]any:
		for key, child := range typed {
			lower := strings.ToLower(key)
			if strings.Contains(lower, "password") || strings.Contains(lower, "secret") || strings.Contains(lower, "api_key") || containsSecretField(child) {
				return true
			}
		}
	case []any:
		for _, child := range typed {
			if containsSecretField(child) {
				return true
			}
		}
	}
	return false
}
