from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import agentmuru
import yaml


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _navigation() -> list[dict[str, Any]]:
    return yaml.safe_load(_read("mkdocs.yml"))["nav"]


def _nav_paths(items: list[Any]) -> list[str]:
    paths: list[str] = []
    for item in items:
        if isinstance(item, str):
            paths.append(item)
            continue
        for value in item.values():
            if isinstance(value, str):
                paths.append(value)
            else:
                paths.extend(_nav_paths(value))
    return paths


def test_public_navigation_matches_the_python_first_product() -> None:
    navigation = _navigation()

    assert [next(iter(section)) for section in navigation] == [
        "Home",
        "Get started",
        "Build",
        "Providers",
        "Operate",
        "Reference",
        "Labs",
        "Project",
    ]
    config = yaml.safe_load(_read("mkdocs.yml"))
    assert "superpowers/**" in config["exclude_docs"]

    paths = _nav_paths(navigation)
    assert len(paths) == len(set(paths))
    assert all((ROOT / "docs" / path).is_file() for path in paths)
    assert "migration-from-legacy-ui.md" not in paths
    assert "architecture/ai-native-transformation.md" not in paths


def test_homepage_has_one_current_install_path_and_real_workspace_visual() -> None:
    homepage = _read("docs/index.md")

    assert "Build agents you can see, steer, and trust." in homepage
    assert "python -m pip install agentmuru==0.3.0" in homepage
    assert 'href="getting-started/quickstart/"' in homepage
    assert 'href="getting-started/real-model/"' in homepage
    assert "assets/workspace-overview.png" in homepage
    assert "Native adaptive-agent preview" not in homepage


def test_raw_html_internal_links_use_published_urls() -> None:
    failures: list[str] = []
    for page in (ROOT / "docs").rglob("*.md"):
        text = page.read_text(encoding="utf-8")
        for href in re.findall(r'href=["\']([^"\']+)["\']', text):
            if href.split("#", 1)[0].endswith(".md"):
                failures.append(f"{page.relative_to(ROOT)} -> {href}")

    assert failures == []


def test_getting_started_path_is_runnable_and_task_complete() -> None:
    installation = _read("docs/getting-started/installation.md")
    quickstart = _read("docs/getting-started/quickstart.md")
    tour = _read("docs/getting-started/workspace-tour.md")
    real_model = _read("docs/getting-started/real-model.md")

    assert "python -m pip install agentmuru==0.3.0" in installation
    assert installation.index("agentmuru==0.3.0") < installation.index("pip install -e")
    for expected in (
        "muru doctor",
        "muru init",
        "muru run app:application",
        "http://127.0.0.1:8000",
        "What you should see",
        "Stop the server",
    ):
        assert expected in quickstart
    for workspace_area in ("Sessions", "Timeline", "Approvals", "Artifacts"):
        assert workspace_area in tour
    for provider in ("openai", "anthropic", "google"):
        assert f"--provider {provider}" in real_model


def test_official_provider_pages_match_shipped_adapters() -> None:
    expectations = {
        "openai": ("OpenAIModel", "OPENAI_API_KEY", "gpt-5.6-terra"),
        "anthropic": ("AnthropicModel", "ANTHROPIC_API_KEY", "claude-sonnet-5"),
        "google": ("GoogleGenAIModel", "GOOGLE_API_KEY", "gemini-3.5-flash"),
    }
    overview = _read("docs/providers/index.md")
    for provider, (class_name, environment_variable, model) in expectations.items():
        page = _read(f"docs/providers/{provider}.md")
        assert f"agentmuru[{provider}]" in page
        assert class_name in page
        assert environment_variable in page
        assert model in page
        assert f"({provider}.md)" in overview


def test_reference_pages_cover_the_stable_surface() -> None:
    public_api = _read("docs/reference/public-api.md")
    cli = _read("docs/reference/cli.md")
    events = _read("docs/reference/events.md")
    providers = _read("docs/reference/providers.md")
    configuration = _read("docs/reference/configuration.md")

    for name in agentmuru.__all__:
        assert f"`{name}`" in public_api
    for command in ("muru version", "muru doctor", "muru init", "muru dev", "muru run"):
        assert command in cli
    for event_type in (
        "agent.started",
        "model.request.started",
        "tool.call.requested",
        "run.completed",
    ):
        assert event_type in events
    for setting in ("max_output_tokens", "temperature", "top_p", "stop", "tool_choice"):
        assert setting in providers
    for variable in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"):
        assert variable in configuration


def test_operational_docs_state_real_boundaries() -> None:
    combined = "\n".join(
        _read(path)
        for path in (
            "docs/operations/server-and-workspace.md",
            "docs/operations/sqlite.md",
            "docs/operations/observability.md",
            "docs/operations/security.md",
            "docs/operations/deployment.md",
        )
    )
    for phrase in (
        "/health",
        "WebSocket",
        "one active AgentMuru runtime process",
        "WAL",
        "storage_busy",
        "process_interrupted",
        "trusted hosts",
        "authentication",
        "TLS",
        "backup",
    ):
        assert phrase.lower() in combined.lower()


def test_labs_are_explicitly_separate_from_the_python_mvp() -> None:
    labs = _read("docs/labs/index.md")
    native = _read("docs/labs/native-preview.md")
    local_models = _read("docs/labs/local-models.md")

    assert "not part of the PyPI 0.3.0 MVP" in labs
    assert "distributed separately through GitHub Releases" in native.replace("\n", " ")
    assert "public model catalog is intentionally empty" in native
    assert "No catalog model is reference-device-qualified" in local_models


def test_public_docs_have_no_legacy_identity_or_stale_current_version() -> None:
    config = yaml.safe_load(_read("mkdocs.yml"))
    public_paths = _nav_paths(config["nav"])
    failures: list[str] = []
    stale: list[str] = []
    dashes: list[str] = []
    for relative in public_paths:
        text = _read(f"docs/{relative}")
        lowered = text.lower()
        if "brickflowui" in lowered or "brickflow ui" in lowered:
            failures.append(relative)
        if relative != "CHANGELOG.md" and "agentmuru 0.2" in lowered:
            stale.append(relative)
        if "—" in text or "–" in text:
            dashes.append(relative)
    assert failures == []
    assert stale == []
    assert dashes == []


def test_removed_public_history_pages_are_absent() -> None:
    for relative in (
        "docs/migration-from-legacy-ui.md",
        "docs/migration-custom-stores-0.2.md",
        "docs/architecture/current-state.md",
        "docs/architecture/ai-native-transformation.md",
    ):
        assert not (ROOT / relative).exists()
