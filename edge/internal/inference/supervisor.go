package inference

import (
	"context"
	"crypto/rand"
	"encoding/base64"
	"encoding/hex"
	"errors"
	"fmt"
	"io"
	"net"
	"net/url"
	"os"
	"os/exec"
	"strconv"
	"strings"
	"sync"
	"time"
	"unicode"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
	"github.com/charmbracelet/x/ansi"
)

type Status string

const (
	StatusStopped  Status = "stopped"
	StatusStarting Status = "starting"
	StatusRunning  Status = "running"
	StatusStopping Status = "stopping"
	StatusFailed   Status = "failed"
)

type RuntimeConfig struct {
	Executable     string
	Arguments      []string
	Environment    []string
	ModelPath      string
	ModelID        string
	ArtifactDigest string
	SessionID      string
	StartupTimeout time.Duration
	StopTimeout    time.Duration
}

type Endpoint struct {
	URL         *url.URL
	Token       string
	CommandLine string
}

type EventPublisher interface {
	Publish(context.Context, contracts.Event) (contracts.Event, error)
}

type Supervisor struct {
	mu        sync.Mutex
	publisher EventPublisher
	status    Status
	command   *exec.Cmd
	done      chan error
	guard     *processGuard
	endpoint  Endpoint
	config    RuntimeConfig
	stopping  bool
	output    *boundedOutput
}

func NewSupervisor(publisher EventPublisher) *Supervisor {
	return &Supervisor{publisher: publisher, status: StatusStopped}
}

func (supervisor *Supervisor) Start(ctx context.Context, config RuntimeConfig) (Endpoint, error) {
	if err := ctx.Err(); err != nil {
		return Endpoint{}, err
	}
	if config.Executable == "" || config.ModelPath == "" {
		return Endpoint{}, errors.New("runtime executable and model path are required")
	}
	if config.StartupTimeout <= 0 {
		config.StartupTimeout = 30 * time.Second
	}
	if config.StopTimeout <= 0 {
		config.StopTimeout = 3 * time.Second
	}

	supervisor.mu.Lock()
	if supervisor.status != StatusStopped && supervisor.status != StatusFailed {
		supervisor.mu.Unlock()
		return Endpoint{}, errors.New("local inference runtime is already active")
	}
	supervisor.status = StatusStarting
	supervisor.stopping = false
	supervisor.config = config
	supervisor.output = newBoundedOutput(32 * 1024)
	supervisor.mu.Unlock()
	_ = supervisor.emit(ctx, "model.load.started", map[string]any{"model_id": config.ModelID, "artifact_digest": config.ArtifactDigest})

	port, err := reserveLoopbackPort()
	if err != nil {
		return Endpoint{}, supervisor.failStart(ctx, err)
	}
	token, err := randomToken()
	if err != nil {
		return Endpoint{}, supervisor.failStart(ctx, err)
	}
	endpointURL, _ := url.Parse("http://127.0.0.1:" + strconv.Itoa(port))
	command := exec.CommandContext(ctx, config.Executable, config.Arguments...)
	command.Env = mergedEnvironment(config.Environment, map[string]string{
		"LLAMA_API_KEY":   token,
		"LLAMA_ARG_HOST":  "127.0.0.1",
		"LLAMA_ARG_PORT":  strconv.Itoa(port),
		"LLAMA_ARG_MODEL": config.ModelPath,
		"LLAMA_ARG_UI":    "false",
	})
	command.Stdout = supervisor.output
	command.Stderr = supervisor.output
	if err := command.Start(); err != nil {
		return Endpoint{}, supervisor.failStart(ctx, err)
	}
	guard, err := attachProcess(command.Process.Pid)
	if err != nil {
		_ = command.Process.Kill()
		_ = command.Wait()
		return Endpoint{}, supervisor.failStart(ctx, fmt.Errorf("attach runtime process guard: %w", err))
	}
	done := make(chan error, 1)
	endpoint := Endpoint{URL: endpointURL, Token: token, CommandLine: sanitizedCommandLine(config.Executable, config.Arguments)}
	supervisor.mu.Lock()
	supervisor.command = command
	supervisor.done = done
	supervisor.guard = guard
	supervisor.endpoint = endpoint
	supervisor.mu.Unlock()

	go supervisor.wait(command, done)
	startupCtx, cancel := context.WithTimeout(ctx, config.StartupTimeout)
	defer cancel()
	if err := waitForHealth(startupCtx, endpoint, done); err != nil {
		return Endpoint{}, supervisor.failRunningStart(ctx, err)
	}
	supervisor.mu.Lock()
	supervisor.status = StatusRunning
	supervisor.mu.Unlock()
	_ = supervisor.emit(ctx, "model.loaded", map[string]any{"model_id": config.ModelID, "artifact_digest": config.ArtifactDigest, "endpoint": endpoint.URL.String()})
	return endpoint, nil
}

func (supervisor *Supervisor) Stop(ctx context.Context) error {
	supervisor.mu.Lock()
	if supervisor.command == nil || supervisor.status == StatusStopped {
		supervisor.status = StatusStopped
		supervisor.mu.Unlock()
		return nil
	}
	supervisor.status = StatusStopping
	supervisor.stopping = true
	command := supervisor.command
	done := supervisor.done
	guard := supervisor.guard
	config := supervisor.config
	supervisor.mu.Unlock()

	_ = supervisor.emit(ctx, "model.unload.started", map[string]any{"model_id": config.ModelID, "artifact_digest": config.ArtifactDigest})
	if err := command.Process.Signal(os.Interrupt); err != nil {
		_ = command.Process.Kill()
	}
	timer := time.NewTimer(config.StopTimeout)
	defer timer.Stop()
	select {
	case <-ctx.Done():
		_ = command.Process.Kill()
		<-done
		if guard != nil {
			_ = guard.Close()
		}
		return ctx.Err()
	case <-timer.C:
		if guard != nil {
			_ = guard.Close()
		}
		_ = command.Process.Kill()
		<-done
	case <-done:
		if guard != nil {
			_ = guard.Close()
		}
	}
	supervisor.mu.Lock()
	supervisor.status = StatusStopped
	supervisor.command = nil
	supervisor.done = nil
	supervisor.guard = nil
	supervisor.mu.Unlock()
	_ = supervisor.emit(ctx, "model.unloaded", map[string]any{"model_id": config.ModelID, "artifact_digest": config.ArtifactDigest})
	return nil
}

func (supervisor *Supervisor) Status() Status {
	supervisor.mu.Lock()
	defer supervisor.mu.Unlock()
	return supervisor.status
}

func (supervisor *Supervisor) wait(command *exec.Cmd, done chan error) {
	err := command.Wait()
	done <- err
	close(done)
	supervisor.mu.Lock()
	unexpected := supervisor.command == command && !supervisor.stopping
	if unexpected {
		supervisor.status = StatusFailed
	}
	config := supervisor.config
	supervisor.mu.Unlock()
	if unexpected {
		_ = supervisor.emit(context.Background(), "model.process.failed", map[string]any{
			"model_id": config.ModelID, "artifact_digest": config.ArtifactDigest, "reason": "runtime process exited",
		})
	}
}

func (supervisor *Supervisor) failStart(ctx context.Context, cause error) error {
	supervisor.mu.Lock()
	supervisor.status = StatusFailed
	config := supervisor.config
	supervisor.mu.Unlock()
	_ = supervisor.emit(ctx, "model.process.failed", map[string]any{"model_id": config.ModelID, "artifact_digest": config.ArtifactDigest, "reason": sanitizeRuntimeText(cause.Error())})
	return cause
}

func (supervisor *Supervisor) failRunningStart(ctx context.Context, cause error) error {
	supervisor.mu.Lock()
	supervisor.stopping = true
	command := supervisor.command
	done := supervisor.done
	guard := supervisor.guard
	supervisor.mu.Unlock()
	if guard != nil {
		_ = guard.Close()
	}
	if command != nil && command.Process != nil {
		_ = command.Process.Kill()
	}
	if done != nil {
		<-done
	}
	return supervisor.failStart(ctx, cause)
}

func (supervisor *Supervisor) emit(ctx context.Context, eventType string, payload map[string]any) error {
	if supervisor.publisher == nil {
		return nil
	}
	idBytes := make([]byte, 8)
	_, _ = rand.Read(idBytes)
	_, err := supervisor.publisher.Publish(ctx, contracts.Event{
		ID: hex.EncodeToString(idBytes), Type: eventType, Timestamp: time.Now().UTC(),
		SessionID: supervisor.config.SessionID, Payload: payload,
	})
	return err
}

func reserveLoopbackPort() (int, error) {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		return 0, err
	}
	defer listener.Close()
	return listener.Addr().(*net.TCPAddr).Port, nil
}

func randomToken() (string, error) {
	value := make([]byte, 32)
	if _, err := rand.Read(value); err != nil {
		return "", err
	}
	return base64.RawURLEncoding.EncodeToString(value), nil
}

func mergedEnvironment(additional []string, required map[string]string) []string {
	values := make(map[string]string)
	for _, entry := range append(os.Environ(), additional...) {
		key, value, ok := strings.Cut(entry, "=")
		if ok {
			values[strings.ToUpper(key)] = key + "=" + value
		}
	}
	for key, value := range required {
		values[strings.ToUpper(key)] = key + "=" + value
	}
	result := make([]string, 0, len(values))
	for _, value := range values {
		result = append(result, value)
	}
	return result
}

func sanitizedCommandLine(executable string, arguments []string) string {
	parts := append([]string{executable}, arguments...)
	for index := range parts {
		parts[index] = sanitizeRuntimeText(parts[index])
	}
	return strings.Join(parts, " ")
}

func sanitizeRuntimeText(value string) string {
	return strings.Map(func(character rune) rune {
		if unicode.IsControl(character) && character != '\n' && character != '\t' {
			return -1
		}
		return character
	}, ansi.Strip(value))
}

type boundedOutput struct {
	mu        sync.Mutex
	remaining int
	content   strings.Builder
}

func newBoundedOutput(limit int) *boundedOutput { return &boundedOutput{remaining: limit} }

func (output *boundedOutput) Write(value []byte) (int, error) {
	output.mu.Lock()
	defer output.mu.Unlock()
	written := len(value)
	if output.remaining <= 0 {
		return written, nil
	}
	text := sanitizeRuntimeText(string(value))
	if len(text) > output.remaining {
		text = text[:output.remaining]
	}
	_, _ = io.WriteString(&output.content, text)
	output.remaining -= len(text)
	return written, nil
}
