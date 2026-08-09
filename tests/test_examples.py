import importlib
import runpy
from pathlib import Path

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
