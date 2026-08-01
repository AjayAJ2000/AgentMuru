import re
from pathlib import Path

import brickflowui as db


def test_runtime_version_matches_project_metadata():
    project = (Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"$', project, re.MULTILINE)

    assert match is not None
    assert db.__version__ == match.group(1)
