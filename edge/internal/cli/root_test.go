package cli

import (
	"bytes"
	"io"
	"testing"
)

func TestVersionDoesNotEnterWorkspace(t *testing.T) {
	var out bytes.Buffer
	opened := false
	cmd := NewRoot(Dependencies{
		Version: "0.3.0-dev",
		Out:     &out,
		ErrOut:  io.Discard,
		OpenWorkspace: func() error {
			opened = true
			return nil
		},
	})
	cmd.SetArgs([]string{"version"})

	if err := cmd.Execute(); err != nil {
		t.Fatalf("Execute() error = %v", err)
	}
	if got, want := out.String(), "AgentMuru 0.3.0-dev\n"; got != want {
		t.Fatalf("output = %q, want %q", got, want)
	}
	if opened {
		t.Fatal("version command opened the terminal workspace")
	}
}

func TestBareCommandOpensWorkspace(t *testing.T) {
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
	cmd.SetArgs(nil)

	if err := cmd.Execute(); err != nil {
		t.Fatalf("Execute() error = %v", err)
	}
	if !opened {
		t.Fatal("bare command did not open the terminal workspace")
	}
}
