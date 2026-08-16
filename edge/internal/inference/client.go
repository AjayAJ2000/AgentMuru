package inference

import (
	"bytes"
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"reflect"
	"strings"
	"time"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

var (
	ErrUnknownAction    = errors.New("model selected an unknown action")
	ErrInvalidDecision  = errors.New("model returned an invalid action decision")
	ErrInvalidArguments = errors.New("model returned invalid action arguments")
	ErrInferenceBackend = errors.New("local inference backend request failed")
)

type Client struct {
	Endpoint       Endpoint
	HTTPClient     *http.Client
	Publisher      EventPublisher
	SessionID      string
	ModelID        string
	ArtifactDigest string
}

func (client *Client) Decide(ctx context.Context, request contracts.DecisionRequest) (contracts.ActionDecision, contracts.Usage, error) {
	started := time.Now()
	grammar, err := GrammarFor(request.Actions)
	if err != nil {
		return contracts.ActionDecision{}, contracts.Usage{}, err
	}
	if err := validateMessages(request.Messages); err != nil {
		return contracts.ActionDecision{}, contracts.Usage{}, err
	}
	maxTokens := request.MaxOutputTokens
	if maxTokens <= 0 {
		maxTokens = 128
	}
	if maxTokens > 256 {
		maxTokens = 256
	}
	_ = client.publish(ctx, "inference.started", map[string]any{
		"model_id": client.ModelID, "artifact_digest": client.ArtifactDigest, "decision_status": "started",
	})

	body, err := json.Marshal(map[string]any{
		"model": client.ModelID, "messages": request.Messages, "temperature": 0, "max_tokens": maxTokens,
		"stream": false, "grammar": grammar,
	})
	if err != nil {
		return contracts.ActionDecision{}, contracts.Usage{}, err
	}
	endpoint := client.Endpoint.URL.ResolveReference(&url.URL{Path: "/v1/chat/completions"})
	httpRequest, err := http.NewRequestWithContext(ctx, http.MethodPost, endpoint.String(), bytes.NewReader(body))
	if err != nil {
		return contracts.ActionDecision{}, contracts.Usage{}, err
	}
	httpRequest.Header.Set("Authorization", "Bearer "+client.Endpoint.Token)
	httpRequest.Header.Set("Content-Type", "application/json")
	httpClient := client.HTTPClient
	if httpClient == nil {
		httpClient = &http.Client{Timeout: 2 * time.Minute}
	}
	response, err := httpClient.Do(httpRequest)
	if err != nil {
		client.publishFailure(ctx, started, "transport_error")
		return contracts.ActionDecision{}, contracts.Usage{}, fmt.Errorf("%w: transport", ErrInferenceBackend)
	}
	defer response.Body.Close()
	if response.StatusCode < 200 || response.StatusCode >= 300 {
		_, _ = io.Copy(io.Discard, io.LimitReader(response.Body, 64*1024))
		client.publishFailure(ctx, started, "http_status")
		return contracts.ActionDecision{}, contracts.Usage{}, fmt.Errorf("%w: status %d", ErrInferenceBackend, response.StatusCode)
	}
	var backend struct {
		Choices []struct {
			Message struct {
				Content string `json:"content"`
			} `json:"message"`
		} `json:"choices"`
		Usage struct {
			PromptTokens     int `json:"prompt_tokens"`
			CompletionTokens int `json:"completion_tokens"`
		} `json:"usage"`
	}
	if err := json.NewDecoder(io.LimitReader(response.Body, 1024*1024)).Decode(&backend); err != nil || len(backend.Choices) != 1 {
		client.publishFailure(ctx, started, "invalid_backend_response")
		return contracts.ActionDecision{}, contracts.Usage{}, ErrInvalidDecision
	}
	decision, err := decodeDecision(backend.Choices[0].Message.Content)
	if err != nil {
		client.publishFailure(ctx, started, "invalid_decision")
		return contracts.ActionDecision{}, contracts.Usage{}, err
	}
	descriptor, ok := actionByName(request.Actions, decision.Action)
	if !ok {
		client.publishFailure(ctx, started, "unknown_action")
		return contracts.ActionDecision{}, contracts.Usage{}, ErrUnknownAction
	}
	if err := validateArguments(descriptor, decision.Arguments); err != nil {
		client.publishFailure(ctx, started, "invalid_arguments")
		return contracts.ActionDecision{}, contracts.Usage{}, err
	}
	usage := contracts.Usage{InputTokens: backend.Usage.PromptTokens, OutputTokens: backend.Usage.CompletionTokens}
	_ = client.publish(ctx, "inference.completed", map[string]any{
		"model_id": client.ModelID, "artifact_digest": client.ArtifactDigest, "decision_status": "accepted",
		"action": decision.Action, "input_tokens": usage.InputTokens, "output_tokens": usage.OutputTokens,
		"duration_ms": time.Since(started).Milliseconds(),
	})
	return decision, usage, nil
}

func decodeDecision(content string) (contracts.ActionDecision, error) {
	decoder := json.NewDecoder(strings.NewReader(content))
	decoder.DisallowUnknownFields()
	var decision contracts.ActionDecision
	if err := decoder.Decode(&decision); err != nil || decision.Action == "" || decision.Arguments == nil {
		return contracts.ActionDecision{}, ErrInvalidDecision
	}
	var trailing any
	if err := decoder.Decode(&trailing); !errors.Is(err, io.EOF) {
		return contracts.ActionDecision{}, ErrInvalidDecision
	}
	return decision, nil
}

func validateMessages(messages []contracts.DecisionMessage) error {
	if len(messages) == 0 || len(messages) > 32 {
		return errors.New("decision request must contain 1 through 32 messages")
	}
	total := 0
	for _, message := range messages {
		if message.Role != "system" && message.Role != "user" && message.Role != "assistant" {
			return errors.New("decision request contains an invalid message role")
		}
		if len(message.Content) == 0 || len(message.Content) > 8192 {
			return errors.New("decision request message is outside the size limit")
		}
		total += len(message.Content)
	}
	if total > 32768 {
		return errors.New("decision request exceeds the total prompt limit")
	}
	return nil
}

func actionByName(actions []contracts.ActionDescriptor, name string) (contracts.ActionDescriptor, bool) {
	for _, action := range actions {
		if action.Name == name {
			return action, true
		}
	}
	return contracts.ActionDescriptor{}, false
}

func validateArguments(action contracts.ActionDescriptor, arguments map[string]any) error {
	for _, required := range action.Required {
		if _, ok := arguments[required]; !ok {
			return fmt.Errorf("%w: missing %s", ErrInvalidArguments, required)
		}
	}
	for name, value := range arguments {
		descriptor, ok := action.Arguments[name]
		if !ok || !argumentMatches(descriptor.Type, value) {
			return fmt.Errorf("%w: %s", ErrInvalidArguments, name)
		}
		if len(descriptor.Enum) > 0 {
			matched := false
			for _, allowed := range descriptor.Enum {
				if reflect.DeepEqual(value, allowed) {
					matched = true
					break
				}
			}
			if !matched {
				return fmt.Errorf("%w: %s is outside its enum", ErrInvalidArguments, name)
			}
		}
	}
	return nil
}

func argumentMatches(kind string, value any) bool {
	switch kind {
	case "string":
		_, ok := value.(string)
		return ok
	case "number":
		_, ok := value.(float64)
		return ok
	case "integer":
		number, ok := value.(float64)
		return ok && number == float64(int64(number))
	case "boolean":
		_, ok := value.(bool)
		return ok
	case "array":
		_, ok := value.([]any)
		return ok
	case "object":
		_, ok := value.(map[string]any)
		return ok
	default:
		return false
	}
}

func (client *Client) publishFailure(ctx context.Context, started time.Time, code string) {
	_ = client.publish(ctx, "inference.completed", map[string]any{
		"model_id": client.ModelID, "artifact_digest": client.ArtifactDigest, "decision_status": "rejected",
		"error_code": code, "duration_ms": time.Since(started).Milliseconds(),
	})
}

func (client *Client) publish(ctx context.Context, eventType string, payload map[string]any) error {
	if client.Publisher == nil {
		return nil
	}
	id := make([]byte, 8)
	_, _ = rand.Read(id)
	_, err := client.Publisher.Publish(ctx, contracts.Event{
		ID: hex.EncodeToString(id), Type: eventType, Timestamp: time.Now().UTC(), SessionID: client.SessionID, Payload: payload,
	})
	return err
}
