import pytest
from brickflowui.vdom import VNode, diff

def test_vnode_serialization():
    handler_registry = {}
    node = VNode(
        type="button",
        props={"className": "btn"},
        children=[VNode(type="text", props={"value": "Click me"})],
        event_handlers={"click": lambda: print("clicked")}
    )
    
    serialized = node.serialize(handler_registry)
    
    assert serialized["type"] == "button"
    assert serialized["props"]["className"] == "btn"
    assert "click" in serialized["props"]
    assert len(handler_registry) == 1
    assert serialized["children"][0]["type"] == "text"

def test_diff_replace_type():
    handler_registry = {}
    old = VNode(type="div")
    new = VNode(type="span")
    
    patches = diff(old, new, handler_registry)
    
    assert len(patches) == 1
    assert patches[0]["op"] == "replace"
    assert patches[0]["node"]["type"] == "span"

def test_diff_props():
    handler_registry = {}
    old = VNode(type="div", props={"color": "red"})
    new = VNode(type="div", props={"color": "blue", "size": "large"})
    
    patches = diff(old, new, handler_registry)
    
    assert len(patches) == 1
    assert patches[0]["op"] == "update_props"
    assert patches[0]["props"] == {"color": "blue", "size": "large"}

def test_diff_children_insertion():
    handler_registry = {}
    old = VNode(type="div", children=[VNode(type="span")])
    new = VNode(type="div", children=[
        VNode(type="span"),
        VNode(type="b")
    ])
    
    patches = diff(old, new, handler_registry)
    
    # In the current implementation, diffing children is index-based.
    # index 0: span vs span -> no patch
    # index 1: None vs b -> insert patch at path [1]
    assert len(patches) == 1
    assert patches[0]["op"] == "insert"
    assert patches[0]["path"] == [1]
    assert patches[0]["node"]["type"] == "b"

def test_diff_children_removal():
    handler_registry = {}
    old = VNode(type="div", children=[
        VNode(type="span"),
        VNode(type="b")
    ])
    new = VNode(type="div", children=[VNode(type="span")])
    
    patches = diff(old, new, handler_registry)
    
    assert len(patches) == 1
    assert patches[0]["op"] == "remove"
    assert patches[0]["path"] == [1]

def test_diff_multiple_child_removals_are_ordered_from_end():
    handler_registry = {}
    old = VNode(type="div", children=[
        VNode(type="span"),
        VNode(type="b"),
        VNode(type="i"),
        VNode(type="strong"),
    ])
    new = VNode(type="div", children=[VNode(type="span")])

    patches = diff(old, new, handler_registry)

    assert patches == [
        {"op": "remove", "path": [3]},
        {"op": "remove", "path": [2]},
        {"op": "remove", "path": [1]},
    ]

def test_diff_removed_prop_sets_null():
    handler_registry = {}
    old = VNode(type="div", props={"title": "hello", "color": "red"})
    new = VNode(type="div", props={"color": "red"})

    patches = diff(old, new, handler_registry)

    assert len(patches) == 1
    assert patches[0]["op"] == "update_props"
    assert patches[0]["props"] == {"title": None}
