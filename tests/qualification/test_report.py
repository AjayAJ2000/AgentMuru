from __future__ import annotations

from qualification.render_report import render_report


def test_report_distinguishes_contract_and_live_verification() -> None:
    markdown = render_report(
        {
            "environment": {"python": "3.11", "generated_at": "2026-08-09T00:00:00Z"},
            "commands": [],
            "scenarios": [{"name": "sqlite_restart", "status": "passed"}],
            "databricks_live": {
                "status": "not_executed",
                "reason": "credentials unavailable",
            },
            "failures": [],
        }
    )

    assert "SQLite restart | Passed" in markdown
    assert "Databricks live | Not executed" in markdown
    assert "credentials unavailable" in markdown
    assert "2026-08-09T00:00:00Z" in markdown


def test_report_renders_clean_wheel_scenario_dictionary() -> None:
    markdown = render_report(
        {
            "environment": {"generated_at": "2026-08-09T00:00:00Z"},
            "commands": [{"name": "pip_check", "exit_code": 0, "duration_seconds": 1.2}],
            "scenarios": {
                "runtime_status": "completed",
                "approval_status": "completed",
                "databricks_sdk": True,
            },
            "databricks_live": {"attempted": False, "reason": "opt-in"},
            "failures": [],
        }
    )

    assert "Runtime execution | Passed" in markdown
    assert "Approval resume | Passed" in markdown
    assert "Databricks optional imports | Passed" in markdown
    assert "pip_check | Passed" in markdown

