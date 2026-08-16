package pack

import (
	"bufio"
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

func Load(path string) (contracts.AgentPack, error) {
	info, err := os.Stat(path)
	if err != nil {
		return contracts.AgentPack{}, err
	}
	if !info.IsDir() {
		return contracts.AgentPack{}, errors.New("agent packs must be unpacked directories")
	}
	var value contracts.AgentPack
	if err := decodeStrict(filepath.Join(path, "manifest.json"), &value.Manifest); err != nil {
		return value, err
	}
	if err := decodeStrict(filepath.Join(path, "agents.json"), &value.Agents); err != nil {
		return value, err
	}
	if err := decodeStrict(filepath.Join(path, "actions.json"), &value.Actions); err != nil {
		return value, err
	}
	if err := decodeStrict(filepath.Join(path, "policy.json"), &value.Policy); err != nil {
		return value, err
	}
	evalFile, err := os.Open(filepath.Join(path, "evals.jsonl"))
	if err != nil {
		return value, err
	}
	defer evalFile.Close()
	scanner := bufio.NewScanner(evalFile)
	for scanner.Scan() {
		var eval contracts.PackEvalCase
		decoder := json.NewDecoder(bytes.NewReader(scanner.Bytes()))
		decoder.DisallowUnknownFields()
		if err := decoder.Decode(&eval); err != nil {
			return value, fmt.Errorf("decode eval: %w", err)
		}
		value.Evals = append(value.Evals, eval)
	}
	if err := scanner.Err(); err != nil {
		return value, err
	}
	if err := verifyChecksums(path); err != nil {
		return value, err
	}
	if violations := Validate(value); len(violations) > 0 {
		return value, fmt.Errorf("agent pack validation failed: %s", violations[0].Code)
	}
	return value, nil
}

func decodeStrict(path string, destination any) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	decoder := json.NewDecoder(bytes.NewReader(data))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(destination); err != nil {
		return fmt.Errorf("decode %s: %w", filepath.Base(path), err)
	}
	return nil
}

func verifyChecksums(root string) error {
	data, err := os.ReadFile(filepath.Join(root, "checksums.txt"))
	if errors.Is(err, os.ErrNotExist) {
		return errors.New("pack checksum manifest is required")
	}
	if err != nil {
		return err
	}
	seen := map[string]bool{}
	for _, line := range strings.Split(strings.TrimSpace(string(data)), "\n") {
		parts := strings.Fields(line)
		if len(parts) != 2 || len(parts[0]) != 64 || filepath.IsAbs(parts[1]) || strings.Contains(parts[1], "..") {
			return errors.New("invalid pack checksum entry")
		}
		name := filepath.ToSlash(filepath.Clean(parts[1]))
		if seen[name] {
			return fmt.Errorf("duplicate pack checksum for %s", name)
		}
		seen[name] = true
		content, err := os.ReadFile(filepath.Join(root, filepath.FromSlash(parts[1])))
		if err != nil {
			return err
		}
		digest := sha256.Sum256(content)
		if hex.EncodeToString(digest[:]) != parts[0] {
			return fmt.Errorf("pack checksum mismatch for %s", parts[1])
		}
	}
	for _, required := range []string{"actions.json", "agents.json", "evals.jsonl", "manifest.json", "policy.json"} {
		if !seen[required] {
			return fmt.Errorf("missing checksum for %s", required)
		}
	}
	return nil
}
