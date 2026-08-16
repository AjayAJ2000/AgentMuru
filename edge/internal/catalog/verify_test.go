package catalog

import (
	"crypto/ed25519"
	"crypto/sha256"
	"errors"
	"os"
	"testing"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

func TestCommittedCatalogFixtureHasAValidSignature(t *testing.T) {
	data, err := os.ReadFile("testdata/catalog.json")
	if err != nil {
		t.Fatal(err)
	}
	signature, err := os.ReadFile("testdata/catalog.sig")
	if err != nil {
		t.Fatal(err)
	}
	seed := sha256.Sum256([]byte("agentmuru-catalog-test-key"))
	publicKey := ed25519.NewKeyFromSeed(seed[:]).Public().(ed25519.PublicKey)
	if _, err := Verify(data, signature, publicKey); err != nil {
		t.Fatalf("committed fixture signature is invalid: %v", err)
	}
}

func TestVerifyAcceptsSignedCatalog(t *testing.T) {
	data, signature, publicKey := signedFixture(t, validCatalogJSON())
	catalog, err := Verify(data, signature, publicKey)
	if err != nil {
		t.Fatalf("Verify() error = %v", err)
	}
	if got, want := len(catalog.Artifacts), 1; got != want {
		t.Fatalf("artifact count = %d, want %d", got, want)
	}
}

func TestVerifyRejectsMutatedCatalog(t *testing.T) {
	data, signature, publicKey := signedFixture(t, validCatalogJSON())
	data[len(data)-2] ^= 1
	_, err := Verify(data, signature, publicKey)
	if !errors.Is(err, ErrInvalidSignature) {
		t.Fatalf("Verify() error = %v, want ErrInvalidSignature", err)
	}
}

func TestVerifyRejectsUnsafeArtifactMetadata(t *testing.T) {
	cases := map[string]string{
		"http URL":        replace(validCatalogJSON(), "https://models.example/", "http://models.example/"),
		"pickle format":   replace(validCatalogJSON(), `"format":"gguf"`, `"format":"pickle"`),
		"oversize model":  replace(validCatalogJSON(), `"size_bytes":524288000`, `"size_bytes":734003201`),
		"missing license": replace(validCatalogJSON(), `"license_url":"https://models.example/license"`, `"license_url":""`),
	}
	for name, value := range cases {
		t.Run(name, func(t *testing.T) {
			data, signature, publicKey := signedFixture(t, value)
			if _, err := Verify(data, signature, publicKey); err == nil {
				t.Fatal("Verify() accepted unsafe catalog metadata")
			}
		})
	}
}

func TestCompatibleFiltersBeforeRuntimeExecution(t *testing.T) {
	data, signature, publicKey := signedFixture(t, validCatalogJSON())
	catalog, err := Verify(data, signature, publicKey)
	if err != nil {
		t.Fatal(err)
	}
	profile := contracts.HardwareProfile{
		RuntimeVariants: []string{"windows-x64-baseline", "windows-x64-avx"},
		Memory:          contracts.MemoryInfo{TotalBytes: 8 << 30},
	}
	compatible := catalog.Compatible(profile)
	if got, want := len(compatible), 1; got != want {
		t.Fatalf("compatible artifacts = %d, want %d", got, want)
	}
	profile.RuntimeVariants = []string{"linux-x64-avx2"}
	if got := catalog.Compatible(profile); len(got) != 0 {
		t.Fatalf("incompatible profile returned %d artifacts", len(got))
	}
}

func validCatalogJSON() string {
	return `{"schema_version":"catalog.agentmuru.dev/v1","revision":"2026-08-17.1","max_artifact_bytes":734003200,"artifacts":[{"id":"qwen-0.5b-q4","model_id":"Qwen/Qwen2.5-0.5B-Instruct-GGUF","revision":"sha256:0123456789abcdef","format":"gguf","url":"https://models.example/qwen.gguf","size_bytes":524288000,"sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","runtime_variants":["windows-x64-avx"],"minimum_memory_bytes":6442450944,"license":{"id":"apache-2.0","gated":true,"license_url":"https://models.example/license"}}]}`
}

func signedFixture(t *testing.T, value string) ([]byte, []byte, ed25519.PublicKey) {
	t.Helper()
	seed := sha256.Sum256([]byte("agentmuru-catalog-test-key"))
	privateKey := ed25519.NewKeyFromSeed(seed[:])
	data := []byte(value)
	return data, ed25519.Sign(privateKey, data), privateKey.Public().(ed25519.PublicKey)
}

func replace(value, old, replacement string) string {
	result := []byte(value)
	oldBytes := []byte(old)
	replacementBytes := []byte(replacement)
	for index := 0; index+len(oldBytes) <= len(result); index++ {
		matched := true
		for offset := range oldBytes {
			if result[index+offset] != oldBytes[offset] {
				matched = false
				break
			}
		}
		if matched {
			return string(append(append(result[:index:index], replacementBytes...), result[index+len(oldBytes):]...))
		}
	}
	return value
}
