package cli

import (
	"bytes"
	"context"
	"errors"
	"io"
	"strings"
	"testing"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/catalog"
	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

func TestModelsInstallRequiresExactLicenseAcceptanceInJSONMode(t *testing.T) {
	service := &fakeModelService{catalog: fixtureModelCatalog()}
	var out bytes.Buffer
	cmd := NewRoot(Dependencies{Version: "test", Out: &out, ErrOut: io.Discard, Models: service})
	cmd.SetArgs([]string{"models", "install", "fixture", "--json"})

	err := cmd.Execute()
	if !errors.Is(err, ErrLicenseRequired) {
		t.Fatalf("Execute() error = %v, want ErrLicenseRequired", err)
	}
	if service.installed {
		t.Fatal("gated model installed without acceptance")
	}
	if !strings.Contains(out.String(), `"code":"license_required"`) {
		t.Fatalf("JSON output = %q", out.String())
	}
}

func TestModelsInstallAcceptsTheCatalogLicenseID(t *testing.T) {
	service := &fakeModelService{catalog: fixtureModelCatalog()}
	cmd := NewRoot(Dependencies{Version: "test", Out: io.Discard, ErrOut: io.Discard, Models: service})
	cmd.SetArgs([]string{"models", "install", "fixture", "--accept-license", "apache-2.0"})

	if err := cmd.Execute(); err != nil {
		t.Fatalf("Execute() error = %v", err)
	}
	if !service.installed || service.accepted != "apache-2.0" {
		t.Fatalf("install state = %v, accepted = %q", service.installed, service.accepted)
	}
}

func TestModelsListJSONIsStable(t *testing.T) {
	service := &fakeModelService{inventory: []catalog.InstalledArtifact{{Artifact: fixtureModelCatalog().Artifacts[0]}}}
	var out bytes.Buffer
	cmd := NewRoot(Dependencies{Version: "test", Out: &out, ErrOut: io.Discard, Models: service})
	cmd.SetArgs([]string{"models", "list", "--json"})

	if err := cmd.Execute(); err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(out.String(), `"id":"fixture"`) {
		t.Fatalf("list output = %q", out.String())
	}
}

type fakeModelService struct {
	catalog   contracts.Catalog
	inventory []catalog.InstalledArtifact
	installed bool
	accepted  string
}

func (service *fakeModelService) Catalog(context.Context) (contracts.Catalog, error) {
	return service.catalog, nil
}

func (service *fakeModelService) Inventory() ([]catalog.InstalledArtifact, error) {
	return service.inventory, nil
}

func (service *fakeModelService) Install(_ context.Context, _ contracts.Artifact, accepted string) error {
	service.installed = true
	service.accepted = accepted
	return nil
}

func (service *fakeModelService) Remove(string) error { return nil }

func fixtureModelCatalog() contracts.Catalog {
	return contracts.Catalog{Artifacts: []contracts.Artifact{{
		ID: "fixture", ModelID: "fixture/model", License: contracts.LicenseInfo{
			ID: "apache-2.0", Gated: true, LicenseURL: "https://models.example/license",
		},
	}}}
}
