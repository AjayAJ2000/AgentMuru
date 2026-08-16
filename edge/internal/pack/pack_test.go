package pack

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

func TestLoadRequiresChecksumManifest(t *testing.T) {
	root := filepath.Join(t.TempDir(), "pack")
	if err := Export(root, fixturePack()); err != nil {
		t.Fatal(err)
	}
	if err := os.Remove(filepath.Join(root, "checksums.txt")); err != nil {
		t.Fatal(err)
	}
	if _, err := Load(root); err == nil || !strings.Contains(err.Error(), "checksum") {
		t.Fatalf("Load() error = %v, want required checksum error", err)
	}
}

func TestLoadRequiresChecksumsForEveryRuntimeContractFile(t *testing.T) {
	root := filepath.Join(t.TempDir(), "pack")
	if err := Export(root, fixturePack()); err != nil {
		t.Fatal(err)
	}
	checksumPath := filepath.Join(root, "checksums.txt")
	data, err := os.ReadFile(checksumPath)
	if err != nil {
		t.Fatal(err)
	}
	lines := strings.Split(strings.TrimSpace(string(data)), "\n")
	if err := os.WriteFile(checksumPath, []byte(strings.Join(lines[1:], "\n")+"\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	if _, err := Load(root); err == nil || !strings.Contains(err.Error(), "missing checksum") {
		t.Fatalf("Load() error = %v, want missing checksum error", err)
	}
}

func TestValidateRejectsCapabilityMissingFromPolicy(t *testing.T) {
	value := fixturePack()
	value.Actions[0].Capabilities = []string{"fs.write"}
	violations := Validate(value)
	if !hasViolation(violations, "undeclared_capability") {
		t.Fatalf("violations = %#v, want undeclared_capability", violations)
	}
}

func TestValidateRequiresEveryEvaluationCategory(t *testing.T) {
	value := fixturePack()
	value.Evals = value.Evals[:1]
	violations := Validate(value)
	if !hasViolation(violations, "missing_eval_category") {
		t.Fatalf("violations = %#v, want missing_eval_category", violations)
	}
}

func fixturePack() contracts.AgentPack {
	return contracts.AgentPack{
		Manifest: contracts.PackManifest{SchemaVersion: contracts.AgentPackSchemaV1, ID: "fixture", Version: "1.0.0", EntryAgent: "router", MaxHops: 4, Effects: "simulate"},
		Agents:   []contracts.AgentSpec{{ID: "router", Actions: []string{"search_files"}}},
		Actions:  []contracts.PackAction{{ID: "search_files", OwnerAgent: "router", InputSchema: map[string]any{"type": "object"}, OutputSchema: map[string]any{"type": "object"}, Capabilities: []string{"fs.read"}}},
		Policy:   contracts.PackPolicy{Capabilities: map[string][]string{"fs.read": {"C:/fixture"}}, NetworkMode: "offline"},
		Evals: []contracts.PackEvalCase{
			{ID: "a", Category: "accepted", Input: "find notes", ExpectedAction: "search_files"},
			{ID: "b", Category: "ambiguous", Input: "maybe"},
			{ID: "c", Category: "rejected", Input: "unknown"},
			{ID: "d", Category: "unsafe", Input: "delete everything"},
		},
	}
}

func hasViolation(values []Violation, code string) bool {
	for _, value := range values {
		if value.Code == code {
			return true
		}
	}
	return false
}
