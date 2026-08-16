package inference

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"time"
)

func waitForHealth(ctx context.Context, endpoint Endpoint, processDone <-chan error) error {
	client := &http.Client{Timeout: 500 * time.Millisecond}
	ticker := time.NewTicker(50 * time.Millisecond)
	defer ticker.Stop()
	for {
		request, err := http.NewRequestWithContext(ctx, http.MethodGet, endpoint.URL.String()+"/health", nil)
		if err != nil {
			return err
		}
		request.Header.Set("Authorization", "Bearer "+endpoint.Token)
		response, requestErr := client.Do(request)
		if requestErr == nil {
			response.Body.Close()
			if response.StatusCode >= 200 && response.StatusCode < 300 {
				return nil
			}
		}
		select {
		case <-ctx.Done():
			return ctx.Err()
		case processErr := <-processDone:
			if processErr == nil {
				processErr = errors.New("runtime exited before health was ready")
			}
			return fmt.Errorf("runtime startup failed: %w", processErr)
		case <-ticker.C:
		}
	}
}
