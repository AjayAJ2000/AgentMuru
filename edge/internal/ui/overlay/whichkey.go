package overlay

func WhichKey(width int) string {
	return framed([]string{
		"GO TO",
		"a  agent map",
		"r  run stream",
		"i  inspector",
		"s  resources",
	}, min(width, 42))
}
