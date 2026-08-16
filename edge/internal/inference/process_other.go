//go:build !windows

package inference

type processGuard struct{}

func attachProcess(int) (*processGuard, error) { return &processGuard{}, nil }
func (*processGuard) Close() error             { return nil }
