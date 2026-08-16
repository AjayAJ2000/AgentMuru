package events

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"sync"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

var sessionIDPattern = regexp.MustCompile(`^[A-Za-z0-9._-]+$`)

type JSONLStore struct {
	root  string
	mu    sync.Mutex
	locks map[string]*sync.Mutex
}

func NewJSONLStore(root string) *JSONLStore {
	return &JSONLStore{root: root, locks: make(map[string]*sync.Mutex)}
}

func (store *JSONLStore) sessionLock(sessionID string) *sync.Mutex {
	store.mu.Lock()
	defer store.mu.Unlock()
	lock := store.locks[sessionID]
	if lock == nil {
		lock = &sync.Mutex{}
		store.locks[sessionID] = lock
	}
	return lock
}

func (store *JSONLStore) path(sessionID string) (string, error) {
	if !sessionIDPattern.MatchString(sessionID) {
		return "", fmt.Errorf("invalid session id %q", sessionID)
	}
	return filepath.Join(store.root, sessionID+".jsonl"), nil
}

func (store *JSONLStore) Append(ctx context.Context, event contracts.Event) (contracts.Event, error) {
	if err := ctx.Err(); err != nil {
		return contracts.Event{}, err
	}
	if err := validateEvent(event); err != nil {
		return contracts.Event{}, err
	}
	if event.Payload == nil {
		event.Payload = map[string]any{}
	}
	path, err := store.path(event.SessionID)
	if err != nil {
		return contracts.Event{}, err
	}
	lock := store.sessionLock(event.SessionID)
	lock.Lock()
	defer lock.Unlock()

	if err := os.MkdirAll(store.root, 0o700); err != nil {
		return contracts.Event{}, err
	}
	file, err := os.OpenFile(path, os.O_CREATE|os.O_RDWR, 0o600)
	if err != nil {
		return contracts.Event{}, err
	}
	defer file.Close()
	data, err := io.ReadAll(file)
	if err != nil {
		return contracts.Event{}, err
	}
	existing, validLength, err := parseLog(data)
	if err != nil {
		return contracts.Event{}, err
	}
	if err := file.Truncate(int64(validLength)); err != nil {
		return contracts.Event{}, err
	}
	if _, err := file.Seek(0, io.SeekEnd); err != nil {
		return contracts.Event{}, err
	}
	event.Sequence = 1
	if len(existing) > 0 {
		event.Sequence = existing[len(existing)-1].Sequence + 1
	}
	event.Timestamp = event.Timestamp.UTC()
	encoded, err := json.Marshal(event)
	if err != nil {
		return contracts.Event{}, err
	}
	encoded = append(encoded, '\n')
	if _, err := file.Write(encoded); err != nil {
		return contracts.Event{}, err
	}
	if err := file.Sync(); err != nil {
		return contracts.Event{}, err
	}
	return event, nil
}

func (store *JSONLStore) Replay(ctx context.Context, sessionID string, after uint64) ([]contracts.Event, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	path, err := store.path(sessionID)
	if err != nil {
		return nil, err
	}
	lock := store.sessionLock(sessionID)
	lock.Lock()
	defer lock.Unlock()
	data, err := os.ReadFile(path)
	if errors.Is(err, os.ErrNotExist) {
		return []contracts.Event{}, nil
	}
	if err != nil {
		return nil, err
	}
	events, _, err := parseLog(data)
	if err != nil {
		return nil, err
	}
	result := make([]contracts.Event, 0, len(events))
	for _, event := range events {
		if event.Sequence > after {
			result = append(result, event)
		}
	}
	return result, nil
}

func parseLog(data []byte) ([]contracts.Event, int, error) {
	validLength := len(data)
	if len(data) > 0 && data[len(data)-1] != '\n' {
		lastNewline := bytes.LastIndexByte(data, '\n')
		if lastNewline < 0 {
			return []contracts.Event{}, 0, nil
		}
		validLength = lastNewline + 1
		data = data[:validLength]
	}
	lines := bytes.Split(data, []byte{'\n'})
	events := make([]contracts.Event, 0, len(lines))
	var previous uint64
	for index, line := range lines {
		if len(bytes.TrimSpace(line)) == 0 {
			continue
		}
		var event contracts.Event
		if err := json.Unmarshal(line, &event); err != nil {
			return nil, 0, fmt.Errorf("decode event line %d: %w", index+1, err)
		}
		if event.Sequence != previous+1 {
			return nil, 0, fmt.Errorf("event line %d has non-monotonic sequence %d", index+1, event.Sequence)
		}
		previous = event.Sequence
		events = append(events, event)
	}
	return events, validLength, nil
}

func validateEvent(event contracts.Event) error {
	if event.ID == "" || event.Type == "" || event.SessionID == "" {
		return errors.New("event id, type, and session id are required")
	}
	if event.Timestamp.IsZero() {
		return errors.New("event timestamp is required")
	}
	if event.Sequence != 0 {
		return errors.New("event sequence is assigned by the store")
	}
	if _, err := json.Marshal(event.Payload); err != nil {
		return fmt.Errorf("event payload must be JSON serializable: %w", err)
	}
	return nil
}
