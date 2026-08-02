import json

import pytest

from brickflowui.vdom import VNode, diff


def _text_children(count: int, prefix: str = "item") -> list[VNode]:
    return [
        VNode(type="Text", props={"value": f"{prefix}-{index}"})
        for index in range(count)
    ]


def _apply_serialized_patches(tree: dict, patches: list[dict]) -> dict:
    result = json.loads(json.dumps(tree))

    for patch in patches:
        path = patch["path"]
        if not path:
            if patch["op"] == "replace":
                result = patch["node"]
                continue
            if patch["op"] == "update_props":
                for key, value in patch["props"].items():
                    if value is None:
                        result["props"].pop(key, None)
                    else:
                        result["props"][key] = value
                continue
            raise AssertionError(f"Unsupported root patch in test helper: {patch}")

        parent = result
        for index in path[:-1]:
            parent = parent["children"][index]
        index = path[-1]

        if patch["op"] == "remove":
            parent["children"].pop(index)
        elif patch["op"] == "insert":
            parent["children"].insert(index, patch["node"])
        elif patch["op"] == "replace":
            parent["children"][index] = patch["node"]
        elif patch["op"] == "update_props":
            props = parent["children"][index]["props"]
            for key, value in patch["props"].items():
                if value is None:
                    props.pop(key, None)
                else:
                    props[key] = value
        else:
            raise AssertionError(f"Unsupported patch in test helper: {patch}")

    return result


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

def test_diff_removes_surplus_children_from_highest_index_first():
    patches = diff(
        VNode(type="Column", children=_text_children(5)),
        VNode(type="Column", children=_text_children(1)),
        {},
    )

    assert [
        patch["path"] for patch in patches if patch["op"] == "remove"
    ] == [[4], [3], [2], [1]]


def test_diff_removes_all_children_from_highest_index_first():
    patches = diff(
        VNode(type="Column", children=_text_children(5)),
        VNode(type="Column"),
        {},
    )

    assert [
        patch["path"] for patch in patches if patch["op"] == "remove"
    ] == [[4], [3], [2], [1], [0]]


def test_diff_removes_nested_surplus_children_from_highest_index_first():
    patches = diff(
        VNode(
            type="Column",
            children=[VNode(type="Row", children=_text_children(5))],
        ),
        VNode(
            type="Column",
            children=[VNode(type="Row", children=_text_children(1))],
        ),
        {},
    )

    assert [
        patch["path"] for patch in patches if patch["op"] == "remove"
    ] == [[0, 4], [0, 3], [0, 2], [0, 1]]


def test_diff_updates_shared_children_before_descending_removals():
    patches = diff(
        VNode(type="Column", children=_text_children(5, "old")),
        VNode(
            type="Column",
            children=[VNode(type="Text", props={"value": "updated"})],
        ),
        {},
    )

    assert patches[0] == {
        "op": "update_props",
        "path": [0],
        "props": {"value": "updated"},
    }
    assert [
        patch["path"] for patch in patches if patch["op"] == "remove"
    ] == [[4], [3], [2], [1]]


def test_diff_inserts_surplus_children_from_lowest_index_first():
    patches = diff(
        VNode(type="Column", children=_text_children(1)),
        VNode(type="Column", children=_text_children(5)),
        {},
    )

    assert [
        patch["path"] for patch in patches if patch["op"] == "insert"
    ] == [[1], [2], [3], [4]]


@pytest.mark.parametrize(
    ("old_count", "new_count"),
    [(old_count, new_count) for old_count in range(13) for new_count in range(13)],
)
def test_diff_patches_apply_across_child_count_matrix(old_count, new_count):
    old = VNode(type="Column", children=_text_children(old_count))
    new = VNode(type="Column", children=_text_children(new_count))
    old_serialized = old.serialize({})
    new_serialized = new.serialize({})

    patches = diff(old, new, {})

    assert _apply_serialized_patches(old_serialized, patches) == new_serialized

    nested_old = VNode(type="Column", children=[old])
    nested_new = VNode(type="Column", children=[new])
    nested_old_serialized = nested_old.serialize({})
    nested_new_serialized = nested_new.serialize({})

    nested_patches = diff(nested_old, nested_new, {})

    assert (
        _apply_serialized_patches(nested_old_serialized, nested_patches)
        == nested_new_serialized
    )


def test_diff_applies_replacement_before_descending_adjacent_removals():
    old = VNode(
        type="Column",
        children=[
            VNode(type="Text", props={"value": "keep"}),
            VNode(type="Row"),
            VNode(type="Badge"),
            VNode(type="Card"),
        ],
    )
    new = VNode(
        type="Column",
        children=[
            VNode(type="Text", props={"value": "keep"}),
            VNode(type="Grid"),
        ],
    )
    old_serialized = old.serialize({})
    new_serialized = new.serialize({})

    patches = diff(old, new, {})

    assert [(patch["op"], patch["path"]) for patch in patches] == [
        ("replace", [1]),
        ("remove", [3]),
        ("remove", [2]),
    ]
    assert _apply_serialized_patches(old_serialized, patches) == new_serialized

def test_diff_removed_prop_sets_null():
    handler_registry = {}
    old = VNode(type="div", props={"title": "hello", "color": "red"})
    new = VNode(type="div", props={"color": "red"})

    patches = diff(old, new, handler_registry)

    assert len(patches) == 1
    assert patches[0]["op"] == "update_props"
    assert patches[0]["props"] == {"title": None}


def test_diff_serializes_vnodes_nested_in_changed_props():
    handler_registry = {}
    old = VNode(
        type="Hero",
        props={"actions": [VNode(type="Button", props={"label": "Export"})]},
    )
    new = VNode(
        type="Hero",
        props={
            "actions": [
                VNode(
                    type="Button",
                    props={"label": "Export"},
                    event_handlers={"click": lambda: None},
                )
            ]
        },
    )

    patches = diff(old, new, handler_registry)

    assert patches[0]["op"] == "update_props"
    assert patches[0]["props"]["actions"][0]["type"] == "Button"
    assert "click" in patches[0]["props"]["actions"][0]["props"]
    assert len(handler_registry) == 1
    json.dumps(patches)
