//go:build !windows

package catalog

import "os"

func replaceCacheFile(source, destination string) error {
	return os.Rename(source, destination)
}
