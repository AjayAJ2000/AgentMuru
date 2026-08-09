from __future__ import annotations

from pathlib import Path

from qualification.run_clean_install import build_smoke_command, clean_environment


def test_harness_runs_smoke_from_outside_repository(tmp_path: Path) -> None:
    smoke_script = tmp_path / "installed_smoke.py"
    command = build_smoke_command(tmp_path / "venv", smoke_script)

    assert command.cwd == tmp_path
    assert command.argv[-1] == str(smoke_script)
    assert "PYTHONPATH" not in command.environment
    assert command.environment["PYTHONNOUSERSITE"] == "1"


def test_clean_environment_removes_source_path_injection() -> None:
    environment = clean_environment({"PYTHONPATH": "source", "KEEP": "value"})

    assert "PYTHONPATH" not in environment
    assert environment["KEEP"] == "value"
    assert environment["PYTHONNOUSERSITE"] == "1"

