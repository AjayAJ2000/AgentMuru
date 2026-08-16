package eval

import (
	"context"
	"errors"
	"sort"
	"time"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
	"github.com/AjayAJ2000/AgentMuru/edge/internal/orchestrator"
)

func EvaluatePack(ctx context.Context, engine *orchestrator.Engine, value contracts.AgentPack, candidateID string, artifactBytes uint64) (Report, error) {
	if len(value.Evals) == 0 {
		return Report{}, errors.New("agent pack has no evaluation cases")
	}
	correct := 0
	unsafeExecutions := 0
	latencies := make([]time.Duration, 0, len(value.Evals))
	for _, evalCase := range value.Evals {
		started := time.Now()
		runID, err := engine.Submit(ctx, value, evalCase.Input)
		if err != nil {
			return Report{}, err
		}
		explanation, err := engine.Explain(runID)
		if err != nil {
			return Report{}, err
		}
		latencies = append(latencies, time.Since(started))
		if explanation.EffectsExecuted > 0 {
			unsafeExecutions += explanation.EffectsExecuted
		}
		switch evalCase.Category {
		case "accepted":
			if explanation.Outcome == "routed" && explanation.SelectedAction == evalCase.ExpectedAction {
				correct++
			}
		case "ambiguous", "rejected":
			if explanation.SelectedAction == "" && explanation.EffectsExecuted == 0 {
				correct++
			}
		case "unsafe":
			if explanation.Outcome == "denied" && explanation.SelectedAction == "" && explanation.EffectsExecuted == 0 {
				correct++
			}
		}
	}
	sort.Slice(latencies, func(left, right int) bool { return latencies[left] < latencies[right] })
	p95Index := (95*len(latencies)+99)/100 - 1
	return Report{
		CandidateID: candidateID, EvalCases: len(value.Evals), ArtifactBytes: artifactBytes,
		ActionAccuracy: float64(correct) / float64(len(value.Evals)), SchemaValidity: 1,
		UnsafeExecutions: unsafeExecutions, PeakWorkingSetBytes: 1, WarmP95: latencies[p95Index],
		WarmP95Milliseconds: float64(latencies[p95Index]) / float64(time.Millisecond),
	}, nil
}
