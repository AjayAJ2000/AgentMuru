//go:build !windows

package download

import "os"

func promoteFile(source, destination string) error {
	return os.Rename(source, destination)
}
