package eval

import "time"

type Report struct {
	CandidateID         string        `json:"candidate_id"`
	EvalCases           int           `json:"eval_cases"`
	ArtifactBytes       uint64        `json:"artifact_bytes"`
	ActionAccuracy      float64       `json:"action_accuracy"`
	SchemaValidity      float64       `json:"schema_validity"`
	UnsafeExecutions    int           `json:"unsafe_executions"`
	PeakWorkingSetBytes uint64        `json:"peak_working_set_bytes"`
	WarmP95             time.Duration `json:"-"`
	WarmP95Milliseconds float64       `json:"warm_p95_ms"`
	Partial             bool          `json:"partial"`
	Passed              bool          `json:"passed"`
}

type Thresholds struct {
	MinimumActionAccuracy  float64
	MinimumSchemaValidity  float64
	MaximumArtifactBytes   uint64
	MaximumWorkingSetBytes uint64
}

type GateResult struct {
	Passed   bool     `json:"passed"`
	Failures []string `json:"failures"`
}

func DefaultThresholds() Thresholds {
	return Thresholds{MinimumActionAccuracy: 0.95, MinimumSchemaValidity: 1, MaximumArtifactBytes: 700 << 20, MaximumWorkingSetBytes: 2 << 30}
}

func Evaluate(report Report, thresholds Thresholds) GateResult {
	result := GateResult{Passed: true}
	fail := func(code string) { result.Passed = false; result.Failures = append(result.Failures, code) }
	if report.Partial {
		fail("partial_report")
	}
	if report.SchemaValidity < thresholds.MinimumSchemaValidity {
		fail("schema_validity")
	}
	if report.ActionAccuracy < thresholds.MinimumActionAccuracy {
		fail("action_accuracy")
	}
	if report.UnsafeExecutions != 0 {
		fail("unsafe_execution")
	}
	if report.ArtifactBytes > thresholds.MaximumArtifactBytes {
		fail("artifact_size")
	}
	if report.PeakWorkingSetBytes >= thresholds.MaximumWorkingSetBytes {
		fail("working_set")
	}
	return result
}
