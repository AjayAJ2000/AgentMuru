from __future__ import annotations

import argparse
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


def _state(value: object) -> str:
    normalized = str(value).lower()
    if normalized in {"passed", "completed", "true", "0"}:
        return "Passed"
    if normalized in {"not_executed", "not executed", "false", "none"}:
        return "Not executed"
    return str(value).replace("_", " ").capitalize()


def _label(name: str) -> str:
    labels = {
        "sqlite_restart": "SQLite restart",
        "runtime_status": "Runtime execution",
        "approval_status": "Approval resume",
        "handoff_status": "Agent handoff",
        "workflow_status": "Workflow execution",
        "databricks_sdk": "Databricks SDK import",
        "databricks_sql": "Databricks SQL import",
    }
    return labels.get(name, name.replace("_", " ").capitalize())


def render_report(report: Mapping[str, Any]) -> str:
    environment = report.get("environment") or {}
    evidence_time = str(environment.get("generated_at", "Not recorded"))
    rows: list[tuple[str, str, str, str]] = []
    scenarios = report.get("scenarios") or {}
    if isinstance(scenarios, Mapping):
        for key in (
            "runtime_status",
            "approval_status",
            "handoff_status",
            "workflow_status",
        ):
            if key in scenarios:
                rows.append((_label(key), _state(scenarios[key]), "installed_smoke", ""))
        if "restored_messages" in scenarios:
            passed = int(scenarios.get("restored_messages", 0)) > 0
            rows.append(("SQLite restart", "Passed" if passed else "Failed", "installed_smoke", "One Runtime process per file"))
        if "databricks_sdk" in scenarios or "databricks_sql" in scenarios:
            imports = [
                bool(scenarios[key])
                for key in ("databricks_sdk", "databricks_sql")
                if key in scenarios
            ]
            passed = all(imports)
            rows.append(("Databricks optional imports", "Passed" if passed else "Failed", "installed_smoke", "No live workspace call"))
        provider_sdks = scenarios.get("provider_sdks")
        if isinstance(provider_sdks, Mapping):
            passed = all(bool(value) for value in provider_sdks.values())
            rows.append(("Official provider extras", "Passed" if passed else "Failed", "installed_smoke", "No credential-backed model call"))
    elif isinstance(scenarios, Sequence) and not isinstance(scenarios, (str, bytes)):
        for scenario in scenarios:
            if isinstance(scenario, Mapping):
                rows.append((
                    _label(str(scenario.get("name", "scenario"))),
                    _state(scenario.get("status", "unknown")),
                    str(scenario.get("command", "qualification harness")),
                    str(scenario.get("limitation", "")),
                ))

    live = report.get("databricks_live") or {}
    attempted = bool(live.get("attempted", False))
    live_status = live.get("status", "passed" if attempted else "not_executed")
    rows.append(("Databricks live", _state(live_status), "credential-backed environment", str(live.get("reason", ""))))

    command_rows = []
    for command in report.get("commands") or []:
        if not isinstance(command, Mapping):
            continue
        command_rows.append((
            str(command.get("name", "command")),
            "Passed" if command.get("exit_code") == 0 else "Failed",
            str(command.get("duration_seconds", "")),
        ))

    lines = [
        "# AgentMuru qualification evidence",
        "",
        f"Evidence time: `{evidence_time}`",
        "",
        "This page is generated from the clean-wheel qualification report. Contract tests and",
        "credential-backed live verification are intentionally separate.",
        "",
        "## Capability matrix",
        "",
        "| Capability | Result | Evidence | Limitation |",
        "| --- | --- | --- | --- |",
    ]
    lines.extend(f"| {capability} | {result} | {evidence} | {limitation} |" for capability, result, evidence, limitation in rows)
    lines.extend([
        "",
        "## Isolated commands",
        "",
        "| Command | Result | Duration (seconds) |",
        "| --- | --- | ---: |",
    ])
    lines.extend(f"| {name} | {result} | {duration} |" for name, result, duration in command_rows)
    failures = list(report.get("failures") or [])
    lines.extend([
        "",
        "## Result",
        "",
        "All required checks passed." if not failures else f"Failures: {', '.join(map(str, failures))}",
        "",
        "SQLite evidence covers one active Runtime process per file and modest concurrency.",
        "It does not claim multi-tenant write scaling or built-in encryption.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_report(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
