package config

import (
	"path/filepath"
	"testing"
)

func TestPathsForWindowsLocalAppData(t *testing.T) {
	paths := PathsForWindows(`C:\Users\muru\AppData\Local`)
	root := filepath.Clean(`C:\Users\muru\AppData\Local\AgentMuru`)

	if paths.Config != filepath.Join(root, "config") {
		t.Fatalf("Config = %q", paths.Config)
	}
	if paths.Cache != filepath.Join(root, "cache") {
		t.Fatalf("Cache = %q", paths.Cache)
	}
	if paths.Data != filepath.Join(root, "data") {
		t.Fatalf("Data = %q", paths.Data)
	}
	if paths.State != filepath.Join(root, "state") {
		t.Fatalf("State = %q", paths.State)
	}
}
