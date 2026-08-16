package ui

type LayoutMode string

const (
	LayoutSingle LayoutMode = "single"
	LayoutTabs   LayoutMode = "tabs"
	LayoutPanes  LayoutMode = "panes"
)

func SelectLayout(width int) LayoutMode {
	switch {
	case width < 70:
		return LayoutSingle
	case width < 100:
		return LayoutTabs
	default:
		return LayoutPanes
	}
}
