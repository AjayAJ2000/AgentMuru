from pathlib import Path
import re


def test_frontend_distribution_contains_only_one_current_entry_bundle():
    repo_root = Path(__file__).resolve().parents[1]
    dist = repo_root / "brickflowui" / "frontend" / "dist"
    index_html = (dist / "index.html").read_text(encoding="utf-8")
    assets = dist / "assets"

    entry_bundles = list(assets.glob("index-*.js"))
    assert len(entry_bundles) == 1, (
        "frontend/dist contains stale entry bundles; run a clean frontend build"
    )

    references = re.findall(r'(?:src|href)="/assets/([^"]+)"', index_html)
    assert references
    assert all((assets / reference).is_file() for reference in references)
