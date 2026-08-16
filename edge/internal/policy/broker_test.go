package policy

import (
	"net"
	"os"
	"path/filepath"
	"testing"
)

func TestBrokerDefaultsToDenyAndIgnoresAgentClaims(t *testing.T) {
	broker := NewBroker(Policy{})
	request := Request{Capability: "shell.everything", Target: "powershell.exe", AgentClaims: []string{"shell.everything"}}
	if decision := broker.Decide(request); decision.Kind != Deny || decision.Code != "unknown_capability" {
		t.Fatalf("unexpected decision: %#v", decision)
	}
}

func TestBrokerRestrictsFileReadsToCanonicalApprovedRoots(t *testing.T) {
	root := t.TempDir()
	broker := NewBroker(Policy{FileReadRoots: []string{root}})
	inside := filepath.Join(root, "reports", "today.txt")
	if err := os.MkdirAll(filepath.Dir(inside), 0o700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(inside, []byte("fixture"), 0o600); err != nil {
		t.Fatal(err)
	}
	if decision := broker.Decide(Request{Capability: FileRead, Target: inside}); decision.Kind != Allow {
		t.Fatalf("approved path denied: %#v", decision)
	}
	outside := filepath.Join(root, "..", "secret.txt")
	if decision := broker.Decide(Request{Capability: FileRead, Target: outside}); decision.Kind != Deny {
		t.Fatalf("traversal escaped approved root: %#v", decision)
	}
}

func TestBrokerRejectsSymlinkEscapeFromApprovedRoot(t *testing.T) {
	root := t.TempDir()
	outside := filepath.Join(t.TempDir(), "secret.txt")
	if err := os.WriteFile(outside, []byte("secret"), 0o600); err != nil {
		t.Fatal(err)
	}
	link := filepath.Join(root, "linked.txt")
	if err := os.Symlink(outside, link); err != nil {
		t.Skipf("symlink creation unavailable: %v", err)
	}
	broker := NewBroker(Policy{FileReadRoots: []string{root}})
	if decision := broker.Decide(Request{Capability: FileRead, Target: link}); decision.Kind != Deny {
		t.Fatalf("symlink escaped approved root: %#v", decision)
	}
}

func TestBrokerSeparatesExecutableFromArgumentsAndRequiresApproval(t *testing.T) {
	executable := filepath.Join(t.TempDir(), "tool.exe")
	broker := NewBroker(Policy{Processes: []ProcessRule{{Executable: executable, Arguments: [][]string{{"--version"}}}}})
	if decision := broker.Decide(Request{Capability: ProcessRun, Target: executable, Arguments: []string{"--version"}}); decision.Kind != RequireApproval {
		t.Fatalf("approved process must require approval: %#v", decision)
	}
	if decision := broker.Decide(Request{Capability: ProcessRun, Target: executable, Arguments: []string{"--version;Remove-Item", "x"}}); decision.Kind != Deny {
		t.Fatalf("undeclared arguments were accepted: %#v", decision)
	}
}

func TestBrokerAllowsOnlyApprovedHTTPSWebTargets(t *testing.T) {
	broker := NewBroker(Policy{WebHosts: []string{"docs.example.com"}})
	if decision := broker.Decide(Request{Capability: WebRead, Target: "https://docs.example.com/guide"}); decision.Kind != Allow {
		t.Fatalf("approved web target denied: %#v", decision)
	}
	for _, target := range []string{"http://docs.example.com", "https://evil.example", "https://127.0.0.1/admin", "https://user@docs.example.com"} {
		if decision := broker.Decide(Request{Capability: WebRead, Target: target}); decision.Kind != Deny {
			t.Fatalf("unsafe web target accepted (%s): %#v", target, decision)
		}
	}
}

func TestResolvedWebAddressesRejectPrivateAndRebindingTargets(t *testing.T) {
	if err := ValidateResolvedIPs([]net.IP{net.ParseIP("93.184.216.34")}); err != nil {
		t.Fatalf("public address rejected: %v", err)
	}
	for _, raw := range []string{"127.0.0.1", "10.0.0.1", "169.254.169.254", "::1", "fc00::1"} {
		if err := ValidateResolvedIPs([]net.IP{net.ParseIP(raw)}); err == nil {
			t.Fatalf("private address accepted: %s", raw)
		}
	}
}
