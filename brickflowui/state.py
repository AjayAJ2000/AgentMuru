"""
State management for BrickflowUI.

Provides React-like hooks (use_state, use_effect, use_memo, use_context)
backed by a per-session RenderContext stored in contextvars.
"""

from __future__ import annotations

import asyncio
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Render context: one per session (WebSocket connection)
# ---------------------------------------------------------------------------

_current_context: ContextVar["RenderContext | None"] = ContextVar(
    "_current_context", default=None
)


@dataclass
class EffectRecord:
    fn: Callable
    deps: Optional[List[Any]]
    last_deps: Optional[List[Any]] = None
    cleanup: Optional[Callable] = None


@dataclass
class RenderContext:
    """Holds all hook state for a single user session."""

    session_id: str
    # State slots indexed by hook call order
    state_slots: List[Any] = field(default_factory=list)
    state_index: int = 0
    # Memo slots
    memo_slots: List[Tuple[Any, Optional[List[Any]]]] = field(default_factory=list)
    memo_index: int = 0
    # Effects to run after render
    effects: List[EffectRecord] = field(default_factory=list)
    effect_index: int = 0
    # Context store (cross-cutting values like current user, theme, etc.)
    context: Dict[str, Any] = field(default_factory=dict)
    # Whether a re-render is needed
    dirty: bool = False
    # Asyncio event to notify the WS sender that a re-render is needed
    rerender_event: Optional[asyncio.Event] = None

    def reset_indices(self) -> None:
        """Called before each render pass to reset hook indices."""
        self.state_index = 0
        self.memo_index = 0
        self.effect_index = 0

    def mark_dirty(self) -> None:
        """Signal that a re-render is needed."""
        self.dirty = True
        if self.rerender_event is not None:
            self.rerender_event.set()

    def run_effects(self) -> None:
        """Run any pending effects after render."""
        for record in self.effects:
            deps_changed = (
                record.last_deps is None
                or record.deps is None
                or record.deps != record.last_deps
            )
            if deps_changed:
                if record.cleanup is not None:
                    try:
                        record.cleanup()
                    except Exception:
                        pass
                cleanup = record.fn()
                record.cleanup = cleanup if callable(cleanup) else None
                record.last_deps = list(record.deps) if record.deps is not None else None

    def cleanup_effects(self) -> None:
        """Run registered cleanup handlers when a session or page is torn down."""
        for record in self.effects:
            if record.cleanup is None:
                continue
            try:
                record.cleanup()
            except Exception:
                pass
            finally:
                record.cleanup = None
        self.effects.clear()


# ---------------------------------------------------------------------------
# Context accessor
# ---------------------------------------------------------------------------


def get_context() -> RenderContext:
    ctx = _current_context.get()
    if ctx is None:
        raise RuntimeError(
            "Hooks called outside of a render context. "
            "Make sure your component is rendered via BrickflowUI."
        )
    return ctx


def set_render_context(ctx: "RenderContext | None") -> Any:
    return _current_context.set(ctx)


def reset_render_context(token: Any) -> None:
    """Restore the render context that was active before ``token`` was created."""
    _current_context.reset(token)


# ---------------------------------------------------------------------------
# Hooks
# ---------------------------------------------------------------------------


def use_state(initial: Any) -> Tuple[Any, Callable[[Any], None]]:
    """
    Returns (value, setter). Calling setter(new_value) will:
    - Update the stored value
    - Mark the session as dirty (triggers re-render)
    """
    ctx = get_context()
    idx = ctx.state_index
    ctx.state_index += 1

    # Grow slots list if needed
    if idx == len(ctx.state_slots):
        ctx.state_slots.append(initial)

    value = ctx.state_slots[idx]

    def setter(new_value: Any) -> None:
        current_value = ctx.state_slots[idx]
        if callable(new_value):
            new_value = new_value(current_value)
        if new_value == current_value:
            return
        ctx.state_slots[idx] = new_value
        ctx.mark_dirty()

    return value, setter


def use_effect(fn: Callable, deps: Optional[List[Any]] = None) -> None:
    """
    Registers a side-effect function to run after render.
    fn may return a cleanup callable.
    If deps is None, runs every render. If [], runs once on mount.
    """
    ctx = get_context()
    idx = ctx.effect_index
    ctx.effect_index += 1

    if idx == len(ctx.effects):
        ctx.effects.append(EffectRecord(fn=fn, deps=deps))
    else:
        ctx.effects[idx].fn = fn
        ctx.effects[idx].deps = deps


def use_memo(fn: Callable, deps: List[Any]) -> Any:
    """
    Returns a memoized result of fn(). Recomputes only when deps change.
    """
    ctx = get_context()
    idx = ctx.memo_index
    ctx.memo_index += 1

    if idx == len(ctx.memo_slots):
        value = fn()
        ctx.memo_slots.append((value, list(deps)))
        return value

    cached_value, cached_deps = ctx.memo_slots[idx]
    if deps != cached_deps:
        value = fn()
        ctx.memo_slots[idx] = (value, list(deps))
        return value

    return cached_value


def use_context(key: str, default: Any = None) -> Any:
    """
    Read a value from the session context store.
    Useful for cross-cutting concerns: current user, theme, feature flags.
    """
    ctx = get_context()
    return ctx.context.get(key, default)


def set_context(key: str, value: Any) -> None:
    """Write a value to the session context store."""
    ctx = get_context()
    if ctx.context.get(key) == value:
        return
    ctx.context[key] = value
    ctx.mark_dirty()
