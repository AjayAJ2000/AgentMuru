from pathlib import Path

import pytest
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
    assert "agentmuru>=0.3,<0.4" in (target / "requirements.txt").read_text()
    assert "muru run app:application" in (target / "README.md").read_text()


@pytest.mark.parametrize(
    ("provider", "requirement", "provider_class", "environment_variable"),
    [
        ("openai", "agentmuru[openai]>=0.3,<0.4", "OpenAIModel", "OPENAI_API_KEY"),
        (
            "anthropic",
            "agentmuru[anthropic]>=0.3,<0.4",
            "AnthropicModel",
            "ANTHROPIC_API_KEY",
        ),
        ("google", "agentmuru[google]>=0.3,<0.4", "GoogleGenAIModel", "GOOGLE_API_KEY"),
    ],
)
def test_init_renders_selected_official_provider(
    tmp_path: Path,
    provider: str,
    requirement: str,
    provider_class: str,
    environment_variable: str,
) -> None:
    target = tmp_path / provider

    result = runner.invoke(app, ["init", str(target), "--provider", provider])

    assert result.exit_code == 0
    assert (target / "requirements.txt").read_text(encoding="utf-8").strip() == requirement
    assert provider_class in (target / "app.py").read_text(encoding="utf-8")
    assert environment_variable in (target / "README.md").read_text(encoding="utf-8")


def test_init_rejects_unknown_provider_without_writing(tmp_path: Path) -> None:
    target = tmp_path / "unknown"

    result = runner.invoke(app, ["init", str(target), "--provider", "mystery"])

    assert result.exit_code != 0
    assert not target.exists()


def test_init_refuses_to_overwrite_nonempty_directory(tmp_path: Path) -> None:
    target = tmp_path / "existing"
    target.mkdir()
    (target / "important.txt").write_text("keep", encoding="utf-8")

    result = runner.invoke(app, ["init", str(target)])

    assert result.exit_code != 0
    assert (target / "important.txt").read_text(encoding="utf-8") == "keep"
