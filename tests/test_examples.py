from __future__ import annotations

import json
from collections.abc import Mapping
import os
from pathlib import Path
import re
import runpy
import subprocess
import uuid

import pytest
from fastapi.testclient import TestClient

from brickflowui.server import create_asgi_app
from scripts.example_manifest import load_example_manifest

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_ROOT = REPO_ROOT / "examples"

MAINTAINED_EXAMPLES = {
    "auth_portal",
    "chatbot_workspace",
    "component_studio",
    "clinical_trial_command_center",
    "data_pipeline_command_center",
    "counter",
}

PUBLIC_RUNTIME_SMOKE_EXAMPLES = (
    "counter",
    "component_studio",
    "data_pipeline_command_center",
    "auth_portal",
    "chatbot_workspace",
)

MEDIA_PROP_KEYS = frozenset({"src", "poster", "logo", "favicon", "avatar", "image"})
REMOTE_MEDIA_PREFIXES = ("http://", "https://", "data:", "blob:")


def _load_example_app(example_name: str):
    app_path = EXAMPLES_ROOT / example_name / "app.py"
    namespace = runpy.run_path(
        str(app_path),
        run_name=f"brickflowui_example_{example_name}",
    )
    return namespace["app"]


def _iter_media_props(payload: object):
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in MEDIA_PROP_KEYS:
                yield key, value
            yield from _iter_media_props(value)
    elif isinstance(payload, list):
        for value in payload:
            yield from _iter_media_props(value)


def _find_payload_nodes(payload: object, node_type: str) -> list[dict]:
    found: list[dict] = []
    if isinstance(payload, dict):
        if payload.get("type") == node_type:
            found.append(payload)
        for value in payload.values():
            found.extend(_find_payload_nodes(value, node_type))
    elif isinstance(payload, list):
        for value in payload:
            found.extend(_find_payload_nodes(value, node_type))
    return found


def _assert_media_value_stays_in_example(app, root: Path, value: object) -> None:
    if not isinstance(value, (str, Path)):
        return

    raw = str(value)
    if raw.lower().startswith(REMOTE_MEDIA_PREFIXES):
        return

    if raw.startswith("/__brickflow_asset__/"):
        asset_id = raw.split("/", 3)[2]
        asset_path = app.get_registered_asset(asset_id)
        assert asset_path is not None, f"Unregistered app asset URL: {raw}"
        assert asset_path.is_file(), f"Missing app asset: {asset_path}"
        resolved_root = root.resolve()
        assert asset_path == resolved_root or resolved_root in asset_path.parents
        return

    asset_path = Path(raw).expanduser().resolve()
    resolved_root = root.resolve()
    assert asset_path == resolved_root or resolved_root in asset_path.parents


def test_maintained_example_manifest_is_complete() -> None:
    specs = load_example_manifest(REPO_ROOT)

    assert [spec.name for spec in specs] == [
        "counter",
        "component_studio",
        "data_pipeline_command_center",
        "clinical_trial_command_center",
        "auth_portal",
        "chatbot_workspace",
    ]
    assert len({spec.name for spec in specs}) == len(specs)
    for spec in specs:
        root = EXAMPLES_ROOT / spec.name
        assert (root / "app.py").is_file()
        assert (root / "requirements.txt").is_file()
        assert (root / "app.yaml").is_file()


def test_examples_directory_matches_manifest() -> None:
    declared = {spec.name for spec in load_example_manifest(REPO_ROOT)}
    actual = {path.name for path in EXAMPLES_ROOT.iterdir() if path.is_dir()}

    assert actual == declared


def test_tracked_files_do_not_reference_removed_examples() -> None:
    removed = {
        "_".join(parts)
        for parts in (
            ("acme", "analytics", "command", "center"),
            ("geometric", "signal", "lab"),
            ("landing", "site"),
            ("local", "playground"),
            ("operations", "finance", "portal"),
            ("pipeline", "observability", "015"),
            ("secure", "internal", "tools"),
            ("weather", "dashboard"),
            ("workspace", "studio"),
        )
    }
    tracked_paths = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    ).stdout.decode("utf-8", errors="surrogateescape")
    gitlinks = {
        entry.split(b"\t", 1)[1].decode("utf-8", errors="surrogateescape")
        for entry in subprocess.run(
            ["git", "ls-files", "--stage", "-z"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        ).stdout.split(b"\0")
        if entry.startswith(b"160000 ")
    }
    removed_bytes = {name: name.encode("ascii") for name in removed}
    missing_regular_files: list[str] = []
    references: dict[str, list[str]] = {}

    for relative_path in filter(None, tracked_paths.split("\0")):
        if relative_path in gitlinks:
            continue

        path = REPO_ROOT / relative_path
        if path.is_dir():
            missing_regular_files.append(relative_path)
            continue

        try:
            content = path.read_bytes()
        except FileNotFoundError:
            missing_regular_files.append(relative_path)
            continue

        matches = sorted(
            name for name, encoded_name in removed_bytes.items() if encoded_name in content
        )
        if matches:
            references[relative_path] = matches

    assert not missing_regular_files, (
        f"Tracked regular files disappeared while scanning: {missing_regular_files}"
    )
    assert not references


def test_maintained_examples_are_self_contained() -> None:
    for spec in load_example_manifest(REPO_ROOT):
        root = EXAMPLES_ROOT / spec.name
        source = (root / "app.py").read_text(encoding="utf-8-sig")

        assert "sys.path" not in source
        assert "../../" not in source.replace("\\\\", "/")
        assert "brickflowui" in (root / "requirements.txt").read_text(encoding="utf-8").lower()
        manifest = (root / "app.yaml").read_text(encoding="utf-8")
        assert "python" in manifest and "app.py" in manifest


def test_retained_examples_do_not_borrow_external_brand_copy() -> None:
    forbidden_brands = {b"astellas", b"inspired"}
    references: dict[str, list[str]] = {}
    retained_paths = [f"examples/{name}" for name in sorted(MAINTAINED_EXAMPLES)]
    tracked_files = subprocess.run(
        ["git", "ls-files", "-z", "--", *retained_paths],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    ).stdout.split(b"\0")

    for relative_path_bytes in filter(None, tracked_files):
        relative_path = relative_path_bytes.decode(
            "utf-8", errors="surrogateescape"
        )
        content = (REPO_ROOT / relative_path).read_bytes().lower()
        matches = sorted(
            brand.decode("ascii")
            for brand in forbidden_brands
            if brand in content
        )
        if matches:
            references[relative_path] = matches

    assert not references


def test_component_studio_does_not_embed_a_release_version() -> None:
    source = (EXAMPLES_ROOT / "component_studio" / "app.py").read_text(
        encoding="utf-8-sig"
    )

    assert not re.search(r"\b\d+\.\d+\.\d+\b", source)


def test_manifest_auth_headers_are_immutable() -> None:
    specs = load_example_manifest(REPO_ROOT)
    clinical_trial = next(spec for spec in specs if spec.name == "clinical_trial_command_center")

    assert isinstance(clinical_trial.auth_headers, Mapping)
    assert not isinstance(clinical_trial.auth_headers, dict)
    with pytest.raises(TypeError):
        clinical_trial.auth_headers["x-brickflow-user-id"] = "changed@example.com"


def test_repository_tooling_is_tracked_candidate() -> None:
    for tool_path in (
        "scripts/smoke_examples.py",
        "scripts/cleanup_local_artifacts.ps1",
    ):
        result = subprocess.run(
            ["git", "check-ignore", "--quiet", tool_path],
            cwd=REPO_ROOT,
            check=False,
        )
        assert result.returncode == 1, f"{tool_path} must not be ignored"


def test_smoke_runner_uses_the_maintained_manifest() -> None:
    from scripts.smoke_examples import configured_checks

    assert [item.name for item in configured_checks(REPO_ROOT)] == [
        spec.name for spec in load_example_manifest(REPO_ROOT)
    ]


def test_smoke_tree_validator_rejects_unrecognizable_vdom_root() -> None:
    from scripts.smoke_examples import validate_full_tree

    with pytest.raises(RuntimeError, match="non-empty VDOM root"):
        validate_full_tree({"type": "full", "tree": {"unexpected": True}}, "/")


def test_smoke_tree_validator_accepts_vdom_root() -> None:
    from scripts.smoke_examples import validate_full_tree

    validate_full_tree({"type": "full", "tree": {"type": "div", "children": []}}, "/")


@pytest.mark.skipif(os.name != "nt", reason="PowerShell reparse points are Windows-only")
def test_cleanup_rejects_reparse_target() -> None:
    test_root = REPO_ROOT / ".tmp" / f"cleanup-reparse-{uuid.uuid4().hex}"
    target = test_root / "target"
    target.mkdir(parents=True)
    reparse_target = test_root / "reparse-target"
    try:
        os.symlink(target, reparse_target, target_is_directory=True)
    except OSError as exc:
        target.rmdir()
        test_root.rmdir()
        pytest.skip(f"Symlink creation is not supported: {exc}")
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                "scripts/cleanup_local_artifacts.ps1",
                "-ValidateTarget",
                str(reparse_target),
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        assert result.returncode != 0
        assert "Refusing cleanup through reparse point" in result.stderr
    finally:
        reparse_target.unlink(missing_ok=True)
        target.rmdir()
        test_root.rmdir()


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"schema_version": 2, "examples": []}, "Unsupported examples manifest schema_version"),
        ({"schema_version": 1, "examples": {}}, "examples must be a list"),
        (
            {
                "schema_version": 1,
                "examples": [
                    {"name": "counter", "title": "Counter", "kind": "quickstart", "routes": ["/"], "auth_headers": {}},
                    {"name": "counter", "title": "Counter", "kind": "quickstart", "routes": ["/"], "auth_headers": {}},
                ],
            },
            "Example names must be unique",
        ),
        (
            {
                "schema_version": 1,
                "examples": [{"name": "../counter", "title": "Counter", "kind": "quickstart", "routes": ["/"], "auth_headers": {}}],
            },
            "Example name must be a relative directory name",
        ),
        (
            {
                "schema_version": 1,
                "examples": [{"name": "counter", "title": "Counter", "kind": "quickstart", "routes": [], "auth_headers": {}}],
            },
            "Example routes must be a non-empty list of strings",
        ),
        (
            {
                "schema_version": 1,
                "examples": [{"name": "counter", "title": "Counter", "kind": "quickstart", "routes": ["/"], "auth_headers": {"x-user": 1}}],
            },
            "Example auth_headers must map strings to strings",
        ),
    ],
)
def test_manifest_rejects_invalid_configuration(
    tmp_path: Path, payload: dict[str, object], message: str
) -> None:
    manifest_path = tmp_path / "examples" / "manifest.json"
    manifest_path.parent.mkdir()
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        load_example_manifest(tmp_path)


@pytest.mark.parametrize(
    "name",
    (
        "counter ",
        "counter.",
        "NUL",
        "nul",
        "CON",
        "PRN",
        "AUX",
        "COM1",
        "LPT9",
        "com\u00b9",
        "COM\u00b2",
        "com\u00b3",
        "lpt\u00b9",
        "LPT\u00b2",
        "lpt\u00b3",
        "foo<bar",
        "foo>bar",
        'foo"bar',
        "foo:bar",
        "foo/bar",
        r"foo\bar",
        "foo|bar",
        "foo?bar",
        "foo*bar",
        "foo\u0001bar",
        "foo\u001fbar",
    ),
)
def test_manifest_rejects_windows_aliasing_names(tmp_path: Path, name: str) -> None:
    manifest_path = tmp_path / "examples" / "manifest.json"
    manifest_path.parent.mkdir()
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "examples": [
                    {
                        "name": name,
                        "title": "Counter",
                        "kind": "quickstart",
                        "routes": ["/"],
                        "auth_headers": {},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Example name must be a relative directory name"):
        load_example_manifest(tmp_path)


def test_every_example_app_compiles() -> None:
    example_apps = sorted(EXAMPLES_ROOT.glob("*/app.py"))

    assert example_apps, "Expected at least one example app."

    for app_path in example_apps:
        source = app_path.read_text(encoding="utf-8-sig")
        compile(source, str(app_path), "exec")


def test_maintained_examples_exist() -> None:
    available_examples = {path.name for path in EXAMPLES_ROOT.iterdir() if path.is_dir()}

    assert MAINTAINED_EXAMPLES.issubset(available_examples)


def test_retained_example_routes_render_with_self_contained_media() -> None:
    for spec in load_example_manifest(REPO_ROOT):
        root = EXAMPLES_ROOT / spec.name
        app = _load_example_app(spec.name)
        client = TestClient(create_asgi_app(app))

        for route in spec.routes:
            response = client.get(route, headers=dict(spec.auth_headers))
            assert response.status_code == 200, f"{spec.name} did not serve {route}"

            with client.websocket_connect(
                f"/events?path={route}", headers=dict(spec.auth_headers)
            ) as websocket:
                payload = websocket.receive_json()

            assert payload["type"] == "full"
            tree = payload["tree"]
            json.dumps(tree)
            for _, value in _iter_media_props(tree):
                _assert_media_value_stays_in_example(app, root, value)


def test_flagship_exposes_complete_operational_views() -> None:
    namespace = runpy.run_path(
        str(EXAMPLES_ROOT / "data_pipeline_command_center" / "app.py")
    )

    rows = namespace["load_pipeline_records"]("mock")
    nodes, edges = namespace["pipeline_flow"](rows)
    columns = namespace["triage_columns"](rows)

    assert rows and all("pipeline" in row for row in rows)
    assert len({row["pipeline"] for row in rows}) == len(rows)
    assert {node["id"] for node in nodes} == {row["pipeline"] for row in rows}
    assert all(edge["from"] != edge["to"] for edge in edges)
    assert [column["id"] for column in columns] == ["healthy", "watch", "at-risk"]
    assert {
        card["id"] for column in columns for card in column["cards"]
    } == {row["pipeline"] for row in rows}


def test_flagship_source_result_reports_sql_success_and_safe_fallback(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    namespace = runpy.run_path(
        str(EXAMPLES_ROOT / "data_pipeline_command_center" / "app.py")
    )
    load_pipeline_source = namespace["load_pipeline_source"]
    sql_module = pytest.importorskip("brickflowui.databricks.sql")
    sql_rows = [{**namespace["PIPELINE_RECORDS"][0], "pipeline": "sql_customer"}]
    monkeypatch.setenv("DEMO_PIPELINE_METRICS_TABLE", "main.ops.pipeline_metrics")
    monkeypatch.setattr(sql_module, "query_to_records", lambda _: sql_rows)

    rows, source = load_pipeline_source("sql")

    assert rows == sql_rows
    assert source == {
        "requested": "sql",
        "active": "sql",
        "fallback": False,
        "error": None,
    }

    def unavailable(_: str) -> list[dict]:
        raise RuntimeError("warehouse secret must not escape")

    monkeypatch.setattr(sql_module, "query_to_records", unavailable)
    rows, source = load_pipeline_source("sql")

    assert rows == namespace["PIPELINE_RECORDS"]
    assert source == {
        "requested": "sql",
        "active": "mock",
        "fallback": True,
        "error": "SQL source unavailable",
    }
    assert "warehouse secret" not in json.dumps(source)
    assert "warehouse secret must not escape" in caplog.text


def test_flagship_charts_only_render_the_filtered_scope() -> None:
    namespace = runpy.run_path(
        str(EXAMPLES_ROOT / "data_pipeline_command_center" / "app.py")
    )
    selected = [namespace["PIPELINE_RECORDS"][3]]
    overview = namespace["overview_page"](
        selected, "YTD", False, lambda _: None
    ).serialize({})
    reliability = namespace["reliability_page"](
        selected, "No signal selected", lambda _: None
    ).serialize({})

    overview_chart = _find_payload_nodes(overview, "ComposedChart")[0]
    reliability_chart = _find_payload_nodes(reliability, "ComposedChart")[0]
    heatmap = _find_payload_nodes(reliability, "Heatmap")[0]
    assert overview_chart["props"]["data"] == [
        {
            "scope": "ML Features",
            "rows_m": 96,
            "cost_usd": 219,
            "sla_pct": 96.8,
        }
    ]
    assert reliability_chart["props"]["data"] == overview_chart["props"]["data"]
    assert heatmap["props"]["data"] == [
        {
            "pipeline": "ML Features",
            "layer": "silver",
            "failures": 4,
        }
    ]

    empty_overview = namespace["overview_page"](
        [], "YTD", False, lambda _: None
    ).serialize({})
    empty_reliability = namespace["reliability_page"](
        [], "No signal selected", lambda _: None
    ).serialize({})
    assert not _find_payload_nodes(empty_overview, "ComposedChart")
    assert not _find_payload_nodes(empty_reliability, "ComposedChart")
    assert not _find_payload_nodes(empty_reliability, "ScatterChart")
    assert not _find_payload_nodes(empty_reliability, "Heatmap")


def test_flagship_emits_status_values_supported_by_the_renderer() -> None:
    namespace = runpy.run_path(
        str(EXAMPLES_ROOT / "data_pipeline_command_center" / "app.py")
    )
    at_risk = [
        row for row in namespace["PIPELINE_RECORDS"] if row["status"] == "At Risk"
    ]
    nodes, _ = namespace["pipeline_flow"](at_risk)
    columns = namespace["triage_columns"](at_risk)

    assert nodes[0]["status"] == "at risk"
    assert columns[2]["id"] == "at-risk"
    assert columns[2]["cards"][0]["status"] == "at risk"


def test_flagship_header_navigation_wraps_without_hiding_mobile_controls() -> None:
    namespace = runpy.run_path(
        str(EXAMPLES_ROOT / "data_pipeline_command_center" / "app.py")
    )
    header = namespace["top_nav"](
        "overview", lambda _: None, lambda _: None
    ).serialize({})
    outer_row = header["children"][0]
    brand, navigation = outer_row["children"]

    assert outer_row["props"]["wrap"] is True
    assert brand["props"]["style"] == {
        "width": "auto",
        "flex": "0 0 auto",
    }
    assert navigation["props"]["wrap"] is True
    assert navigation["props"]["style"] == {
        "width": "auto",
        "flex": "0 1 auto",
        "minWidth": "0",
        "justifyContent": "flex-start",
    }


def test_flagship_websocket_reports_actual_sql_source_transitions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    namespace = runpy.run_path(
        str(EXAMPLES_ROOT / "data_pipeline_command_center" / "app.py")
    )
    sql_module = pytest.importorskip("brickflowui.databricks.sql")
    monkeypatch.setenv("DEMO_PIPELINE_METRICS_TABLE", "main.ops.pipeline_metrics")
    app = namespace["app"]
    client = TestClient(create_asgi_app(app))

    def select_sql() -> dict:
        with client.websocket_connect("/events?path=/") as websocket:
            full = websocket.receive_json()
            source_select = next(
                node
                for node in _find_payload_nodes(full, "Select")
                if node["props"]["name"] == "source_mode"
            )
            websocket.send_json(
                {
                    "type": "event",
                    "event_id": source_select["props"]["change"],
                    "data": {"value": "sql"},
                }
            )
            return websocket.receive_json()

    monkeypatch.setattr(
        sql_module,
        "query_to_records",
        lambda _: [{**namespace["PIPELINE_RECORDS"][0], "pipeline": "from_sql"}],
    )
    success = select_sql()
    assert success["type"] == "patch"
    assert "SQL source active" in json.dumps(success)
    assert "Active: SQL" in json.dumps(success)

    def unavailable(_: str) -> list[dict]:
        raise RuntimeError("private warehouse detail")

    monkeypatch.setattr(sql_module, "query_to_records", unavailable)
    fallback = select_sql()
    serialized_fallback = json.dumps(fallback)
    assert fallback["type"] == "patch"
    assert "SQL fallback active" in serialized_fallback
    assert "SQL source unavailable" in serialized_fallback
    assert "Active: MOCK" in serialized_fallback
    assert "private warehouse detail" not in serialized_fallback


def test_flagship_websocket_covers_operational_state_transitions() -> None:
    namespace = runpy.run_path(
        str(EXAMPLES_ROOT / "data_pipeline_command_center" / "app.py")
    )
    client = TestClient(create_asgi_app(namespace["app"]))

    def send_event(websocket, node: dict, event_name: str, value: object) -> dict:
        websocket.send_json(
            {
                "type": "event",
                "event_id": node["props"][event_name],
                "data": {"value": value},
            }
        )
        response = websocket.receive_json()
        assert response["type"] == "patch", response
        return response

    def view_button(payload: object, view_key: str) -> dict:
        return next(
            node
            for node in _find_payload_nodes(payload, "Button")
            if node["props"].get("viewKey") == view_key
        )

    with client.websocket_connect("/events?path=/") as websocket:
        full = websocket.receive_json()
        search = next(
            node
            for node in _find_payload_nodes(full, "Input")
            if node["props"]["name"] == "search"
        )
        empty = send_event(websocket, search, "change", "no-such-pipeline")
        serialized_empty = json.dumps(empty)
        assert "Empty filtered result" in serialized_empty
        assert "No pipelines match the current filters" in serialized_empty

    with client.websocket_connect("/events?path=/") as websocket:
        full = websocket.receive_json()
        pipelines = send_event(
            websocket, view_button(full, "pipelines"), "click", None
        )
        assert websocket.receive_json()["type"] == "event_complete"
        graph = _find_payload_nodes(pipelines, "PipelineGraph")[0]
        selection = send_event(
            websocket,
            graph,
            "nodeClick",
            {"id": "ml_features", "label": "ML Features", "status": "at risk"},
        )
        assert "ML Features selected for operational review" in json.dumps(selection)

    with client.websocket_connect("/events?path=/") as websocket:
        full = websocket.receive_json()
        triage = send_event(websocket, view_button(full, "triage"), "click", None)
        assert websocket.receive_json()["type"] == "event_complete"
        board = _find_payload_nodes(triage, "KanbanBoard")[0]
        selection = send_event(
            websocket,
            board,
            "cardClick",
            {"id": "ml_features", "title": "ML Features", "column": "at-risk"},
        )
        assert "ML Features opened from the triage queue" in json.dumps(selection)

    with client.websocket_connect("/events?path=/") as websocket:
        full = websocket.receive_json()
        pipelines = send_event(
            websocket, view_button(full, "pipelines"), "click", None
        )
        assert websocket.receive_json()["type"] == "event_complete"
        run_button = next(
            node
            for node in _find_payload_nodes(pipelines, "Button")
            if node["props"]["label"] == "Run simulated refresh"
        )
        complete_button = next(
            node
            for node in _find_payload_nodes(pipelines, "Button")
            if node["props"]["label"] == "Complete simulated run"
        )
        pending = send_event(websocket, run_button, "click", None)
        assert "Simulated action pending" in json.dumps(pending)
        assert websocket.receive_json()["type"] == "event_complete"
        success = send_event(websocket, complete_button, "click", None)
        assert "Simulated action acknowledged" in json.dumps(success)

    with client.websocket_connect("/events?path=/") as websocket:
        full = websocket.receive_json()
        assistant = send_event(
            websocket, view_button(full, "assistant"), "click", None
        )
        assert websocket.receive_json()["type"] == "event_complete"
        chat_input = _find_payload_nodes(assistant, "ChatInput")[0]
        complete_button = next(
            node
            for node in _find_payload_nodes(assistant, "Button")
            if node["props"]["label"] == "Complete simulated response"
        )
        pending = send_event(
            websocket, chat_input, "submit", "Which pipeline is at risk?"
        )
        assert "simulated response is pending" in json.dumps(pending)
        assert websocket.receive_json()["type"] == "event_complete"
        complete = send_event(websocket, complete_button, "click", None)
        assert "Simulated analysis: ML Features" in json.dumps(complete)


def test_flagship_websocket_switches_every_operational_view() -> None:
    namespace = runpy.run_path(
        str(EXAMPLES_ROOT / "data_pipeline_command_center" / "app.py")
    )
    assert namespace["VIEW_KEYS"] == (
        "overview",
        "pipelines",
        "reliability",
        "triage",
        "assistant",
    )

    def find_view_button(node: dict, view_key: str) -> dict | None:
        if node.get("type") == "Button" and node.get("props", {}).get(
            "viewKey"
        ) == view_key:
            return node
        for child in node.get("children", []):
            found = find_view_button(child, view_key)
            if found:
                return found
        return None

    app = namespace["app"]
    client = TestClient(create_asgi_app(app))
    expected_markers = {
        "overview": "Operational pulse",
        "pipelines": "Pipeline flow",
        "reliability": "Reliability signals",
        "triage": "Triage queue",
        "assistant": "Pipeline assistant",
    }

    for view_key in namespace["VIEW_KEYS"]:
        with client.websocket_connect("/events?path=/") as websocket:
            full = websocket.receive_json()
            buttons = {
                key: find_view_button(full["tree"], key)
                for key in namespace["VIEW_KEYS"]
            }
            assert all(buttons.values())

            if view_key != "overview":
                button = buttons[view_key]
                assert button is not None
                websocket.send_json(
                    {
                        "type": "event",
                        "event_id": button["props"]["click"],
                        "data": {"value": None},
                    }
                )
                response = websocket.receive_json()
            else:
                pipelines_button = buttons["pipelines"]
                overview_button = buttons["overview"]
                assert pipelines_button is not None and overview_button is not None
                websocket.send_json(
                    {
                        "type": "event",
                        "event_id": pipelines_button["props"]["click"],
                        "data": {"value": None},
                    }
                )
                assert websocket.receive_json()["type"] == "patch"
                assert websocket.receive_json()["type"] == "event_complete"
                websocket.send_json(
                    {
                        "type": "event",
                        "event_id": overview_button["props"]["click"],
                        "data": {"value": None},
                    }
                )
                response = websocket.receive_json()

        assert response["type"] == "patch", response
        assert expected_markers[view_key] in json.dumps(response)


def test_flagship_executive_brief_opens_without_a_runtime_error() -> None:
    app = _load_example_app("data_pipeline_command_center")
    client = TestClient(create_asgi_app(app))

    with client.websocket_connect("/events?path=/") as websocket:
        full = websocket.receive_json()
        brief_button = next(
            button
            for button in _find_payload_nodes(full["tree"], "Button")
            if "Executive brief" in json.dumps(button)
        )
        websocket.send_json(
            {
                "type": "event",
                "event_id": brief_button["props"]["click"],
                "data": {"value": None},
            }
        )
        patch = websocket.receive_json()
        completion = websocket.receive_json()

    assert patch["type"] == "patch", patch
    assert '"visible": true' in json.dumps(patch)
    assert completion == {
        "type": "event_complete",
        "event_id": brief_button["props"]["click"],
    }


@pytest.mark.parametrize("example_name", PUBLIC_RUNTIME_SMOKE_EXAMPLES)
def test_public_example_serves_shell_and_full_websocket_tree(example_name: str) -> None:
    app = _load_example_app(example_name)
    client = TestClient(create_asgi_app(app))

    response = client.get("/")

    assert response.status_code == 200
    assert "BrickflowUI" in response.text

    with client.websocket_connect("/events?path=/") as websocket:
        payload = websocket.receive_json()

    assert payload["type"] == "full"
    assert isinstance(payload["tree"], dict)
    assert payload["tree"]["type"]
    json.dumps(payload["tree"])
