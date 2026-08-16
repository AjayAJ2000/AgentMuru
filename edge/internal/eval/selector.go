package eval

import (
	"errors"
	"sort"
)

var ErrNoPassingCandidate = errors.New("no candidate passed every activation gate")

type Selection struct {
	CandidateID   string `json:"candidate_id"`
	ArtifactBytes uint64 `json:"artifact_bytes"`
}

func Select(reports []Report) (Selection, error) {
	passing := make([]Report, 0, len(reports))
	for _, report := range reports {
		if report.Passed {
			passing = append(passing, report)
		}
	}
	if len(passing) == 0 {
		return Selection{}, ErrNoPassingCandidate
	}
	sort.Slice(passing, func(left, right int) bool {
		if passing[left].ArtifactBytes != passing[right].ArtifactBytes {
			return passing[left].ArtifactBytes < passing[right].ArtifactBytes
		}
		if passing[left].WarmP95 != passing[right].WarmP95 {
			return passing[left].WarmP95 < passing[right].WarmP95
		}
		return passing[left].CandidateID < passing[right].CandidateID
	})
	return Selection{CandidateID: passing[0].CandidateID, ArtifactBytes: passing[0].ArtifactBytes}, nil
}
