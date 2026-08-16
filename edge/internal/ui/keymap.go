package ui

type KeyMap struct {
	Palette string
	Help    string
	Focus   string
	Jump    string
	Quit    string
}

func DefaultKeyMap() KeyMap {
	return KeyMap{Palette: "ctrl+p", Help: "?", Focus: "tab", Jump: "g", Quit: "q"}
}
