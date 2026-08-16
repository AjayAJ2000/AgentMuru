package inference

import (
	"context"
	"errors"
	"reflect"
	"sync"
	"testing"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

func TestLowMemoryBudgetUnloadsBeforeLoadingSpecialist(t *testing.T) {
	loader := &recordingLoader{}
	manager := NewManager([]ModelSpec{{ID: "router", EstimatedMemoryBytes: 1 << 30}, {ID: "extractor", EstimatedMemoryBytes: 1 << 30}}, loader)
	budget := Budget{MaxResidentModels: 1, MaxMemoryBytes: 2 << 30}
	first, err := manager.Acquire(context.Background(), "router", budget)
	if err != nil {
		t.Fatal(err)
	}
	first.Release()
	if _, err := manager.Acquire(context.Background(), "extractor", budget); err != nil {
		t.Fatal(err)
	}
	want := []string{"load:router", "unload:router", "load:extractor"}
	if got := loader.log(); !reflect.DeepEqual(got, want) {
		t.Fatalf("loader log = %v, want %v", got, want)
	}
}

func TestManagerNeverEvictsLeasedModel(t *testing.T) {
	loader := &recordingLoader{}
	manager := NewManager([]ModelSpec{{ID: "router", EstimatedMemoryBytes: 1 << 30}, {ID: "extractor", EstimatedMemoryBytes: 1 << 30}}, loader)
	budget := Budget{MaxResidentModels: 1, MaxMemoryBytes: 2 << 30}
	lease, err := manager.Acquire(context.Background(), "router", budget)
	if err != nil {
		t.Fatal(err)
	}
	defer lease.Release()
	if _, err := manager.Acquire(context.Background(), "extractor", budget); !errors.Is(err, ErrNoEvictableModel) {
		t.Fatalf("Acquire() error = %v, want ErrNoEvictableModel", err)
	}
	if got := loader.log(); !reflect.DeepEqual(got, []string{"load:router"}) {
		t.Fatalf("loader log = %v", got)
	}
}

func TestManagerRejectsModelLargerThanBudget(t *testing.T) {
	manager := NewManager([]ModelSpec{{ID: "large", EstimatedMemoryBytes: 4 << 30}}, &recordingLoader{})
	_, err := manager.Acquire(context.Background(), "large", Budget{MaxResidentModels: 1, MaxMemoryBytes: 2 << 30})
	if !errors.Is(err, ErrModelExceedsBudget) {
		t.Fatalf("Acquire() error = %v, want ErrModelExceedsBudget", err)
	}
}

func TestDefaultBudgetAllowsOneResidentModelOnEightGiB(t *testing.T) {
	budget := DefaultBudget(contracts.HardwareProfile{Memory: contracts.MemoryInfo{TotalBytes: 8 << 30, AvailableBytes: 6 << 30}})
	if budget.MaxResidentModels != 1 {
		t.Fatalf("MaxResidentModels = %d, want 1", budget.MaxResidentModels)
	}
}

type recordingLoader struct {
	mu      sync.Mutex
	actions []string
}

func (loader *recordingLoader) Load(_ context.Context, id string) error {
	loader.mu.Lock()
	defer loader.mu.Unlock()
	loader.actions = append(loader.actions, "load:"+id)
	return nil
}

func (loader *recordingLoader) Unload(_ context.Context, id string) error {
	loader.mu.Lock()
	defer loader.mu.Unlock()
	loader.actions = append(loader.actions, "unload:"+id)
	return nil
}

func (loader *recordingLoader) log() []string {
	loader.mu.Lock()
	defer loader.mu.Unlock()
	return append([]string(nil), loader.actions...)
}
