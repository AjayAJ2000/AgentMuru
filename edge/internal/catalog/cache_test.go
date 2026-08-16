package catalog

import (
	"errors"
	"os"
	"path/filepath"
	"testing"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

func TestCacheInventoryAndRemoveStayInsideRoot(t *testing.T) {
	root := t.TempDir()
	cache := NewCache(root)
	artifact := contracts.Artifact{
		ID: "fixture", ModelID: "fixture/model", SHA256: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
		SizeBytes: 5, Format: "gguf", License: contracts.LicenseInfo{ID: "apache-2.0"},
	}
	path := cache.PathFor(artifact)
	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte("model"), 0o600); err != nil {
		t.Fatal(err)
	}
	if err := cache.Record(artifact, false); err != nil {
		t.Fatalf("Record() error = %v", err)
	}

	inventory, err := cache.Inventory()
	if err != nil {
		t.Fatalf("Inventory() error = %v", err)
	}
	if len(inventory) != 1 || inventory[0].Artifact.ID != "fixture" {
		t.Fatalf("inventory = %#v", inventory)
	}
	if err := cache.Remove("fixture"); err != nil {
		t.Fatalf("Remove() error = %v", err)
	}
	if _, err := os.Stat(path); !errors.Is(err, os.ErrNotExist) {
		t.Fatalf("artifact remains after removal: %v", err)
	}
	if err := cache.Remove("../outside"); !errors.Is(err, ErrArtifactNotInstalled) {
		t.Fatalf("unsafe remove error = %v, want ErrArtifactNotInstalled", err)
	}
}

func TestEmbeddedBootstrapCatalogIsSigned(t *testing.T) {
	value, err := LoadBootstrap()
	if err != nil {
		t.Fatalf("LoadBootstrap() error = %v", err)
	}
	if value.SchemaVersion != contracts.CatalogSchemaV1 {
		t.Fatalf("schema = %q", value.SchemaVersion)
	}
}
