from __future__ import annotations

from pathlib import Path

import agentmuru
import yaml


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_public_navigation_follows_customer_tasks() -> None:
    navigation = yaml.safe_load(_read("mkdocs.yml"))["nav"]

    assert [next(iter(section)) for section in navigation] == [
        "Home",
        "Start",
        "Tutorials",
        "How-to guides",
        "Concepts",
        "Reference",
    ]
    assert [next(iter(page)) for page in navigation[1]["Start"]] == [
        "Choose a path",
        "Installation",
        "Five-minute local quickstart",
    ]

    public_labels = yaml.safe_dump(navigation)
    for internal_label in (
        "Qualification",
        "Integration status",
        "Architecture",
        "Current state",
        "Target state",
        "Transformation log",
        "Decisions",
    ):
        assert internal_label not in public_labels


def test_start_pages_separate_selection_installation_and_quickstart() -> None:
    installation_path = ROOT / "docs/getting-started/installation.md"
    quickstart_path = ROOT / "docs/getting-started/quickstart.md"
    assert installation_path.is_file()
    assert quickstart_path.is_file()

    choices = _read("docs/getting-started.md")
    installation = installation_path.read_text(encoding="utf-8")
    quickstart = quickstart_path.read_text(encoding="utf-8")

    assert "Choose your path" in choices
    assert "getting-started/installation.md" in choices
    assert "getting-started/quickstart.md" in choices
    assert "python -m pip install agentmuru==0.2.0" in installation
    assert installation.index("agentmuru==0.2.0") < installation.index("pip install -e")
    for expected in (
        "muru doctor",
        "muru init",
        "muru run app:application",
        "http://127.0.0.1:8000",
        "What you should see",
        "Next steps",
    ):
        assert expected in quickstart


def test_homepage_routes_readers_by_goal() -> None:
    homepage = _read("docs/index.md")

    assert "Choose your goal" in homepage
    assert "How the docs are organized" in homepage
    for destination in (
        "getting-started/quickstart.md",
        "guides/sqlite-persistence.md",
        "cookbook/governed-tools.md",
        "reference/public-api.md",
        "integration-status.md",
    ):
        assert destination in homepage


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
