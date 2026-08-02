import subprocess

import pytest

from scripts import runtime_resilience
from scripts.runtime_resilience import find_event_id, percentile


def test_percentile_uses_nearest_rank():
    assert percentile([10.0, 20.0, 30.0, 40.0], 95) == 40.0
    assert percentile([30.0, 10.0, 20.0], 50) == 20.0


def test_find_event_id_locates_named_button():
    tree = {
        "type": "Column",
        "props": {},
        "children": [
            {
                "type": "Button",
                "props": {"label": "+", "click": "event-1"},
                "children": [],
            }
        ],
    }

    assert find_event_id(tree, "+") == "event-1"


def test_find_event_id_rejects_missing_button():
    with pytest.raises(ValueError, match="button"):
        find_event_id({"type": "Text", "props": {}, "children": []}, "+")


def test_counter_output_does_not_use_a_bounded_pipe(monkeypatch):
    captured = {}

    def fake_popen(*args, **kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(runtime_resilience.subprocess, "Popen", fake_popen)

    runtime_resilience._spawn_counter(9180)

    assert captured["stdout"] is not subprocess.PIPE
