from __future__ import annotations

import asyncio
from pathlib import Path

from examples import (
    artifact_agent,
    databricks_agent,
    durable_agent,
    governed_tool_agent,
    handoff_agent,
    workflow_agent,
)


def test_governed_tool_scenario_exercises_every_policy_outcome() -> None:
    result = asyncio.run(governed_tool_agent.main())

    assert result == {
        "allow": "completed",
        "deny": "permission_denied",
        "approve": "completed",
        "reject": "completed",
        "expiry": "approval_expired",
        "mutations": 1,
    }


def test_artifact_scenario_creates_reopenable_supported_artifacts() -> None:
    result = asyncio.run(artifact_agent.main())

    assert result["run_status"] == "completed"
    assert result["artifact_kinds"] == ["code", "file", "json", "markdown", "table"]
    assert result["artifact_count"] == 5


def test_durable_scenario_restores_history_from_same_file(tmp_path: Path) -> None:
    result = asyncio.run(durable_agent.main(tmp_path / "agentmuru.db"))

    assert result == {
        "sessions": 1,
        "runs": 1,
        "messages": 2,
        "events": 12,
        "status": "completed",
    }


def test_handoff_scenario_runs_both_agents() -> None:
    result = asyncio.run(handoff_agent.main())

    assert result == {
        "source_agent": "researcher",
        "source_status": "completed",
        "target_agent": "writer",
        "target_status": "completed",
        "handoffs": 1,
    }


def test_databricks_scenario_is_safe_without_credentials_or_network() -> None:
    result = databricks_agent.main()

    assert result["network_attempted"] is False
    assert result["host_configured"] in {True, False}
    assert result["sdk_installed"] in {True, False}


def test_workflow_scenario_returns_checkpoint_evidence() -> None:
    result = asyncio.run(workflow_agent.main())

    assert result == {
        "status": "completed",
        "summary": "AgentMuru verified 2 facts.",
        "checkpoints": ["research", "summarize"],
    }

