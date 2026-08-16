package events

import (
	"context"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

type spyStore struct {
	persisted bool
}

func (store *spyStore) Append(_ context.Context, event contracts.Event) (contracts.Event, error) {
	store.persisted = true
	event.Sequence = 1
	return event, nil
}

func (store *spyStore) Replay(_ context.Context, _ string, _ uint64) ([]contracts.Event, error) {
	return nil, nil
}

func fixtureEvent() contracts.Event {
	return contracts.Event{
		ID:        "event-1",
		Type:      "session.started",
		Timestamp: time.Date(2026, 8, 17, 0, 0, 0, 0, time.UTC),
		SessionID: "session-1",
		Payload:   map[string]any{"title": "Fixture"},
	}
}

func TestPublishAppendsBeforeSubscriberReceives(t *testing.T) {
	store := &spyStore{}
	bus := NewBus(store)
	stream, cancel := bus.Subscribe("session-1", 1)
	defer cancel()

	appended, err := bus.Publish(context.Background(), fixtureEvent())
	if err != nil {
		t.Fatalf("Publish() error = %v", err)
	}
	if !store.persisted {
		t.Fatal("subscriber notification happened before persistence")
	}
	select {
	case got := <-stream:
		if got.Sequence != appended.Sequence || got.Sequence != 1 {
			t.Fatalf("subscriber sequence = %d, appended = %d", got.Sequence, appended.Sequence)
		}
	case <-time.After(time.Second):
		t.Fatal("subscriber did not receive persisted event")
	}
}

func TestJSONLStoreAssignsMonotonicSequenceAndReplays(t *testing.T) {
	store := NewJSONLStore(t.TempDir())
	ctx := context.Background()

	first, err := store.Append(ctx, fixtureEvent())
	if err != nil {
		t.Fatalf("first Append() error = %v", err)
	}
	secondEvent := fixtureEvent()
	secondEvent.ID = "event-2"
	second, err := store.Append(ctx, secondEvent)
	if err != nil {
		t.Fatalf("second Append() error = %v", err)
	}
	if first.Sequence != 1 || second.Sequence != 2 {
		t.Fatalf("sequences = %d, %d", first.Sequence, second.Sequence)
	}

	replayed, err := store.Replay(ctx, "session-1", 1)
	if err != nil {
		t.Fatalf("Replay() error = %v", err)
	}
	if len(replayed) != 1 || replayed[0].ID != "event-2" {
		t.Fatalf("Replay() = %#v", replayed)
	}
}

func TestJSONLStoreIgnoresOneTruncatedTail(t *testing.T) {
	root := t.TempDir()
	store := NewJSONLStore(root)
	if _, err := store.Append(context.Background(), fixtureEvent()); err != nil {
		t.Fatalf("Append() error = %v", err)
	}
	path := filepath.Join(root, "session-1.jsonl")
	file, err := os.OpenFile(path, os.O_APPEND|os.O_WRONLY, 0)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := file.WriteString(`{"id":"partial"`); err != nil {
		t.Fatal(err)
	}
	if err := file.Close(); err != nil {
		t.Fatal(err)
	}

	replayed, err := store.Replay(context.Background(), "session-1", 0)
	if err != nil {
		t.Fatalf("Replay() error = %v", err)
	}
	if len(replayed) != 1 || replayed[0].Sequence != 1 {
		t.Fatalf("Replay() = %#v", replayed)
	}
}

func TestJSONLStoreNormalizesLocalTimeAndNilPayload(t *testing.T) {
	store := NewJSONLStore(t.TempDir())
	event := fixtureEvent()
	event.Timestamp = time.Now()
	event.Payload = nil

	got, err := store.Append(context.Background(), event)
	if err != nil {
		t.Fatalf("Append() error = %v", err)
	}
	if got.Timestamp.Location() != time.UTC {
		t.Fatalf("timestamp location = %v, want UTC", got.Timestamp.Location())
	}
	if got.Payload == nil {
		t.Fatal("payload remained nil")
	}
}
