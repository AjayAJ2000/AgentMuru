package inference

import (
	"errors"
	"strings"
	"testing"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

func TestGrammarForIsDeterministicAndContainsOnlyDeclaredActions(t *testing.T) {
	actions := []contracts.ActionDescriptor{{Name: "write_note"}, {Name: "search_files"}}
	grammar, err := GrammarFor(actions)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(grammar, `action ::= "\"search_files\"" | "\"write_note\""`) {
		t.Fatalf("grammar action order is not deterministic:\n%s", grammar)
	}
	if strings.Contains(grammar, "delete_all") {
		t.Fatal("grammar contains an undeclared action")
	}
}

func TestGrammarForRejectsUnsafeActionNames(t *testing.T) {
	_, err := GrammarFor([]contracts.ActionDescriptor{{Name: `bad\"name`}})
	if !errors.Is(err, ErrInvalidActionDescriptor) {
		t.Fatalf("GrammarFor() error = %v, want ErrInvalidActionDescriptor", err)
	}
}
