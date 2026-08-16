package inference

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"strings"
	"testing"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

func TestDecideRejectsUnknownAction(t *testing.T) {
	client := fixtureDecisionClient(t, `{"action":"delete_all","arguments":{}}`)
	_, _, err := client.Decide(context.Background(), decisionRequest())
	if !errors.Is(err, ErrUnknownAction) {
		t.Fatalf("Decide() error = %v, want ErrUnknownAction", err)
	}
}

func TestDecideRejectsMarkdownAndMalformedJSON(t *testing.T) {
	client := fixtureDecisionClient(t, "```json\n{\"action\":\"search_files\",\"arguments\":{}}\n```")
	_, _, err := client.Decide(context.Background(), decisionRequest())
	if !errors.Is(err, ErrInvalidDecision) {
		t.Fatalf("Decide() error = %v, want ErrInvalidDecision", err)
	}
}

func TestDecideValidatesArgumentsAndReturnsUsage(t *testing.T) {
	client := fixtureDecisionClient(t, `{"action":"search_files","arguments":{"query":"needle"}}`)
	decision, usage, err := client.Decide(context.Background(), decisionRequest())
	if err != nil {
		t.Fatal(err)
	}
	if decision.Action != "search_files" || decision.Arguments["query"] != "needle" {
		t.Fatalf("decision = %#v", decision)
	}
	if usage.InputTokens != 11 || usage.OutputTokens != 7 {
		t.Fatalf("usage = %#v", usage)
	}
}

func TestDecideRejectsUndeclaredArgument(t *testing.T) {
	client := fixtureDecisionClient(t, `{"action":"search_files","arguments":{"query":"needle","root":"C:/"}}`)
	_, _, err := client.Decide(context.Background(), decisionRequest())
	if !errors.Is(err, ErrInvalidArguments) {
		t.Fatalf("Decide() error = %v, want ErrInvalidArguments", err)
	}
}

func TestDecideEnforcesArgumentEnum(t *testing.T) {
	client := fixtureDecisionClient(t, `{"action":"search_files","arguments":{"query":"needle"}}`)
	request := decisionRequest()
	descriptor := request.Actions[0].Arguments["query"]
	descriptor.Enum = []any{"docs", "source"}
	request.Actions[0].Arguments["query"] = descriptor
	_, _, err := client.Decide(context.Background(), request)
	if !errors.Is(err, ErrInvalidArguments) {
		t.Fatalf("Decide() error = %v, want ErrInvalidArguments", err)
	}
}

func TestInferenceEventsExcludePromptTokenAndArguments(t *testing.T) {
	publisher := &recordingPublisher{}
	client := fixtureDecisionClient(t, `{"action":"search_files","arguments":{"query":"needle"}}`)
	client.Publisher = publisher
	client.SessionID = "session-safe"
	if _, _, err := client.Decide(context.Background(), decisionRequest()); err != nil {
		t.Fatal(err)
	}
	raw, err := json.Marshal(publisher.events)
	if err != nil {
		t.Fatal(err)
	}
	for _, secret := range []string{"Find needle", `"query":"needle"`, "test-token"} {
		if strings.Contains(string(raw), secret) {
			t.Fatalf("safe inference events leaked %q: %s", secret, raw)
		}
	}
}

func fixtureDecisionClient(t *testing.T, content string) *Client {
	t.Helper()
	transport := roundTripFunc(func(request *http.Request) (*http.Response, error) {
		if request.Header.Get("Authorization") != "Bearer test-token" {
			t.Fatalf("authorization header = %q", request.Header.Get("Authorization"))
		}
		body := `{"choices":[{"message":{"content":` + quoteJSON(content) + `}}],"usage":{"prompt_tokens":11,"completion_tokens":7}}`
		return jsonResponse(body), nil
	})
	return &Client{
		Endpoint:   Endpoint{URL: mustURL("http://127.0.0.1:12345"), Token: "test-token"},
		HTTPClient: &http.Client{Transport: transport}, ModelID: "fixture", ArtifactDigest: "aaaaaaaa",
	}
}

func decisionRequest() contracts.DecisionRequest {
	return contracts.DecisionRequest{
		Messages: []contracts.DecisionMessage{{Role: "user", Content: "Find needle"}},
		Actions: []contracts.ActionDescriptor{{
			Name: "search_files", Description: "Search local files", Required: []string{"query"},
			Arguments: map[string]contracts.ArgumentDescriptor{"query": {Type: "string"}},
		}},
		MaxOutputTokens: 64,
	}
}
