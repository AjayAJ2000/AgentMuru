package pack

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

func Export(path string, value contracts.AgentPack) error {
	if violations := Validate(value); len(violations) > 0 {
		return fmt.Errorf("cannot export invalid pack: %s", violations[0].Code)
	}
	if _, err := os.Stat(path); err == nil {
		return errors.New("output pack directory already exists")
	} else if !errors.Is(err, os.ErrNotExist) {
		return err
	}
	parent := filepath.Dir(path)
	if err := os.MkdirAll(parent, 0o700); err != nil {
		return err
	}
	temporary, err := os.MkdirTemp(parent, ".agentmuru-pack-*")
	if err != nil {
		return err
	}
	defer os.RemoveAll(temporary)

	agents := append([]contracts.AgentSpec(nil), value.Agents...)
	actions := append([]contracts.PackAction(nil), value.Actions...)
	sort.Slice(agents, func(left, right int) bool { return agents[left].ID < agents[right].ID })
	sort.Slice(actions, func(left, right int) bool { return actions[left].ID < actions[right].ID })
	files := map[string]any{"manifest.json": value.Manifest, "agents.json": agents, "actions.json": actions, "policy.json": value.Policy}
	checksums := map[string]string{}
	for name, content := range files {
		data, err := json.MarshalIndent(content, "", "  ")
		if err != nil {
			return err
		}
		data = append(data, '\n')
		if err := os.WriteFile(filepath.Join(temporary, name), data, 0o600); err != nil {
			return err
		}
		digest := sha256.Sum256(data)
		checksums[name] = hex.EncodeToString(digest[:])
	}
	var evalData []byte
	for _, eval := range value.Evals {
		line, err := json.Marshal(eval)
		if err != nil {
			return err
		}
		evalData = append(evalData, line...)
		evalData = append(evalData, '\n')
	}
	if err := os.WriteFile(filepath.Join(temporary, "evals.jsonl"), evalData, 0o600); err != nil {
		return err
	}
	digest := sha256.Sum256(evalData)
	checksums["evals.jsonl"] = hex.EncodeToString(digest[:])
	names := make([]string, 0, len(checksums))
	for name := range checksums {
		names = append(names, name)
	}
	sort.Strings(names)
	var lines []string
	for _, name := range names {
		lines = append(lines, checksums[name]+"  "+name)
	}
	if err := os.WriteFile(filepath.Join(temporary, "checksums.txt"), []byte(strings.Join(lines, "\n")+"\n"), 0o600); err != nil {
		return err
	}
	return os.Rename(temporary, path)
}
