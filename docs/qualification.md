# AgentMuru qualification evidence

Evidence time: `2026-08-09T08:54:18.015188Z`

This page is generated from the clean-wheel qualification report. Contract tests and
credential-backed live verification are intentionally separate.

## Capability matrix

| Capability | Result | Evidence | Limitation |
| --- | --- | --- | --- |
| Runtime execution | Passed | installed_smoke |  |
| Approval resume | Passed | installed_smoke |  |
| Agent handoff | Passed | installed_smoke |  |
| Workflow execution | Passed | installed_smoke |  |
| SQLite restart | Passed | installed_smoke | One Runtime process per file |
| Databricks optional imports | Passed | installed_smoke | No live workspace call |
| Databricks live | Not executed | credential-backed environment | Live network qualification requires an explicit opt-in environment. |

## Isolated commands

| Command | Result | Duration (seconds) |
| --- | --- | ---: |
| create_venv | Passed | 7.658 |
| install_wheel_with_databricks_extra | Passed | 76.926 |
| pip_check | Passed | 1.231 |
| cli_version | Passed | 0.702 |
| cli_doctor | Passed | 0.63 |
| cli_init | Passed | 0.638 |
| scaffold_import | Passed | 0.249 |
| installed_smoke | Passed | 15.734 |
| installed_server_health | Passed | 1.211 |

## Result

All required checks passed.

SQLite evidence covers one active Runtime process per file and modest concurrency.
It does not claim multi-tenant write scaling or built-in encryption.
