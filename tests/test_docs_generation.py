import inspect

from brickflowui import components
from scripts.generate_component_reference import build_example


def test_progress_reference_uses_a_numeric_value():
    example = build_example("Progress", inspect.signature(components.Progress))

    assert "value=85" in example
    assert 'value="active"' not in example
