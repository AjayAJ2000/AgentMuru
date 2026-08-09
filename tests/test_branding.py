from pathlib import Path

import yaml

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_URL = "https://github.com/AjayAJ2000/AgentMuru"
DOCUMENTATION_URL = "https://ajayaj2000.github.io/AgentMuru/"
ALLOWED_HISTORY = {
    ROOT / "docs" / "migration-from-legacy-ui.md",
    ROOT / "docs" / "architecture" / "current-state.md",
    ROOT / "docs" / "architecture" / "ai-native-transformation.md",
    ROOT / "docs" / "superpowers" / "specs" / "2026-08-08-agentmuru-ai-native-rearchitecture-design.md",
    ROOT / "docs" / "superpowers" / "plans" / "2026-08-08-agentmuru-ai-native-rearchitecture.md",
    ROOT
    / "docs"
    / "superpowers"
    / "specs"
    / "2026-08-09-agentmuru-qualification-persistence-and-launch-design.md",
    ROOT
    / "docs"
    / "superpowers"
    / "plans"
    / "2026-08-09-agentmuru-persistence-and-qualification.md",
    ROOT
    / "docs"
    / "superpowers"
    / "plans"
    / "2026-08-09-agentmuru-documentation-and-release.md",
    ROOT
    / "docs"
    / "superpowers"
    / "plans"
    / "2026-08-09-agentmuru-landing-and-launch.md",
}


def test_public_repository_copy_uses_agentmuru_identity() -> None:
    candidates = [ROOT / "README.md", ROOT / "pyproject.toml", ROOT / "mkdocs.yml"]
    candidates += list((ROOT / "docs").rglob("*.md"))
    failures = []
    for path in candidates:
        if path in ALLOWED_HISTORY:
            continue
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        if "brickflowui" in text or "brickflow ui" in text:
            failures.append(str(path.relative_to(ROOT)))
    assert failures == []


def test_frontend_source_has_no_legacy_protocol_identity() -> None:
    failures = []
    for path in (ROOT / "frontend" / "src").rglob("*"):
        if path.suffix not in {".ts", ".tsx", ".css"}:
            continue
        if "brickflow" in path.read_text(encoding="utf-8", errors="replace").lower():
            failures.append(str(path.relative_to(ROOT)))
    assert failures == []


def test_public_release_urls_use_exact_agentmuru_identity() -> None:
    package = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert package["project"]["urls"] == {
        "Homepage": REPOSITORY_URL,
        "Documentation": DOCUMENTATION_URL,
        "Repository": REPOSITORY_URL,
        "Issues": f"{REPOSITORY_URL}/issues",
    }

    docs = yaml.safe_load((ROOT / "mkdocs.yml").read_text(encoding="utf-8"))
    assert docs["site_url"] == DOCUMENTATION_URL
    assert docs["repo_url"] == REPOSITORY_URL
    assert docs["repo_name"] == "AjayAJ2000/AgentMuru"

    issue_config = yaml.safe_load(
        (ROOT / ".github" / "ISSUE_TEMPLATE" / "config.yml").read_text(encoding="utf-8")
    )
    assert issue_config["contact_links"][0]["url"] == DOCUMENTATION_URL
    assert issue_config["contact_links"][1]["url"] == f"{REPOSITORY_URL}/blob/main/SECURITY.md"


def test_public_install_and_documentation_are_featured() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    support = (ROOT / "SUPPORT.md").read_text(encoding="utf-8")

    assert "python -m pip install agentmuru" in readme
    assert "https://pypi.org/project/agentmuru/" in readme
    assert f"[{DOCUMENTATION_URL}]({DOCUMENTATION_URL})" in readme
    assert f"[{DOCUMENTATION_URL}]({DOCUMENTATION_URL})" in support


def test_docs_use_agentmuru_product_family_identity() -> None:
    config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    css = (ROOT / "docs" / "stylesheets" / "agentmuru.css").read_text(encoding="utf-8")
    logo = (ROOT / "docs" / "assets" / "agentmuru-mark.svg").read_text(encoding="utf-8")
    index = (ROOT / "docs" / "index.md").read_text(encoding="utf-8")

    assert "docs/assets/agentmuru-mark.svg" in config
    assert "stylesheets/agentmuru.css" in config
    assert all(color in css for color in ("#0A7C7F", "#0D5F8A", "#C48A1F", "#0D0F14", "#F4F7FB"))
    assert all(font in config for font in ("Inter", "JetBrains Mono"))
    assert "AgentMuru Hybrid Vel Eye mark" in logo
    assert "Build agents you can see, steer, and trust." in index
