package orchestrator

import (
	"context"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

type Explanation struct {
	RunID           string    `json:"run_id"`
	PackID          string    `json:"pack_id"`
	InputDigest     string    `json:"input_digest"`
	Path            []string  `json:"path"`
	Outcome         string    `json:"outcome"`
	SelectedAction  string    `json:"selected_action,omitempty"`
	Reason          string    `json:"reason"`
	Mode            string    `json:"mode"`
	EffectsExecuted int       `json:"effects_executed"`
	CreatedAt       time.Time `json:"created_at"`
}

type Engine struct{ stateDir string }

func NewEngine(stateDir string) *Engine { return &Engine{stateDir: stateDir} }
func (engine *Engine) StateDir() string { return engine.stateDir }

func (engine *Engine) Submit(ctx context.Context, value contracts.AgentPack, input string) (string, error) {
	if err := ctx.Err(); err != nil {
		return "", err
	}
	if value.Manifest.Effects != "simulate" {
		return "", errors.New("effect execution is unavailable until a passing security gate is active")
	}
	if strings.TrimSpace(input) == "" {
		return "", errors.New("run input is required")
	}
	path := []string{value.Manifest.EntryAgent}
	outcome := "abstained"
	selectedAction := ""
	reason := "no declared action matched; abstained"
	if unsafeInput(input) {
		outcome = "denied"
		reason = "conservative local safety rule denied the request before routing"
		path = append(path, "policy:deny")
	} else if action, score := selectAction(value.Actions, input); score > 0 {
		if action.OwnerAgent != "" && action.OwnerAgent != value.Manifest.EntryAgent {
			path = append(path, action.OwnerAgent)
		}
		path = append(path, action.ID)
		outcome = "routed"
		selectedAction = action.ID
		reason = "deterministic keyword match to declared action; effect remained simulated"
	}
	idBytes := make([]byte, 12)
	if _, err := rand.Read(idBytes); err != nil {
		return "", err
	}
	runID := hex.EncodeToString(idBytes)
	digest := sha256.Sum256([]byte(input))
	explanation := Explanation{RunID: runID, PackID: value.Manifest.ID, InputDigest: hex.EncodeToString(digest[:]), Path: path, Outcome: outcome, SelectedAction: selectedAction, Reason: reason, Mode: "simulate", EffectsExecuted: 0, CreatedAt: time.Now().UTC()}
	if err := engine.persist(explanation); err != nil {
		return "", err
	}
	return runID, nil
}

func (engine *Engine) Explain(runID string) (Explanation, error) {
	if !regexp.MustCompile(`^[0-9a-f]{24}$`).MatchString(runID) {
		return Explanation{}, errors.New("invalid run id")
	}
	data, err := os.ReadFile(filepath.Join(engine.stateDir, "runs", runID+".json"))
	if err != nil {
		return Explanation{}, err
	}
	var value Explanation
	decoder := json.NewDecoder(strings.NewReader(string(data)))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(&value); err != nil {
		return Explanation{}, err
	}
	return value, nil
}

func (engine *Engine) persist(value Explanation) error {
	directory := filepath.Join(engine.stateDir, "runs")
	if err := os.MkdirAll(directory, 0o700); err != nil {
		return err
	}
	data, err := json.MarshalIndent(value, "", "  ")
	if err != nil {
		return err
	}
	temporary, err := os.CreateTemp(directory, ".run-*.tmp")
	if err != nil {
		return err
	}
	path := temporary.Name()
	defer os.Remove(path)
	if err := temporary.Chmod(0o600); err != nil {
		temporary.Close()
		return err
	}
	if _, err := temporary.Write(append(data, '\n')); err != nil {
		temporary.Close()
		return err
	}
	if err := temporary.Sync(); err != nil {
		temporary.Close()
		return err
	}
	if err := temporary.Close(); err != nil {
		return err
	}
	return os.Rename(path, filepath.Join(directory, value.RunID+".json"))
}

func selectAction(actions []contracts.PackAction, input string) (contracts.PackAction, int) {
	inputTokens := tokens(input)
	type scored struct {
		action contracts.PackAction
		score  int
	}
	values := make([]scored, 0, len(actions))
	for _, action := range actions {
		score := 0
		for token := range tokens(action.ID + " " + action.Description) {
			if inputTokens[token] {
				score++
			}
		}
		values = append(values, scored{action: action, score: score})
	}
	sort.Slice(values, func(left, right int) bool {
		if values[left].score == values[right].score {
			return values[left].action.ID < values[right].action.ID
		}
		return values[left].score > values[right].score
	})
	if len(values) == 0 {
		return contracts.PackAction{}, 0
	}
	return values[0].action, values[0].score
}

func tokens(value string) map[string]bool {
	result := map[string]bool{}
	for _, token := range regexp.MustCompile(`[a-z0-9]+`).FindAllString(strings.ToLower(value), -1) {
		if normalized := normalizeToken(token); normalized != "" {
			result[normalized] = true
		}
	}
	return result
}

func normalizeToken(token string) string {
	aliases := map[string]string{
		"find": "search", "locate": "search", "search": "search",
		"summarize": "summarize", "summary": "summarize", "condense": "summarize", "brief": "summarize",
		"classify": "classify", "categorize": "classify", "category": "classify", "label": "classify",
	}
	if normalized := aliases[token]; normalized != "" {
		return normalized
	}
	stop := map[string]bool{
		"the": true, "this": true, "that": true, "with": true, "from": true, "into": true,
		"document": true, "documents": true, "file": true, "files": true, "text": true,
		"report": true, "reports": true, "note": true, "notes": true, "approved": true, "root": true,
	}
	if len(token) <= 2 || stop[token] {
		return ""
	}
	return token
}

func unsafeInput(input string) bool {
	normalized := strings.Join(regexp.MustCompile(`[a-z0-9]+`).FindAllString(strings.ToLower(input), -1), " ")
	for _, signal := range []string{
		"delete every", "disable security", "browser password", "environment secret", "exfiltrate",
		"outside the approved", "private ip", "wildcard command", "bypass approval",
		"web page instructions as policy", "modify the active agent policy", "ignore policy",
	} {
		if strings.Contains(normalized, signal) {
			return true
		}
	}
	return false
}
