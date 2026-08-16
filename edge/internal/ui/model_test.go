package ui

import (
	"testing"
	"time"

	tea "charm.land/bubbletea/v2"
	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

func TestLayoutBreakpoints(t *testing.T) {
	cases := []struct {
		width int
		want  LayoutMode
	}{
		{width: 60, want: LayoutSingle},
		{width: 69, want: LayoutSingle},
		{width: 70, want: LayoutTabs},
		{width: 99, want: LayoutTabs},
		{width: 100, want: LayoutPanes},
		{width: 160, want: LayoutPanes},
	}
	for _, test := range cases {
		if got := SelectLayout(test.width); got != test.want {
			t.Errorf("SelectLayout(%d) = %q, want %q", test.width, got, test.want)
		}
	}
}

func TestRuntimeEventUpdatesAgentStatusWithoutTick(t *testing.T) {
	model := New(Dependencies{})
	event := contracts.Event{
		ID: "event-1", Type: "agent.started", Timestamp: time.Now().UTC(),
		SessionID: "session-1", Sequence: 1, Payload: map[string]any{"agent": "router"},
	}

	next, command := model.Update(RuntimeEventMsg{Event: event})
	updated := next.(*Model)

	if got := updated.AgentStatus("router"); got != "active" {
		t.Fatalf("AgentStatus(router) = %q, want active", got)
	}
	if command != nil {
		t.Fatal("event without a stream scheduled an unexpected command")
	}
}

func TestInitWaitsForEventInsteadOfSchedulingTicker(t *testing.T) {
	stream := make(chan contracts.Event, 1)
	stream <- contracts.Event{ID: "event-1", Type: "session.started"}
	model := New(Dependencies{Events: stream})

	command := model.Init()
	if command == nil {
		t.Fatal("Init() did not wait for the event stream")
	}
	message := command()
	if _, ok := message.(RuntimeEventMsg); !ok {
		t.Fatalf("Init command returned %T, want RuntimeEventMsg", message)
	}
}

func TestViewSanitizesUntrustedTerminalControls(t *testing.T) {
	model := New(Dependencies{})
	model.width = 100
	model.height = 30
	model.events = append(model.events, contracts.Event{
		ID: "event-1", Type: "tool.completed", Payload: map[string]any{
			"result": "safe\x1b]52;c;ZXhmaWx0cmF0ZQ==\a text",
		},
	})

	view := model.View()

	if containsEscape(view.Content) {
		t.Fatalf("View() contains terminal control sequence: %q", view.Content)
	}
	if view.MouseMode != tea.MouseModeCellMotion {
		t.Fatalf("MouseMode = %v, want cell motion", view.MouseMode)
	}
}
