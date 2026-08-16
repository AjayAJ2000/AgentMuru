package cli

import (
	"encoding/json"
	"io"
	"os"
	"path/filepath"
	"testing"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/compiler"
	"github.com/AjayAJ2000/AgentMuru/edge/internal/pack"
)

func TestCreatePlainCompilesAValidatedPack(t *testing.T) {
	root := t.TempDir()
	draftPath := filepath.Join(root, "draft.json")
	output := filepath.Join(root, "pack")
	draft := compiler.Draft{ID: "notes", Goal: "Route note tasks", Examples: []compiler.Example{{Input: "find", ExpectedAction: "search_files"}, {Input: "locate", ExpectedAction: "search_files"}}, Actions: []compiler.DraftAction{{ID: "search_files", InputSchema: map[string]any{"type": "object"}, OutputSchema: map[string]any{"type": "object"}, Capabilities: []string{"fs.read"}}}, CapabilityScopes: map[string][]string{"fs.read": {"C:/notes"}}}
	data, _ := json.Marshal(draft)
	if err := os.WriteFile(draftPath, data, 0o600); err != nil {
		t.Fatal(err)
	}
	command := NewRoot(Dependencies{Version: "test", Out: io.Discard, ErrOut: io.Discard})
	command.SetArgs([]string{"create", "--from", draftPath, "--output", output, "--plain"})
	if err := command.Execute(); err != nil {
		t.Fatalf("Execute() error = %v", err)
	}
	if _, err := pack.Load(output); err != nil {
		t.Fatalf("created pack does not load: %v", err)
	}
}
