package inference

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
	"github.com/AjayAJ2000/AgentMuru/edge/internal/events"
)

func TestSupervisorUsesLoopbackAndEphemeralToken(t *testing.T) {
	publisher := &recordingPublisher{}
	supervisor := NewSupervisor(publisher)
	endpoint, err := supervisor.Start(context.Background(), helperRuntimeConfig(t))
	if err != nil {
		t.Fatalf("Start() error = %v", err)
	}
	t.Cleanup(func() { _ = supervisor.Stop(context.Background()) })

	if got := endpoint.URL.Hostname(); got != "127.0.0.1" {
		t.Fatalf("hostname = %q, want loopback", got)
	}
	if len(endpoint.Token) < 40 {
		t.Fatalf("ephemeral token is too short: %q", endpoint.Token)
	}
	if strings.Contains(endpoint.CommandLine, endpoint.Token) {
		t.Fatal("ephemeral token leaked into the child command line")
	}
	if got := supervisor.Status(); got != StatusRunning {
		t.Fatalf("status = %q, want running", got)
	}
}

func TestSupervisorEmitsPersistableLifecycleOrder(t *testing.T) {
	publisher := &recordingPublisher{}
	supervisor := NewSupervisor(publisher)
	if _, err := supervisor.Start(context.Background(), helperRuntimeConfig(t)); err != nil {
		t.Fatal(err)
	}
	if err := supervisor.Stop(context.Background()); err != nil {
		t.Fatal(err)
	}
	got := publisher.types()
	want := []string{"model.load.started", "model.loaded", "model.unload.started", "model.unloaded"}
	if strings.Join(got, ",") != strings.Join(want, ",") {
		t.Fatalf("lifecycle events = %v, want %v", got, want)
	}
}

func TestSupervisorLifecycleIsPersistedThroughTheEventBus(t *testing.T) {
	store := events.NewJSONLStore(t.TempDir())
	supervisor := NewSupervisor(events.NewBus(store))
	if _, err := supervisor.Start(context.Background(), helperRuntimeConfig(t)); err != nil {
		t.Fatal(err)
	}
	if err := supervisor.Stop(context.Background()); err != nil {
		t.Fatal(err)
	}
	persisted, err := store.Replay(context.Background(), "session-test", 0)
	if err != nil {
		t.Fatal(err)
	}
	got := make([]string, len(persisted))
	for index, event := range persisted {
		got[index] = event.Type
	}
	want := []string{"model.load.started", "model.loaded", "model.unload.started", "model.unloaded"}
	if strings.Join(got, ",") != strings.Join(want, ",") {
		t.Fatalf("persisted lifecycle events = %v, want %v", got, want)
	}
}

func TestSupervisorHonorsCanceledStartup(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	supervisor := NewSupervisor(nil)
	if _, err := supervisor.Start(ctx, helperRuntimeConfig(t)); err == nil {
		t.Fatal("Start() succeeded with a canceled context")
	}
}

func TestSupervisorHelperProcess(t *testing.T) {
	if os.Getenv("GO_WANT_AGENTMURU_HELPER") != "1" {
		return
	}
	host := os.Getenv("LLAMA_ARG_HOST")
	port := os.Getenv("LLAMA_ARG_PORT")
	token := os.Getenv("LLAMA_API_KEY")
	server := &http.Server{Addr: host + ":" + port, Handler: http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		if request.Header.Get("Authorization") != "Bearer "+token {
			writer.WriteHeader(http.StatusUnauthorized)
			return
		}
		writer.Header().Set("Content-Type", "application/json")
		_, _ = writer.Write([]byte(`{"status":"ok"}`))
	})}
	if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	os.Exit(0)
}

func helperRuntimeConfig(t *testing.T) RuntimeConfig {
	t.Helper()
	return RuntimeConfig{
		Executable:  os.Args[0],
		Arguments:   []string{"-test.run=TestSupervisorHelperProcess", "--"},
		Environment: []string{"GO_WANT_AGENTMURU_HELPER=1"},
		ModelPath:   "fixture.gguf", ModelID: "fixture", ArtifactDigest: strings.Repeat("a", 64),
		SessionID: "session-test", StartupTimeout: 5 * time.Second, StopTimeout: 200 * time.Millisecond,
	}
}

type recordingPublisher struct {
	mu     sync.Mutex
	events []contracts.Event
}

func (publisher *recordingPublisher) Publish(_ context.Context, event contracts.Event) (contracts.Event, error) {
	publisher.mu.Lock()
	defer publisher.mu.Unlock()
	publisher.events = append(publisher.events, event)
	return event, nil
}

func (publisher *recordingPublisher) types() []string {
	publisher.mu.Lock()
	defer publisher.mu.Unlock()
	result := make([]string, len(publisher.events))
	for index, event := range publisher.events {
		result[index] = event.Type
	}
	return result
}
