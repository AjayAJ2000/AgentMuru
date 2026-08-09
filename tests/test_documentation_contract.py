from __future__ import annotations

from pathlib import Path

import agentmuru


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_quickstart_begins_with_verified_distribution_commands() -> None:
    guide = _read("docs/getting-started.md")

    assert "python -m pip install agentmuru==0.2.0" in guide
    assert "muru doctor" in guide
    assert "muru init" in guide
    assert guide.index("agentmuru==0.2.0") < guide.index("pip install -e")


def test_public_api_reference_matches_stable_exports() -> None:
    reference = _read("docs/reference/public-api.md")

    for name in agentmuru.__all__:
        assert f"`{name}`" in reference
    assert "from agentmuru import SQLitePersistence" in reference


def test_persistence_guide_contains_verified_contract_and_limits() -> None:
    guide = _read("docs/guides/sqlite-persistence.md")

    assert 'SQLitePersistence("agentmuru.db")' in guide
    assert "one active AgentMuru runtime process" in guide
    assert "BEGIN IMMEDIATE" in guide
    assert "storage_busy" in guide
    assert "process_interrupted" in guide
    assert "WAL" in guide
    assert "5,000 ms" in guide
    assert "not encrypted" in guide


def test_custom_store_migration_lists_every_explicit_mutation() -> None:
    migration = _read("docs/migration-custom-stores-0.2.md")
    for method in (
        "append_message",
        "create_run",
        "update_run",
        "get_run",
        "get_idempotent_run",
        "bind_idempotency_key",
        "recover_interrupted_runs",
        "append_event",
    ):
        assert f"`{method}`" in migration


def test_server_and_deployment_guides_cover_operational_boundaries() -> None:
    server = _read("docs/guides/server-and-workspace.md")
    deployment = _read("docs/guides/deployment.md")
    combined = server + deployment + _read("docs/guides/security.md")

    for phrase in (
        "/health",
        "WebSocket",
        "trusted hosts",
        "TLS",
        "backup",
        "payload",
        "authentication",
        "database path",
    ):
        assert phrase.lower() in combined.lower()

