package cli

import (
	"bytes"
	"io"
	"os"
	"path/filepath"
	"strings"
	"testing"

	tea "charm.land/bubbletea/v2"
	ui "github.com/AjayAJ2000/AgentMuru/edge/internal/ui"
)

func TestOpenWorkspacePrintsActionableMessageWhenOutputIsRedirected(t *testing.T) {
	var out bytes.Buffer
	started := false

	err := OpenWorkspace(WorkspaceDependencies{
		In:                strings.NewReader(""),
		Out:               &out,
		InputInteractive:  func(io.Reader) bool { return true },
		OutputInteractive: func(io.Writer) bool { return false },
		Run: func(*ui.Model, io.Reader, io.Writer) error {
			started = true
			return nil
		},
	})

	if err != nil {
		t.Fatalf("OpenWorkspace() error = %v", err)
	}
	if started {
		t.Fatal("workspace renderer started with redirected output")
	}
	if got := out.String(); !strings.Contains(got, "muru doctor --json") {
		t.Fatalf("output = %q, want actionable doctor command", got)
	}
}

func TestOpenWorkspaceRunsOnlyWithInteractiveInputAndOutput(t *testing.T) {
	started := false
	err := OpenWorkspace(WorkspaceDependencies{
		In:                strings.NewReader(""),
		Out:               io.Discard,
		InputInteractive:  func(io.Reader) bool { return true },
		OutputInteractive: func(io.Writer) bool { return true },
		Run: func(model *ui.Model, input io.Reader, output io.Writer) error {
			started = model != nil && input != nil && output != nil
			return nil
		},
	})

	if err != nil {
		t.Fatalf("OpenWorkspace() error = %v", err)
	}
	if !started {
		t.Fatal("interactive workspace was not started")
	}
}

func TestOpenWorkspacePassesTheSessionPathToTheModel(t *testing.T) {
	path := filepath.Join(t.TempDir(), "workspace.json")
	err := OpenWorkspace(WorkspaceDependencies{
		In:                strings.NewReader(""),
		Out:               io.Discard,
		SessionPath:       path,
		InputInteractive:  func(io.Reader) bool { return true },
		OutputInteractive: func(io.Writer) bool { return true },
		Run: func(model *ui.Model, _ io.Reader, _ io.Writer) error {
			_, command := model.Update(tea.KeyPressMsg{Code: tea.KeyTab})
			if command == nil {
				t.Fatal("navigation did not persist the session")
			}
			command()
			return nil
		},
	})
	if err != nil {
		t.Fatalf("OpenWorkspace() error = %v", err)
	}
	if _, err := os.Stat(path); err != nil {
		t.Fatalf("session snapshot was not written: %v", err)
	}
}

func TestUICommandUsesWorkspaceEntrypoint(t *testing.T) {
	opened := false
	cmd := NewRoot(Dependencies{
		Version: "test",
		Out:     io.Discard,
		ErrOut:  io.Discard,
		OpenWorkspace: func() error {
			opened = true
			return nil
		},
	})
	cmd.SetArgs([]string{"ui"})

	if err := cmd.Execute(); err != nil {
		t.Fatalf("Execute() error = %v", err)
	}
	if !opened {
		t.Fatal("ui command did not open the terminal workspace")
	}
}
