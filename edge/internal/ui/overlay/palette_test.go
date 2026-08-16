package overlay

import (
	"reflect"
	"testing"
)

func TestFilterActionsUsesFuzzySubsequenceAndStableOrdering(t *testing.T) {
	got := FilterActions("er")
	want := []string{"benchmark", "permissions"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("FilterActions(er) = %v, want %v", got, want)
	}
}

func TestPaletteContainsEveryPublicAction(t *testing.T) {
	want := []string{"benchmark", "create", "doctor", "explain", "help", "models", "permissions", "run", "settings"}
	if !reflect.DeepEqual(PaletteActions, want) {
		t.Fatalf("PaletteActions = %v, want %v", PaletteActions, want)
	}
}
