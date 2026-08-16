package download

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"os"
	"path/filepath"
	"testing"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

func TestFetchPromotesOnlyVerifiedBytes(t *testing.T) {
	data := []byte("small deterministic gguf fixture")
	artifact := artifactFor(data)
	target := filepath.Join(t.TempDir(), artifact.SHA256+".gguf")
	var downloaded uint64

	err := Fetch(context.Background(), fixtureClient(data), artifact, target, func(current, declared uint64) {
		downloaded = current
		if declared != uint64(len(data)) {
			t.Fatalf("declared bytes = %d, want %d", declared, len(data))
		}
	})
	if err != nil {
		t.Fatalf("Fetch() error = %v", err)
	}
	if downloaded != uint64(len(data)) {
		t.Fatalf("progress = %d, want %d", downloaded, len(data))
	}
	got, err := os.ReadFile(target)
	if err != nil {
		t.Fatal(err)
	}
	if string(got) != string(data) {
		t.Fatalf("downloaded bytes = %q, want %q", got, data)
	}
}

func TestFetchNeverPromotesWrongDigest(t *testing.T) {
	data := []byte("model")
	artifact := artifactFor(data)
	artifact.SHA256 = "0000000000000000000000000000000000000000000000000000000000000000"
	target := filepath.Join(t.TempDir(), "model.gguf")

	err := Fetch(context.Background(), fixtureClient(data), artifact, target, nil)
	if !errors.Is(err, ErrDigestMismatch) {
		t.Fatalf("Fetch() error = %v, want ErrDigestMismatch", err)
	}
	if _, err := os.Stat(target); !errors.Is(err, os.ErrNotExist) {
		t.Fatalf("target exists after digest mismatch: %v", err)
	}
	if _, err := os.Stat(target + ".partial"); !errors.Is(err, os.ErrNotExist) {
		t.Fatalf("partial exists after digest mismatch: %v", err)
	}
}

func TestFetchRejectsMoreThanDeclaredSize(t *testing.T) {
	data := []byte("oversized")
	artifact := artifactFor(data)
	artifact.SizeBytes--
	target := filepath.Join(t.TempDir(), "model.gguf")

	err := Fetch(context.Background(), fixtureClient(data), artifact, target, nil)
	if !errors.Is(err, ErrSizeMismatch) {
		t.Fatalf("Fetch() error = %v, want ErrSizeMismatch", err)
	}
}

func TestFetchCancellationLeavesNoPartial(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	data := []byte("model")
	artifact := artifactFor(data)
	target := filepath.Join(t.TempDir(), "model.gguf")

	err := Fetch(ctx, fixtureClient(data), artifact, target, nil)
	if !errors.Is(err, context.Canceled) {
		t.Fatalf("Fetch() error = %v, want context.Canceled", err)
	}
	if _, err := os.Stat(target + ".partial"); !errors.Is(err, os.ErrNotExist) {
		t.Fatalf("partial exists after cancellation: %v", err)
	}
}

func artifactFor(data []byte) contracts.Artifact {
	digest := sha256.Sum256(data)
	return contracts.Artifact{
		ID: "fixture", URL: "https://models.example/fixture.gguf", SizeBytes: uint64(len(data)),
		SHA256: hex.EncodeToString(digest[:]), Format: "gguf",
	}
}
