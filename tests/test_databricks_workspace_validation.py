import subprocess
import sys
from pathlib import Path

from scripts.validate_databricks_workspace import redact_origin, validate_results


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "validate_databricks_workspace.py"


def test_redact_origin_drops_credentials_path_and_query():
    assert (
        redact_origin("https://token@example.cloud/path?q=secret")
        == "https://example.cloud"
    )


def test_validate_results_rejects_same_subject_and_missing_permission_difference():
    results = [
        {"profile": "a", "subject": "same", "catalog": True, "warehouse": True, "job": True},
        {"profile": "b", "subject": "same", "catalog": True, "warehouse": True, "job": True},
    ]

    errors = validate_results(results)

    assert any("different subjects" in item for item in errors)
    assert any("permission difference" in item for item in errors)


def test_validate_results_requires_every_resource_for_profile_a():
    results = [
        {"profile": "a", "subject": "owner", "catalog": True, "warehouse": False, "job": True},
        {"profile": "b", "subject": "viewer", "catalog": True, "warehouse": False, "job": False},
    ]

    assert any("profile a" in item.lower() and "warehouse" in item for item in validate_results(results))


def test_cli_without_configuration_fails_safely():
    completed = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )
    output = f"{completed.stdout}\n{completed.stderr}".lower()

    assert completed.returncode != 0
    assert "required" in output or "configuration" in output
    assert "traceback" not in output
    assert "passed" not in output
