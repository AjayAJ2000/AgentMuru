import pytest
import brickflowui.state as state
from brickflowui.state import (
    RenderContext,
    set_context,
    set_render_context,
    use_effect,
    use_memo,
    use_state,
)

@pytest.fixture
def ctx():
    c = RenderContext(session_id="test-session")
    token = set_render_context(c)
    yield c
    state.reset_render_context(token)

def test_use_state_initial(ctx):
    val, setter = use_state(42)
    assert val == 42
    assert ctx.state_slots[0] == 42

def test_use_state_update(ctx):
    val, setter = use_state(42)
    setter(100)
    assert ctx.state_slots[0] == 100
    assert ctx.dirty is True

def test_use_state_functional_update(ctx):
    val, setter = use_state(2)
    setter(lambda current: current + 3)
    assert ctx.state_slots[0] == 5

def test_use_state_no_rerender_when_value_unchanged(ctx):
    val, setter = use_state(2)
    setter(2)
    assert ctx.dirty is False

def test_use_state_multiple_hooks(ctx):
    v1, s1 = use_state("a")
    v2, s2 = use_state("b")
    
    assert v1 == "a"
    assert v2 == "b"
    assert len(ctx.state_slots) == 2
    
    ctx.reset_indices()
    v1_again, s1_again = use_state("a")
    v2_again, s2_again = use_state("b")
    
    assert v1_again == "a"
    assert v2_again == "b"

def test_use_memo(ctx):
    calls = 0
    def compute():
        nonlocal calls
        calls += 1
        return "result"

    # First call
    res = use_memo(compute, [1])
    assert res == "result"
    assert calls == 1
    
    ctx.reset_indices()
    # Second call with same deps
    res = use_memo(compute, [1])
    assert res == "result"
    assert calls == 1 # cached
    
    ctx.reset_indices()
    # Third call with new deps
    res = use_memo(compute, [2])
    assert res == "result"
    assert calls == 2 # recomputed

def test_use_effect_lifecycle(ctx):
    mounted = False
    
    def on_mount():
        nonlocal mounted
        mounted = True
        return lambda: setattr(pytest, "cleanup_called", True) # Hacky way to check cleanup

    # Render 1
    use_effect(on_mount, [])
    ctx.run_effects()
    assert mounted is True
    
    ctx.reset_indices()
    # Render 2
    use_effect(on_mount, [])
    ctx.run_effects()
    # Should not run again as deps are []
    # (Testing cleanup and re-run would require more complex setup but this covers basic registration)
    assert len(ctx.effects) == 1

def test_set_context_marks_session_dirty(ctx):
    set_context("user", {"id": "abc"})
    assert ctx.context["user"] == {"id": "abc"}
    assert ctx.dirty is True

def test_cleanup_effects_runs_registered_cleanup(ctx):
    cleaned = {"count": 0}

    def on_mount():
        return lambda: cleaned.__setitem__("count", cleaned["count"] + 1)

    use_effect(on_mount, [])
    ctx.run_effects()
    ctx.cleanup_effects()

    assert cleaned["count"] == 1
    assert ctx.effects == []


def test_reset_render_context_restores_previous_context():
    outer = RenderContext(session_id="outer")
    inner = RenderContext(session_id="inner")
    outer_token = set_render_context(outer)
    try:
        inner_token = set_render_context(inner)
        state.reset_render_context(inner_token)
        assert state.get_context() is outer
    finally:
        state.reset_render_context(outer_token)
