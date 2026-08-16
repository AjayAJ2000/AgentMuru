package contracts

import "time"

type Event struct {
	ID        string         `json:"id"`
	Type      string         `json:"type"`
	Timestamp time.Time      `json:"timestamp"`
	SessionID string         `json:"session_id"`
	Sequence  uint64         `json:"sequence"`
	RunID     *string        `json:"run_id"`
	TraceID   *string        `json:"trace_id"`
	ParentID  *string        `json:"parent_id"`
	Payload   map[string]any `json:"payload"`
}
