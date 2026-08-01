"""Virtual DOM: VNode definition, serialization, and diffing."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

EventHandler = Callable[..., None]
_MISSING = object()


def _serialize_prop_value(value: Any, handler_registry: Dict[str, EventHandler]) -> Any:
    """Convert VNodes nested in a prop into the JSON wire representation."""
    if isinstance(value, VNode):
        return value.serialize(handler_registry)
    if isinstance(value, list):
        return [_serialize_prop_value(item, handler_registry) for item in value]
    if isinstance(value, tuple):
        return [_serialize_prop_value(item, handler_registry) for item in value]
    if isinstance(value, dict):
        return {
            key: _serialize_prop_value(item, handler_registry)
            for key, item in value.items()
            if not callable(item)
        }
    return value


@dataclass
class VNode:
    """A node in the virtual UI tree."""

    type: str
    props: Dict[str, Any] = field(default_factory=dict)
    children: List["VNode"] = field(default_factory=list)
    key: Optional[str] = None
    # Maps event_id → callable; event_id is sent to frontend, callable is stored server-side
    event_handlers: Dict[str, EventHandler] = field(default_factory=dict)

    def serialize(self, handler_registry: Dict[str, EventHandler]) -> dict:
        """Serialize this node to a JSON-safe dict, registering event handlers."""
        serialized_handlers: Dict[str, str] = {}
        for event_name, handler in self.event_handlers.items():
            event_id = str(uuid.uuid4())
            handler_registry[event_id] = handler
            serialized_handlers[event_name] = event_id

        # Filter and recursively serialize props
        safe_props = {}
        for k, v in self.props.items():
            if callable(v):
                continue
            
            safe_props[k] = _serialize_prop_value(v, handler_registry)

        return {
            "type": self.type,
            "props": {**safe_props, **serialized_handlers},
            "children": [child.serialize(handler_registry) for child in self.children],
            "key": self.key,
        }


# ---------------------------------------------------------------------------
# Patch types for incremental updates
# ---------------------------------------------------------------------------


@dataclass
class ReplacePatch:
    path: List[int]  # child index path from root
    node: dict       # serialized new node


@dataclass
class UpdatePropsPatch:
    path: List[int]
    props: Dict[str, Any]


@dataclass
class InsertChildPatch:
    path: List[int]
    index: int
    node: dict


@dataclass
class RemoveChildPatch:
    path: List[int]
    index: int


Patch = ReplacePatch | UpdatePropsPatch | InsertChildPatch | RemoveChildPatch


def diff(
    old: Optional[VNode],
    new: Optional[VNode],
    handler_registry: Dict[str, EventHandler],
    path: Optional[List[int]] = None,
) -> List[dict]:
    """
    Compute a list of JSON patches from old→new virtual tree.
    Returns a list of JSON-safe patch dicts.
    """
    if path is None:
        path = []

    patches: List[dict] = []

    # Both None → nothing to do
    if old is None and new is None:
        return patches

    # Old gone, new appeared → parent should handle this via InsertChild
    if old is None:
        assert new is not None
        patches.append({
            "op": "insert",
            "path": path,
            "node": new.serialize(handler_registry),
        })
        return patches

    # New gone → remove
    if new is None:
        patches.append({"op": "remove", "path": path})
        return patches

    # Type changed → full replace
    if old.type != new.type:
        patches.append({
            "op": "replace",
            "path": path,
            "node": new.serialize(handler_registry),
        })
        return patches

    # Same type: diff props
    old_props_no_events = {k: v for k, v in old.props.items()}
    new_props_no_events = {k: v for k, v in new.props.items()}

    # Re-register event handlers for new node
    new_event_ids: Dict[str, str] = {}
    for event_name, handler in new.event_handlers.items():
        event_id = str(uuid.uuid4())
        handler_registry[event_id] = handler
        new_event_ids[event_name] = event_id

    prop_diff: Dict[str, Any] = {}
    all_keys = (
        set(old_props_no_events.keys())
        | set(new_props_no_events.keys())
        | set(old.event_handlers.keys())
        | set(new.event_handlers.keys())
    )
    for key in all_keys:
        new_val = new_event_ids[key] if key in new_event_ids else new_props_no_events.get(key, _MISSING)
        old_val = old_props_no_events.get(key, _MISSING)
        if new_val is _MISSING:
            prop_diff[key] = None
        elif new_val != old_val or key in new_event_ids:
            prop_diff[key] = _serialize_prop_value(new_val, handler_registry)

    if prop_diff:
        patches.append({"op": "update_props", "path": path, "props": prop_diff})

    # Diff children shared by both trees before changing the list shape.
    shared_len = min(len(old.children), len(new.children))
    for i in range(shared_len):
        patches.extend(
            diff(old.children[i], new.children[i], handler_registry, path + [i])
        )

    # Removals must run from the tail toward the shared prefix. Applying a
    # lower-index removal first would shift later indexes and invalidate the
    # remaining patch paths.
    for i in range(len(old.children) - 1, shared_len - 1, -1):
        patches.append({"op": "remove", "path": path + [i]})

    # Inserts remain valid in ascending order because each insertion extends
    # the list up to the next target index.
    for i in range(shared_len, len(new.children)):
        patches.append({
            "op": "insert",
            "path": path + [i],
            "node": new.children[i].serialize(handler_registry),
        })

    return patches
