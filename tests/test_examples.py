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
