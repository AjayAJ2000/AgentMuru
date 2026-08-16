package overlay

func Help(width int) string {
	return framed([]string{
		"KEYBOARD + MOUSE",
		"Ctrl+P  command palette",
		"Tab     next pane",
		"g …     jump to pane",
		"/       filter run stream",
		"?       toggle help",
		"q       quit safely",
		"Mouse   focus visible pane",
		"Esc     close or cancel",
	}, min(width, 52))
}
