package ui

type Theme struct {
	Active   string
	Complete string
	Failed   string
	Waiting  string
}

func DefaultTheme() Theme {
	return Theme{Active: "RUN", Complete: "OK", Failed: "ERR", Waiting: "WAIT"}
}
