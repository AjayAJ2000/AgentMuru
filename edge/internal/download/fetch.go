package download

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strings"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

var (
	ErrDigestMismatch = errors.New("artifact digest mismatch")
	ErrSizeMismatch   = errors.New("artifact size mismatch")
	ErrHTTPStatus     = errors.New("artifact download returned an unsuccessful status")
)

type ProgressFunc func(downloaded, declared uint64)

func Fetch(ctx context.Context, client *http.Client, artifact contracts.Artifact, destination string, progress ProgressFunc) error {
	if client == nil {
		client = http.DefaultClient
	}
	upstream, err := url.Parse(artifact.URL)
	if err != nil || upstream.Scheme != "https" || upstream.Host == "" || strings.ToLower(artifact.Format) != "gguf" {
		return errors.New("artifact metadata is not safe to download")
	}
	if len(artifact.SHA256) != 64 || artifact.SizeBytes == 0 || artifact.SizeBytes > contracts.MaximumArtifactBytes {
		return errors.New("artifact verification metadata is invalid")
	}
	if err := os.MkdirAll(filepath.Dir(destination), 0o700); err != nil {
		return fmt.Errorf("create artifact directory: %w", err)
	}
	partial := destination + ".partial"
	if err := os.Remove(partial); err != nil && !errors.Is(err, os.ErrNotExist) {
		return fmt.Errorf("remove stale partial artifact: %w", err)
	}
	promoted := false
	defer func() {
		if !promoted {
			_ = os.Remove(partial)
		}
	}()

	request, err := http.NewRequestWithContext(ctx, http.MethodGet, artifact.URL, nil)
	if err != nil {
		return err
	}
	response, err := client.Do(request)
	if err != nil {
		return err
	}
	defer response.Body.Close()
	if response.StatusCode < 200 || response.StatusCode >= 300 {
		return fmt.Errorf("%w: %d", ErrHTTPStatus, response.StatusCode)
	}
	if response.ContentLength > int64(artifact.SizeBytes) {
		return ErrSizeMismatch
	}

	file, err := os.OpenFile(partial, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0o600)
	if err != nil {
		return fmt.Errorf("create partial artifact: %w", err)
	}
	hash := sha256.New()
	buffer := make([]byte, 64*1024)
	limited := io.LimitReader(response.Body, int64(artifact.SizeBytes)+1)
	var downloaded uint64
	for {
		select {
		case <-ctx.Done():
			file.Close()
			return ctx.Err()
		default:
		}
		count, readErr := limited.Read(buffer)
		if count > 0 {
			downloaded += uint64(count)
			if downloaded > artifact.SizeBytes {
				file.Close()
				return ErrSizeMismatch
			}
			if _, err := file.Write(buffer[:count]); err != nil {
				file.Close()
				return fmt.Errorf("write partial artifact: %w", err)
			}
			_, _ = hash.Write(buffer[:count])
			if progress != nil {
				progress(downloaded, artifact.SizeBytes)
			}
		}
		if errors.Is(readErr, io.EOF) {
			break
		}
		if readErr != nil {
			file.Close()
			return fmt.Errorf("read artifact response: %w", readErr)
		}
	}
	if downloaded != artifact.SizeBytes {
		file.Close()
		return ErrSizeMismatch
	}
	if !strings.EqualFold(hex.EncodeToString(hash.Sum(nil)), artifact.SHA256) {
		file.Close()
		return ErrDigestMismatch
	}
	if err := file.Sync(); err != nil {
		file.Close()
		return fmt.Errorf("flush partial artifact: %w", err)
	}
	if err := file.Close(); err != nil {
		return fmt.Errorf("close partial artifact: %w", err)
	}
	if err := promoteFile(partial, destination); err != nil {
		return fmt.Errorf("promote verified artifact: %w", err)
	}
	promoted = true
	return nil
}
