package inference

import (
	"errors"
	"fmt"
	"regexp"
	"sort"
	"strings"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

var (
	ErrInvalidActionDescriptor = errors.New("invalid action descriptor")
	actionNamePattern          = regexp.MustCompile(`^[a-z][a-z0-9_]{0,63}$`)
)

func GrammarFor(actions []contracts.ActionDescriptor) (string, error) {
	if len(actions) == 0 {
		return "", fmt.Errorf("%w: at least one action is required", ErrInvalidActionDescriptor)
	}
	names := make([]string, 0, len(actions))
	seen := map[string]struct{}{}
	for _, action := range actions {
		if !actionNamePattern.MatchString(action.Name) {
			return "", fmt.Errorf("%w: unsafe action name %q", ErrInvalidActionDescriptor, action.Name)
		}
		if _, duplicate := seen[action.Name]; duplicate {
			return "", fmt.Errorf("%w: duplicate action %q", ErrInvalidActionDescriptor, action.Name)
		}
		seen[action.Name] = struct{}{}
		names = append(names, action.Name)
	}
	sort.Strings(names)
	literals := make([]string, len(names))
	for index, name := range names {
		literals[index] = fmt.Sprintf("\"\\\"%s\\\"\"", name)
	}
	return strings.Join([]string{
		`root ::= ws "{" ws "\"action\"" ws ":" ws action ws "," ws "\"arguments\"" ws ":" ws object (ws "," ws "\"abstain_reason\"" ws ":" ws string)? ws "}" ws`,
		`action ::= ` + strings.Join(literals, " | "),
		`object ::= "{" ws (string ws ":" ws value (ws "," ws string ws ":" ws value)*)? ws "}"`,
		`array ::= "[" ws (value (ws "," ws value)*)? ws "]"`,
		`value ::= object | array | string | number | "true" | "false" | "null"`,
		`string ::= "\"" ([^"\\] | "\\" ["\\/bfnrt] | "\\u" [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F])* "\""`,
		`number ::= "-"? ("0" | [1-9] [0-9]*) ("." [0-9]+)? ([eE] [+-]? [0-9]+)?`,
		`ws ::= [ \t\n\r]*`,
	}, "\n"), nil
}
