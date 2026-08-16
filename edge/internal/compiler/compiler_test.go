package compiler

import "testing"

func TestActionRouterUsesOneLogicalAgentUntilSpecializationIsRequired(t *testing.T) {
	draft := Draft{
		ID: "notes", Goal: "Route note tasks", Examples: []Example{{Input: "find notes", ExpectedAction: "search_files"}, {Input: "summarize note", ExpectedAction: "summarize_text"}},
		Actions:          []DraftAction{{ID: "search_files", InputSchema: objectSchema(), OutputSchema: objectSchema(), Capabilities: []string{"fs.read"}}, {ID: "summarize_text", InputSchema: objectSchema(), OutputSchema: objectSchema()}},
		CapabilityScopes: map[string][]string{"fs.read": {"C:/notes"}},
	}
	pack, questions, err := Compile(draft)
	if err != nil {
		t.Fatal(err)
	}
	if len(questions) != 0 || len(pack.Agents) != 1 {
		t.Fatalf("agents = %d, questions = %#v", len(pack.Agents), questions)
	}
}

func TestCompilerAddsWebVerifierOnlyWhenRequested(t *testing.T) {
	draft := Draft{ID: "research", Goal: "Research facts", Examples: []Example{{Input: "verify", ExpectedAction: "web_lookup"}, {Input: "check", ExpectedAction: "web_lookup"}}, Actions: []DraftAction{{ID: "web_lookup", InputSchema: objectSchema(), OutputSchema: objectSchema(), Capabilities: []string{"web.read"}}}, CapabilityScopes: map[string][]string{"web.read": {"example.com"}}}
	pack, _, err := Compile(draft)
	if err != nil {
		t.Fatal(err)
	}
	if len(pack.Agents) != 2 || pack.Agents[1].ID != "web-verifier" {
		t.Fatalf("agents = %#v", pack.Agents)
	}
}

func objectSchema() map[string]any { return map[string]any{"type": "object"} }
