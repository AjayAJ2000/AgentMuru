import json
from pathlib import Path

import agentmuru
import yaml

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised by the Python 3.10 CI job
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]


def test_distribution_package_and_cli_are_agentmuru_only() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert config["project"]["name"] == "agentmuru"
    assert config["project"]["scripts"] == {"muru": "agentmuru.cli.main:app"}
    assert config["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == ["agentmuru"]
    assert (ROOT / "agentmuru" / "frontend" / "dist" / "index.html").exists()
    assert not (ROOT / "brickflowui").exists()
    assert config["project"]["version"] == "0.2.0"
    assert agentmuru.__version__ == "0.2.0"
    assert json.loads((ROOT / "frontend" / "package.json").read_text(encoding="utf-8"))[
        "version"
    ] == "0.2.0"
    assert "/qualification" in config["tool"]["hatch"]["build"]["targets"]["sdist"]["include"]


def test_optional_all_extra_references_agentmuru() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert config["project"]["optional-dependencies"]["all"] == [
        "agentmuru[databricks,dev,docs]"
    ]


def test_ci_and_docs_workflows_require_clean_wheel_qualification() -> None:
    for relative in (".github/workflows/ci.yml", ".github/workflows/docs.yml"):
        workflow = yaml.safe_load((ROOT / relative).read_text(encoding="utf-8"))
        assert "qualification" in workflow["jobs"]
        rendered = (ROOT / relative).read_text(encoding="utf-8")
        assert "qualification/run_clean_install.py" in rendered
        assert "agentmuru-0.2.0-py3-none-any.whl" in rendered


def test_publish_workflow_builds_once_and_requires_qualification() -> None:
    workflow_path = ROOT / ".github" / "workflows" / "publish.yml"
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

    assert "qualification" in workflow["jobs"]
    assert workflow["jobs"]["publish"]["needs"] == ["qualification"]
    publish_steps = str(workflow["jobs"]["publish"]["steps"])
    assert "download-artifact" in publish_steps
    assert "python -m build" not in publish_steps
    assert workflow["jobs"]["publish"]["permissions"] == {"id-token": "write"}
