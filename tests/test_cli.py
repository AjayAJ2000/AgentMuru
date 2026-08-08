from pathlib import Path

from typer.testing import CliRunner

from agentmuru.cli.main import app


runner = CliRunner()


def test_version_reports_agentmuru_identity() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert result.stdout.strip().startswith("AgentMuru ")


def test_doctor_validates_local_installation() -> None:
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "Python" in result.stdout
    assert "Workspace assets" in result.stdout
    assert "ready" in result.stdout.lower()


def test_init_creates_small_runtime_first_project(tmp_path: Path) -> None:
    target = tmp_path / "customer-agent"

    result = runner.invoke(app, ["init", str(target), "--name", "Customer Muru"])

    assert result.exit_code == 0
    assert "from agentmuru import Agent, Application, FakeModel, tool" in (target / "app.py").read_text()
    assert "agentmuru" in (target / "requirements.txt").read_text()
    assert "muru run app:application" in (target / "README.md").read_text()


def test_init_refuses_to_overwrite_nonempty_directory(tmp_path: Path) -> None:
    target = tmp_path / "existing"
    target.mkdir()
    (target / "important.txt").write_text("keep", encoding="utf-8")

    result = runner.invoke(app, ["init", str(target)])

    assert result.exit_code != 0
    assert (target / "important.txt").read_text(encoding="utf-8") == "keep"
