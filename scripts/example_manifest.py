from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType


_WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
    "COM\u00b9",
    "COM\u00b2",
    "COM\u00b3",
    "LPT\u00b9",
    "LPT\u00b2",
    "LPT\u00b3",
}
_WINDOWS_INVALID_FILENAME_CHARS = frozenset('<>:"/\\|?*')


@dataclass(frozen=True)
class ExampleSpec:
    name: str
    title: str
    kind: str
    routes: tuple[str, ...]
    auth_headers: Mapping[str, str]


def load_example_manifest(repo_root: Path) -> tuple[ExampleSpec, ...]:
    manifest_path = repo_root / "examples" / "manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("Unsupported examples manifest schema_version")

    rows = payload.get("examples")
    if not isinstance(rows, list):
        raise ValueError("examples must be a list")

    specs = tuple(_parse_spec(row) for row in rows)
    if len({spec.name for spec in specs}) != len(specs):
        raise ValueError("Example names must be unique")
    return specs


def _parse_spec(row: object) -> ExampleSpec:
    if not isinstance(row, dict):
        raise ValueError("Each example must be an object")

    name = row.get("name")
    if not isinstance(name, str) or not _is_relative_directory_name(name):
        raise ValueError("Example name must be a relative directory name")

    title = row.get("title")
    if not isinstance(title, str):
        raise ValueError("Example title must be a string")

    kind = row.get("kind")
    if not isinstance(kind, str):
        raise ValueError("Example kind must be a string")

    routes = row.get("routes")
    if not isinstance(routes, list) or not routes or not all(isinstance(route, str) for route in routes):
        raise ValueError("Example routes must be a non-empty list of strings")

    auth_headers = row.get("auth_headers")
    if not isinstance(auth_headers, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in auth_headers.items()
    ):
        raise ValueError("Example auth_headers must map strings to strings")

    return ExampleSpec(
        name=name,
        title=title,
        kind=kind,
        routes=tuple(routes),
        auth_headers=MappingProxyType(dict(auth_headers)),
    )


def _is_relative_directory_name(name: str) -> bool:
    return (
        name not in {"", ".", ".."}
        and Path(name).name == name
        and "/" not in name
        and "\\" not in name
        and not any(character in _WINDOWS_INVALID_FILENAME_CHARS for character in name)
        and all(ord(character) >= 32 for character in name)
        and not name.endswith((" ", "."))
        and name.split(".", 1)[0].upper() not in _WINDOWS_RESERVED_NAMES
    )
