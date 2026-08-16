package catalog

import (
	"context"
	"net/http"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
	"github.com/AjayAJ2000/AgentMuru/edge/internal/download"
)

type LocalModels struct {
	verified contracts.Catalog
	cache    *Cache
	client   *http.Client
}

func NewLocalModels(verified contracts.Catalog, cache *Cache, client *http.Client) *LocalModels {
	if client == nil {
		client = http.DefaultClient
	}
	return &LocalModels{verified: verified, cache: cache, client: client}
}

func (models *LocalModels) Catalog(context.Context) (contracts.Catalog, error) {
	return models.verified, nil
}

func (models *LocalModels) Inventory() ([]InstalledArtifact, error) {
	return models.cache.Inventory()
}

func (models *LocalModels) Install(ctx context.Context, artifact contracts.Artifact, acceptedLicense string) error {
	path := models.cache.PathFor(artifact)
	if err := download.Fetch(ctx, models.client, artifact, path, nil); err != nil {
		return err
	}
	accepted := artifact.License.Gated && acceptedLicense == artifact.License.ID
	return models.cache.Record(artifact, accepted)
}

func (models *LocalModels) Remove(id string) error {
	return models.cache.Remove(id)
}
