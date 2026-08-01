import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from typer.testing import CliRunner

from brickflowui.cli.main import app


runner = CliRunner()


def test_cli_help_only_shows_supported_commands():
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "new" in result.output
    assert "dev" in result.output
    assert "info" not in result.output
    assert "--template" not in result.output


def test_module_cli_help_has_no_runpy_warning():
    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-m", "brickflowui.cli.main", "--help"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "RuntimeWarning" not in result.stderr


def test_new_command_scaffolds_default_app(monkeypatch):
    repo_root = Path(__file__).resolve().parents[1]
    app_name = f"sample_app_{uuid.uuid4().hex[:8]}"
    scratch_dir = repo_root / f"_tmp_cli_{uuid.uuid4().hex[:8]}"

    try:
        scratch_dir.mkdir()
        monkeypatch.setattr(Path, "cwd", lambda: scratch_dir)
        result = runner.invoke(app, ["new", app_name], catch_exceptions=False)

        assert result.exit_code == 0
        assert "copy .env.example .env" in result.output or "cp .env.example .env" in result.output
        assert (scratch_dir / app_name / "app.py").exists()
        assert (scratch_dir / app_name / "app.yaml").exists()
        assert (scratch_dir / app_name / "requirements.txt").exists()
        assert (scratch_dir / app_name / ".env.example").exists()
    finally:
        shutil.rmtree(scratch_dir, ignore_errors=True)


def test_new_command_renders_success_message_without_markup(monkeypatch):
    repo_root = Path(__file__).resolve().parents[1]
    app_name = f"sample_app_{uuid.uuid4().hex[:8]}"
    scratch_dir = repo_root / f"_tmp_cli_{uuid.uuid4().hex[:8]}"

    try:
        scratch_dir.mkdir()
        monkeypatch.setattr(Path, "cwd", lambda: scratch_dir)

        result = runner.invoke(app, ["new", app_name], catch_exceptions=False)

        assert result.exit_code == 0
        assert "Created BrickflowUI app:" in result.output
        assert "[bold" not in result.output
        assert "[/bold" not in result.output
    finally:
        shutil.rmtree(scratch_dir, ignore_errors=True)


def test_dev_command_renders_banner_without_markup(monkeypatch):
    repo_root = Path(__file__).resolve().parents[1]
    scratch_dir = repo_root / f"_tmp_cli_{uuid.uuid4().hex[:8]}"

    try:
        scratch_dir.mkdir()
        (scratch_dir / "app.py").write_text("", encoding="utf-8")
        monkeypatch.setattr(Path, "cwd", lambda: scratch_dir)
        monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: None)

        result = runner.invoke(app, ["dev", "--no-reload"], catch_exceptions=False)

        assert result.exit_code == 0
        assert "BrickflowUI Dev Server" in result.output
        assert "[bold" not in result.output
        assert "[/bold" not in result.output
    finally:
        shutil.rmtree(scratch_dir, ignore_errors=True)


def test_new_command_reports_permission_errors_cleanly(monkeypatch):
    repo_root = Path(__file__).resolve().parents[1]
    app_name = f"sample_app_{uuid.uuid4().hex[:8]}"
    scratch_dir = repo_root / f"_tmp_cli_{uuid.uuid4().hex[:8]}"
    original_write_text = Path.write_text

    def blocked_write(self, *args, **kwargs):
        if self.name == "app.py":
            raise PermissionError("access denied")
        return original_write_text(self, *args, **kwargs)

    try:
        scratch_dir.mkdir()
        monkeypatch.setattr(Path, "cwd", lambda: scratch_dir)
        monkeypatch.setattr(Path, "write_text", blocked_write)

        result = runner.invoke(app, ["new", app_name], catch_exceptions=False)

        assert result.exit_code == 1
        assert "permission error" in result.output.lower()
        assert not (scratch_dir / app_name / "app.py").exists()
    finally:
        shutil.rmtree(scratch_dir, ignore_errors=True)


@pytest.mark.parametrize("name", ["../escape", "child/name", r"child\name", ".", "CON"])
def test_new_command_rejects_unsafe_project_names(monkeypatch, name):
    repo_root = Path(__file__).resolve().parents[1]
    suffix = uuid.uuid4().hex[:8]
    scratch_dir = repo_root / f"_tmp_cli_{suffix}"
    escaped_dir = repo_root / "escape"

    try:
        scratch_dir.mkdir()
        monkeypatch.setattr(Path, "cwd", lambda: scratch_dir)

        result = runner.invoke(app, ["new", name], catch_exceptions=False)

        assert result.exit_code == 2
        assert "single safe directory name" in result.output
        assert list(scratch_dir.iterdir()) == []
    finally:
        shutil.rmtree(scratch_dir, ignore_errors=True)
        shutil.rmtree(escaped_dir, ignore_errors=True)
