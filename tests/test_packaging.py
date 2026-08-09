from pathlib import Path

import agentmuru

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
    assert "/qualification" in config["tool"]["hatch"]["build"]["targets"]["sdist"]["include"]


def test_optional_all_extra_references_agentmuru() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert config["project"]["optional-dependencies"]["all"] == [
        "agentmuru[databricks,dev,docs]"
    ]
