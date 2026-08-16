from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_windows_native_release_creates_output_directory_before_build() -> None:
    workflow = (ROOT / ".github/workflows/native-release.yml").read_text(encoding="utf-8")

    create = "New-Item -ItemType Directory -Force dist/native"
    build = "go build -trimpath"
    assert create in workflow
    assert workflow.index(create) < workflow.index(build)
