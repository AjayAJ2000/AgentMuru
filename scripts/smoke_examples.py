from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Final
from urllib.error import URLError
from urllib.request import Request, urlopen

from websockets.sync.client import connect


REPO_ROOT: Final = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.example_manifest import ExampleSpec, load_example_manifest  # noqa: E402


STARTUP_TIMEOUT_SECONDS: Final = 35
REQUEST_TIMEOUT_SECONDS: Final = 5


def configured_checks(repo_root: Path = REPO_ROOT) -> tuple[ExampleSpec, ...]:
    return load_example_manifest(repo_root)


def run_check(spec: ExampleSpec, port: int) -> tuple[bool, str]:
    """Run the bounded HTTP and WebSocket smoke check for one manifest example."""
    app_path = REPO_ROOT / "examples" / spec.name / "app.py"
    environment = os.environ.copy()
    environment["DATABRICKS_APP_PORT"] = str(port)
    environment["PYTHONPATH"] = _pythonpath_with_repo(environment.get("PYTHONPATH"))
    process = subprocess.Popen(
        [sys.executable, str(app_path)],
        cwd=app_path.parent,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        base_url = f"http://127.0.0.1:{port}"
        _wait_until_ready(base_url, spec)
        for route in spec.routes:
            _request_route(base_url, route, spec)
            _assert_full_tree(base_url, route, spec)
        return True, f"{spec.name}: passed"
    except Exception as exc:
        return False, f"{spec.name}: {exc}"
    finally:
        _stop_process(process)


def _pythonpath_with_repo(existing: str | None) -> str:
    entries = [str(REPO_ROOT)]
    if existing:
        entries.append(existing)
    return os.pathsep.join(entries)


def _wait_until_ready(base_url: str, spec: ExampleSpec) -> None:
    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    route = spec.routes[0]
    while time.monotonic() < deadline:
        try:
            _request_route(base_url, route, spec)
        except (OSError, URLError):
            time.sleep(0.25)
            continue
        return
    raise TimeoutError(f"server did not become ready within {STARTUP_TIMEOUT_SECONDS} seconds")


def _request_route(base_url: str, route: str, spec: ExampleSpec) -> None:
    request = Request(f"{base_url}{route}", headers=dict(spec.auth_headers))
    with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        if response.status != 200:
            raise RuntimeError(f"{route} returned HTTP {response.status}")


def _assert_full_tree(base_url: str, route: str, spec: ExampleSpec) -> None:
    websocket_url = f"ws{base_url.removeprefix('http')}/events?path={route}"
    with connect(
        websocket_url,
        additional_headers=dict(spec.auth_headers),
        open_timeout=REQUEST_TIMEOUT_SECONDS,
        close_timeout=REQUEST_TIMEOUT_SECONDS,
    ) as websocket:
        payload = json.loads(websocket.recv(timeout=REQUEST_TIMEOUT_SECONDS))
    validate_full_tree(payload, route)


def validate_full_tree(payload: object, route: str) -> None:
    if not isinstance(payload, dict) or payload.get("type") != "full":
        raise RuntimeError(f"{route} did not return a full message with a non-empty VDOM root")
    tree = payload.get("tree")
    if not isinstance(tree, dict) or not isinstance(tree.get("type"), str) or not tree["type"]:
        raise RuntimeError(f"{route} did not return a full message with a non-empty VDOM root")
    if "children" in tree and not isinstance(tree["children"], list):
        raise RuntimeError(f"{route} did not return a full message with a non-empty VDOM root")


def _stop_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=REQUEST_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=REQUEST_TIMEOUT_SECONDS)
    if process.stdout is not None:
        process.stdout.close()


def main() -> int:
    failures = [
        message
        for index, spec in enumerate(configured_checks())
        for passed, message in [run_check(spec, port=8765 + index)]
        if not passed
    ]
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print("All manifest examples passed smoke checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
