//go:build !windows

package ui

import "os"

func replaceFile(source, destination string) error {
	return os.Rename(source, destination)
}
