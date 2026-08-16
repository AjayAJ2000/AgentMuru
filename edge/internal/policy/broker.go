// Package policy makes authorization decisions from trusted host policy.
// Agent prompts and model output are deliberately not authority sources.
package policy

import (
	"errors"
	"net"
	"net/url"
	"path/filepath"
	"reflect"
	"runtime"
	"strings"
)

const (
	FileRead   = "fs.read"
	ProcessRun = "process.run"
	WebRead    = "web.read"
)

type DecisionKind string

const (
	Allow           DecisionKind = "allow"
	Deny            DecisionKind = "deny"
	RequireApproval DecisionKind = "require_approval"
)

type Decision struct {
	Kind DecisionKind `json:"kind"`
	Code string       `json:"code"`
}

type Request struct {
	Capability string
	Target     string
	Arguments  []string
	// AgentClaims is recorded by callers for audit only. It never grants access.
	AgentClaims []string
}

type ProcessRule struct {
	Executable string
	Arguments  [][]string
}

type Policy struct {
	FileReadRoots []string
	Processes     []ProcessRule
	WebHosts      []string
}

type Broker struct{ policy Policy }

func NewBroker(policy Policy) *Broker { return &Broker{policy: policy} }

func (broker *Broker) Decide(request Request) Decision {
	switch request.Capability {
	case FileRead:
		return broker.decideFileRead(request.Target)
	case ProcessRun:
		return broker.decideProcess(request.Target, request.Arguments)
	case WebRead:
		return broker.decideWeb(request.Target)
	default:
		return Decision{Kind: Deny, Code: "unknown_capability"}
	}
}

func (broker *Broker) decideFileRead(target string) Decision {
	if target == "" || isWindowsDevicePath(target) {
		return Decision{Kind: Deny, Code: "invalid_path"}
	}
	canonicalTarget, err := filepath.EvalSymlinks(target)
	if err != nil {
		return Decision{Kind: Deny, Code: "invalid_path"}
	}
	canonicalTarget, err = filepath.Abs(filepath.Clean(canonicalTarget))
	if err != nil {
		return Decision{Kind: Deny, Code: "invalid_path"}
	}
	for _, rawRoot := range broker.policy.FileReadRoots {
		root, err := filepath.EvalSymlinks(rawRoot)
		if err != nil {
			continue
		}
		root, err = filepath.Abs(filepath.Clean(root))
		if err != nil {
			continue
		}
		relative, err := filepath.Rel(root, canonicalTarget)
		if err == nil && relative != ".." && !strings.HasPrefix(relative, ".."+string(filepath.Separator)) && !filepath.IsAbs(relative) {
			return Decision{Kind: Allow, Code: "approved_file_root"}
		}
	}
	return Decision{Kind: Deny, Code: "file_root_denied"}
}

func (broker *Broker) decideProcess(target string, arguments []string) Decision {
	canonicalTarget, err := filepath.Abs(filepath.Clean(target))
	if err != nil || target == "" {
		return Decision{Kind: Deny, Code: "invalid_executable"}
	}
	for _, rule := range broker.policy.Processes {
		canonicalRule, err := filepath.Abs(filepath.Clean(rule.Executable))
		if err != nil || !samePath(canonicalTarget, canonicalRule) {
			continue
		}
		for _, allowed := range rule.Arguments {
			if reflect.DeepEqual(arguments, allowed) {
				return Decision{Kind: RequireApproval, Code: "process_approval_required"}
			}
		}
		return Decision{Kind: Deny, Code: "arguments_denied"}
	}
	return Decision{Kind: Deny, Code: "executable_denied"}
}

func (broker *Broker) decideWeb(target string) Decision {
	parsed, err := url.Parse(target)
	if err != nil || parsed.Scheme != "https" || parsed.User != nil || parsed.Hostname() == "" || (parsed.Port() != "" && parsed.Port() != "443") {
		return Decision{Kind: Deny, Code: "invalid_web_target"}
	}
	host := strings.ToLower(strings.TrimSuffix(parsed.Hostname(), "."))
	if address := net.ParseIP(host); address != nil {
		if ValidateResolvedIPs([]net.IP{address}) != nil {
			return Decision{Kind: Deny, Code: "private_web_target"}
		}
	}
	for _, allowed := range broker.policy.WebHosts {
		if host == strings.ToLower(strings.TrimSuffix(allowed, ".")) {
			return Decision{Kind: Allow, Code: "approved_web_host"}
		}
	}
	return Decision{Kind: Deny, Code: "web_host_denied"}
}

// ValidateResolvedIPs must be called after every DNS resolution and again for
// redirects so an approved hostname cannot rebind to a local service.
func ValidateResolvedIPs(addresses []net.IP) error {
	if len(addresses) == 0 {
		return errors.New("web target did not resolve")
	}
	for _, address := range addresses {
		if address == nil || address.IsLoopback() || address.IsPrivate() || address.IsUnspecified() || address.IsLinkLocalUnicast() || address.IsLinkLocalMulticast() || address.IsMulticast() {
			return errors.New("web target resolved to a non-public address")
		}
	}
	return nil
}

func samePath(left, right string) bool {
	if runtime.GOOS == "windows" {
		return strings.EqualFold(left, right)
	}
	return left == right
}

func isWindowsDevicePath(path string) bool {
	normalized := strings.ReplaceAll(path, "/", "\\")
	return strings.HasPrefix(normalized, `\\`) || strings.HasPrefix(normalized, `\\?\`) || strings.HasPrefix(normalized, `\\.\`)
}
