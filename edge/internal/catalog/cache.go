package catalog

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"time"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

var ErrArtifactNotInstalled = errors.New("artifact is not installed")

type InstalledArtifact struct {
	Artifact        contracts.Artifact `json:"artifact"`
	InstalledAt     time.Time          `json:"installed_at"`
	LicenseAccepted bool               `json:"license_accepted"`
}

type Cache struct {
	root string
}

func NewCache(root string) *Cache {
	return &Cache{root: root}
}

func (cache *Cache) PathFor(artifact contracts.Artifact) string {
	return filepath.Join(cache.root, "artifacts", artifact.SHA256+".gguf")
}

func (cache *Cache) Record(artifact contracts.Artifact, licenseAccepted bool) error {
	if !digestPattern.MatchString(artifact.SHA256) || artifact.ID == "" {
		return errors.New("artifact metadata is invalid")
	}
	info, err := os.Stat(cache.PathFor(artifact))
	if err != nil {
		return fmt.Errorf("stat installed artifact: %w", err)
	}
	if uint64(info.Size()) != artifact.SizeBytes {
		return errors.New("installed artifact size does not match catalog")
	}
	installed := InstalledArtifact{Artifact: artifact, InstalledAt: time.Now().UTC(), LicenseAccepted: licenseAccepted}
	data, err := json.Marshal(installed)
	if err != nil {
		return err
	}
	directory := filepath.Join(cache.root, "inventory")
	if err := os.MkdirAll(directory, 0o700); err != nil {
		return err
	}
	target := filepath.Join(directory, metadataName(artifact.ID))
	temporary, err := os.CreateTemp(directory, ".inventory-*.tmp")
	if err != nil {
		return err
	}
	temporaryPath := temporary.Name()
	defer os.Remove(temporaryPath)
	if err := temporary.Chmod(0o600); err != nil {
		temporary.Close()
		return err
	}
	if _, err := temporary.Write(append(data, '\n')); err != nil {
		temporary.Close()
		return err
	}
	if err := temporary.Sync(); err != nil {
		temporary.Close()
		return err
	}
	if err := temporary.Close(); err != nil {
		return err
	}
	return replaceCacheFile(temporaryPath, target)
}

func (cache *Cache) Inventory() ([]InstalledArtifact, error) {
	directory := filepath.Join(cache.root, "inventory")
	entries, err := os.ReadDir(directory)
	if errors.Is(err, os.ErrNotExist) {
		return []InstalledArtifact{}, nil
	}
	if err != nil {
		return nil, err
	}
	result := make([]InstalledArtifact, 0, len(entries))
	for _, entry := range entries {
		if entry.IsDir() || filepath.Ext(entry.Name()) != ".json" {
			continue
		}
		data, err := os.ReadFile(filepath.Join(directory, entry.Name()))
		if err != nil {
			return nil, err
		}
		var installed InstalledArtifact
		decoder := json.NewDecoder(bytes.NewReader(data))
		decoder.DisallowUnknownFields()
		if err := decoder.Decode(&installed); err != nil {
			return nil, fmt.Errorf("decode inventory %q: %w", entry.Name(), err)
		}
		if !digestPattern.MatchString(installed.Artifact.SHA256) {
			return nil, fmt.Errorf("inventory %q contains an invalid digest", entry.Name())
		}
		if _, err := os.Stat(cache.PathFor(installed.Artifact)); err != nil {
			return nil, fmt.Errorf("inventory %q references a missing artifact: %w", entry.Name(), err)
		}
		result = append(result, installed)
	}
	sort.Slice(result, func(left, right int) bool { return result[left].Artifact.ID < result[right].Artifact.ID })
	return result, nil
}

func (cache *Cache) Remove(id string) error {
	inventory, err := cache.Inventory()
	if err != nil {
		return err
	}
	for _, installed := range inventory {
		if installed.Artifact.ID != id {
			continue
		}
		if err := os.Remove(cache.PathFor(installed.Artifact)); err != nil && !errors.Is(err, os.ErrNotExist) {
			return err
		}
		if err := os.Remove(filepath.Join(cache.root, "inventory", metadataName(id))); err != nil && !errors.Is(err, os.ErrNotExist) {
			return err
		}
		return nil
	}
	return ErrArtifactNotInstalled
}

func metadataName(id string) string {
	digest := sha256.Sum256([]byte(id))
	return hex.EncodeToString(digest[:]) + ".json"
}
