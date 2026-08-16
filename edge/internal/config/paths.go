package config

import (
	"errors"
	"os"
	"path/filepath"
	"runtime"
)

type Paths struct {
	Config string
	Cache  string
	Data   string
	State  string
}

func pathsUnder(root string) Paths {
	return Paths{
		Config: filepath.Join(root, "config"),
		Cache:  filepath.Join(root, "cache"),
		Data:   filepath.Join(root, "data"),
		State:  filepath.Join(root, "state"),
	}
}

func PathsForWindows(localAppData string) Paths {
	return pathsUnder(filepath.Join(localAppData, "AgentMuru"))
}

func DiscoverPaths() (Paths, error) {
	if runtime.GOOS == "windows" {
		localAppData := os.Getenv("LOCALAPPDATA")
		if localAppData == "" {
			return Paths{}, errors.New("LOCALAPPDATA is not set")
		}
		return PathsForWindows(localAppData), nil
	}

	home, err := os.UserHomeDir()
	if err != nil {
		return Paths{}, err
	}
	configHome := os.Getenv("XDG_CONFIG_HOME")
	if configHome == "" {
		configHome = filepath.Join(home, ".config")
	}
	cacheHome := os.Getenv("XDG_CACHE_HOME")
	if cacheHome == "" {
		cacheHome = filepath.Join(home, ".cache")
	}
	dataHome := os.Getenv("XDG_DATA_HOME")
	if dataHome == "" {
		dataHome = filepath.Join(home, ".local", "share")
	}
	stateHome := os.Getenv("XDG_STATE_HOME")
	if stateHome == "" {
		stateHome = filepath.Join(home, ".local", "state")
	}
	return Paths{
		Config: filepath.Join(configHome, "agentmuru"),
		Cache:  filepath.Join(cacheHome, "agentmuru"),
		Data:   filepath.Join(dataHome, "agentmuru"),
		State:  filepath.Join(stateHome, "agentmuru"),
	}, nil
}
