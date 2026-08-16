package events

import (
	"context"
	"sync"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

type Bus struct {
	store Store
	mu    sync.Mutex
	next  uint64
	subs  map[string]map[uint64]chan contracts.Event
}

func NewBus(store Store) *Bus {
	return &Bus{store: store, subs: make(map[string]map[uint64]chan contracts.Event)}
}

func (bus *Bus) Subscribe(sessionID string, buffer int) (<-chan contracts.Event, func()) {
	if buffer < 1 {
		buffer = 1
	}
	stream := make(chan contracts.Event, buffer)
	bus.mu.Lock()
	bus.next++
	id := bus.next
	if bus.subs[sessionID] == nil {
		bus.subs[sessionID] = make(map[uint64]chan contracts.Event)
	}
	bus.subs[sessionID][id] = stream
	bus.mu.Unlock()
	var once sync.Once
	return stream, func() {
		once.Do(func() {
			bus.mu.Lock()
			delete(bus.subs[sessionID], id)
			if len(bus.subs[sessionID]) == 0 {
				delete(bus.subs, sessionID)
			}
			bus.mu.Unlock()
		})
	}
}

func (bus *Bus) Publish(ctx context.Context, event contracts.Event) (contracts.Event, error) {
	appended, err := bus.store.Append(ctx, event)
	if err != nil {
		return contracts.Event{}, err
	}
	bus.mu.Lock()
	streams := make([]chan contracts.Event, 0, len(bus.subs[event.SessionID]))
	for _, stream := range bus.subs[event.SessionID] {
		streams = append(streams, stream)
	}
	bus.mu.Unlock()
	for _, stream := range streams {
		select {
		case stream <- appended:
		case <-ctx.Done():
			return contracts.Event{}, ctx.Err()
		}
	}
	return appended, nil
}
