package inference

import (
	"context"
	"errors"
	"fmt"
	"sync"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

var (
	ErrModelUnknown       = errors.New("model is not registered")
	ErrModelExceedsBudget = errors.New("model exceeds the memory budget")
	ErrNoEvictableModel   = errors.New("no idle model can be evicted")
)

type ModelSpec struct {
	ID                   string
	EstimatedMemoryBytes uint64
}

type Budget struct {
	MaxResidentModels int
	MaxMemoryBytes    uint64
}

type ModelLoader interface {
	Load(context.Context, string) error
	Unload(context.Context, string) error
}

type residentModel struct {
	spec     ModelSpec
	loaded   bool
	leases   int
	lastUsed uint64
}

type Manager struct {
	mu     sync.Mutex
	loader ModelLoader
	models map[string]*residentModel
	clock  uint64
	memory uint64
	loaded int
}

type Lease struct {
	manager *Manager
	modelID string
	once    sync.Once
}

func NewManager(specs []ModelSpec, loader ModelLoader) *Manager {
	models := make(map[string]*residentModel, len(specs))
	for _, spec := range specs {
		models[spec.ID] = &residentModel{spec: spec}
	}
	return &Manager{loader: loader, models: models}
}

func (manager *Manager) Acquire(ctx context.Context, modelID string, budget Budget) (*Lease, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	manager.mu.Lock()
	defer manager.mu.Unlock()
	model := manager.models[modelID]
	if model == nil {
		return nil, ErrModelUnknown
	}
	if budget.MaxResidentModels <= 0 {
		budget.MaxResidentModels = 1
	}
	if budget.MaxMemoryBytes > 0 && model.spec.EstimatedMemoryBytes > budget.MaxMemoryBytes {
		return nil, ErrModelExceedsBudget
	}
	manager.clock++
	if model.loaded {
		model.leases++
		model.lastUsed = manager.clock
		return &Lease{manager: manager, modelID: modelID}, nil
	}

	for manager.loaded >= budget.MaxResidentModels || (budget.MaxMemoryBytes > 0 && manager.memory+model.spec.EstimatedMemoryBytes > budget.MaxMemoryBytes) {
		candidate := manager.leastRecentlyUsedIdle(modelID)
		if candidate == nil {
			return nil, ErrNoEvictableModel
		}
		if manager.loader == nil {
			return nil, errors.New("model loader is unavailable")
		}
		if err := manager.loader.Unload(ctx, candidate.spec.ID); err != nil {
			return nil, fmt.Errorf("unload %s: %w", candidate.spec.ID, err)
		}
		candidate.loaded = false
		manager.loaded--
		manager.memory -= candidate.spec.EstimatedMemoryBytes
	}
	if manager.loader == nil {
		return nil, errors.New("model loader is unavailable")
	}
	if err := manager.loader.Load(ctx, modelID); err != nil {
		return nil, fmt.Errorf("load %s: %w", modelID, err)
	}
	model.loaded = true
	model.leases = 1
	model.lastUsed = manager.clock
	manager.loaded++
	manager.memory += model.spec.EstimatedMemoryBytes
	return &Lease{manager: manager, modelID: modelID}, nil
}

func (lease *Lease) Release() {
	if lease == nil || lease.manager == nil {
		return
	}
	lease.once.Do(func() {
		lease.manager.mu.Lock()
		defer lease.manager.mu.Unlock()
		model := lease.manager.models[lease.modelID]
		if model == nil || model.leases == 0 {
			return
		}
		model.leases--
		lease.manager.clock++
		model.lastUsed = lease.manager.clock
	})
}

func (manager *Manager) leastRecentlyUsedIdle(exclude string) *residentModel {
	var selected *residentModel
	for id, model := range manager.models {
		if id == exclude || !model.loaded || model.leases > 0 {
			continue
		}
		if selected == nil || model.lastUsed < selected.lastUsed || (model.lastUsed == selected.lastUsed && model.spec.ID < selected.spec.ID) {
			selected = model
		}
	}
	return selected
}

func DefaultBudget(profile contracts.HardwareProfile) Budget {
	resident := 1
	if profile.Memory.TotalBytes >= 16<<30 {
		resident = 2
	}
	available := profile.Memory.AvailableBytes
	if available == 0 {
		available = profile.Memory.TotalBytes
	}
	return Budget{MaxResidentModels: resident, MaxMemoryBytes: available * 3 / 4}
}
