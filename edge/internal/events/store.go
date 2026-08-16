package events

import (
	"context"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

type Store interface {
	Append(context.Context, contracts.Event) (contracts.Event, error)
	Replay(context.Context, string, uint64) ([]contracts.Event, error)
}
