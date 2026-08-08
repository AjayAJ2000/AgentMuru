from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_HISTORY = {
    ROOT / "docs" / "migration-from-legacy-ui.md",
    ROOT / "docs" / "architecture" / "current-state.md",
    ROOT / "docs" / "architecture" / "ai-native-transformation.md",
    ROOT / "docs" / "superpowers" / "specs" / "2026-08-08-agentmuru-ai-native-rearchitecture-design.md",
    ROOT / "docs" / "superpowers" / "plans" / "2026-08-08-agentmuru-ai-native-rearchitecture.md",
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
