package eval

import (
	"errors"
	"testing"
	"time"
)

func TestUnsafeExecutionFailsCandidateEvenWhenAccuracyPasses(t *testing.T) {
	report := Report{CandidateID: "unsafe", ActionAccuracy: 0.99, SchemaValidity: 1, UnsafeExecutions: 1, ArtifactBytes: 300 << 20, PeakWorkingSetBytes: 1 << 30}
	result := Evaluate(report, DefaultThresholds())
	if result.Passed || !contains(result.Failures, "unsafe_execution") {
		t.Fatalf("gate result = %#v", result)
	}
}

func TestSelectChoosesSmallestPassingArtifactBeforeLatency(t *testing.T) {
	slowSmall := Report{CandidateID: "small", Passed: true, ArtifactBytes: 350 << 20, WarmP95: 2200 * time.Millisecond}
	fastLarge := Report{CandidateID: "large", Passed: true, ArtifactBytes: 620 << 20, WarmP95: 900 * time.Millisecond}
	selection, err := Select([]Report{fastLarge, slowSmall})
	if err != nil {
		t.Fatal(err)
	}
	if selection.CandidateID != "small" {
		t.Fatalf("selection = %#v", selection)
	}
}

func TestSelectRejectsAllFailingCandidates(t *testing.T) {
	_, err := Select([]Report{{CandidateID: "failed"}})
	if !errors.Is(err, ErrNoPassingCandidate) {
		t.Fatalf("Select() error = %v", err)
	}
}

func contains(values []string, value string) bool {
	for _, candidate := range values {
		if candidate == value {
			return true
		}
	}
	return false
}
