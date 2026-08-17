import importlib
import runpy
from pathlib import Path

import pytest

from agentmuru import Application


ROOT = Path(__file__).resolve().parents[1]


def test_agent_examples_export_applications_without_external_credentials() -> None:
    for relative in ("hello_agent.py", "governed_data_agent.py"):
        namespace = runpy.run_path(str(ROOT / "examples" / relative), run_name="agentmuru_example")
        assert isinstance(namespace["application"], Application)


def test_workflow_example_has_deterministic_main() -> None:
    namespace = runpy.run_path(
        str(ROOT / "examples" / "workflow_agent.py"), run_name="agentmuru_example"
    )
    assert callable(namespace["main"])


def test_complete_scenario_gallery_imports_without_credentials() -> None:
    for module_name in (
        "examples.governed_tool_agent",
        "examples.artifact_agent",
        "examples.durable_agent",
        "examples.handoff_agent",
        "examples.databricks_agent",
    ):
        assert importlib.import_module(module_name) is not None


def test_provider_examples_export_applications_without_network_calls() -> None:
    for module_name in (
        "examples.providers.openai_agent",
        "examples.providers.anthropic_agent",
        "examples.providers.google_agent",
    ):
        module = importlib.import_module(module_name)
        assert isinstance(module.application, Application)


@pytest.mark.parametrize(
    ("example", "page"),
    [
        ("examples/governed_tool_agent.py", "docs/cookbook/governed-tools.md"),
        ("examples/artifact_agent.py", "docs/cookbook/artifacts.md"),
        ("examples/durable_agent.py", "docs/cookbook/durable-sessions.md"),
        ("examples/handoff_agent.py", "docs/cookbook/workflows-and-handoffs.md"),
        ("examples/databricks_agent.py", "docs/operations/databricks.md"),
    ],
)
def test_scenario_has_cookbook_page(example: str, page: str) -> None:
    text = (ROOT / page).read_text(encoding="utf-8")
    module_name = example.replace("/", ".").removesuffix(".py")
    assert module_name in text
    assert f"python {example}" in text
