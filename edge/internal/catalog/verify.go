package catalog

import (
	"crypto/ed25519"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"net/url"
	"regexp"
	"strings"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

var (
	ErrInvalidSignature = errors.New("invalid catalog signature")
	digestPattern       = regexp.MustCompile(`^[0-9a-f]{64}$`)
	revisionPattern     = regexp.MustCompile(`^(sha256:)?[0-9a-f]{16,64}$`)
)

var knownRuntimeVariants = map[string]struct{}{
	"windows-x64-baseline": {},
	"windows-x64-avx":      {},
	"windows-x64-avx2":     {},
	"linux-x64-baseline":   {},
	"linux-x64-avx":        {},
	"linux-x64-avx2":       {},
}

func Verify(data, signature []byte, publicKey ed25519.PublicKey) (contracts.Catalog, error) {
	signature = decodeSignature(signature)
	if len(publicKey) != ed25519.PublicKeySize || len(signature) != ed25519.SignatureSize || !ed25519.Verify(publicKey, data, signature) {
		return contracts.Catalog{}, ErrInvalidSignature
	}

	var value contracts.Catalog
	decoder := json.NewDecoder(strings.NewReader(string(data)))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(&value); err != nil {
		return contracts.Catalog{}, fmt.Errorf("decode catalog: %w", err)
	}
	if err := validate(value); err != nil {
		return contracts.Catalog{}, err
	}
	return value, nil
}

func decodeSignature(value []byte) []byte {
	if len(value) == ed25519.SignatureSize {
		return value
	}
	decoded, err := base64.StdEncoding.DecodeString(strings.TrimSpace(string(value)))
	if err != nil {
		return value
	}
	return decoded
}

func validate(value contracts.Catalog) error {
	if value.SchemaVersion != contracts.CatalogSchemaV1 {
		return fmt.Errorf("unsupported catalog schema %q", value.SchemaVersion)
	}
	if value.Revision == "" {
		return errors.New("catalog revision is required")
	}
	if value.MaxArtifactBytes == 0 || value.MaxArtifactBytes > contracts.MaximumArtifactBytes {
		return fmt.Errorf("catalog artifact ceiling exceeds %d bytes", contracts.MaximumArtifactBytes)
	}
	seen := make(map[string]struct{}, len(value.Artifacts))
	for index, artifact := range value.Artifacts {
		if artifact.ID == "" || artifact.ModelID == "" {
			return fmt.Errorf("artifact %d has an empty identity", index)
		}
		if _, exists := seen[artifact.ID]; exists {
			return fmt.Errorf("duplicate artifact id %q", artifact.ID)
		}
		seen[artifact.ID] = struct{}{}
		if !revisionPattern.MatchString(artifact.Revision) {
			return fmt.Errorf("artifact %q has a mutable revision", artifact.ID)
		}
		if strings.ToLower(artifact.Format) != "gguf" {
			return fmt.Errorf("artifact %q uses rejected format %q", artifact.ID, artifact.Format)
		}
		upstream, err := url.Parse(artifact.URL)
		if err != nil || upstream.Scheme != "https" || upstream.Host == "" || upstream.User != nil {
			return fmt.Errorf("artifact %q has an unsafe upstream URL", artifact.ID)
		}
		if artifact.SizeBytes == 0 || artifact.SizeBytes > value.MaxArtifactBytes || artifact.SizeBytes > contracts.MaximumArtifactBytes {
			return fmt.Errorf("artifact %q exceeds the size ceiling", artifact.ID)
		}
		if !digestPattern.MatchString(artifact.SHA256) {
			return fmt.Errorf("artifact %q has an invalid SHA-256 digest", artifact.ID)
		}
		if len(artifact.RuntimeVariants) == 0 {
			return fmt.Errorf("artifact %q has no runtime variants", artifact.ID)
		}
		variantSeen := map[string]struct{}{}
		for _, variant := range artifact.RuntimeVariants {
			if _, ok := knownRuntimeVariants[variant]; !ok {
				return fmt.Errorf("artifact %q names unknown runtime variant %q", artifact.ID, variant)
			}
			if _, duplicate := variantSeen[variant]; duplicate {
				return fmt.Errorf("artifact %q repeats runtime variant %q", artifact.ID, variant)
			}
			variantSeen[variant] = struct{}{}
		}
		if artifact.License.ID == "" {
			return fmt.Errorf("artifact %q has no license id", artifact.ID)
		}
		if artifact.License.Gated {
			licenseURL, err := url.Parse(artifact.License.LicenseURL)
			if err != nil || licenseURL.Scheme != "https" || licenseURL.Host == "" {
				return fmt.Errorf("artifact %q requires a valid license URL", artifact.ID)
			}
		}
	}
	return nil
}
