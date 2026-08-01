from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_ROOT = REPO_ROOT / "examples"

FLAGSHIP_EXAMPLES = {
    "acme_analytics_command_center",
    "component_studio",
    "clinical_trial_command_center",
    "data_pipeline_command_center",
    "geometric_signal_lab",
    "secure_internal_tools",
    "workspace_studio",
}


def test_every_example_app_compiles() -> None:
    example_apps = sorted(EXAMPLES_ROOT.glob("*/app.py"))

    assert example_apps, "Expected at least one example app."

    for app_path in example_apps:
        source = app_path.read_text(encoding="utf-8-sig")
        compile(source, str(app_path), "exec")


def test_flagship_examples_exist() -> None:
    available_examples = {path.name for path in EXAMPLES_ROOT.iterdir() if path.is_dir()}

    assert FLAGSHIP_EXAMPLES.issubset(available_examples)
