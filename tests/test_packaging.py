from pathlib import Path
import re
import subprocess

import yaml

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 CI uses the backport.
    import tomli as tomllib


REPO_ROOT = Path(__file__).resolve().parents[1]
NODE24_ACTION_MINIMUM_MAJORS = {
    "actions/checkout": 5,
    "actions/configure-pages": 6,
    "actions/deploy-pages": 5,
    "actions/setup-node": 5,
    "actions/setup-python": 6,
    "actions/upload-pages-artifact": 5,
    "github/codeql-action": 4,
}


def test_ruff_lint_policy_does_not_inherit_tool_defaults():
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["tool"]["ruff"]["lint"]["select"] == ["E4", "E7", "E9", "F"]


def test_public_tree_excludes_internal_agent_artifacts():
    tracked = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    forbidden_prefixes = (
        ".agents/",
        ".codex/",
        ".superpowers/",
        "docs/superpowers/",
        "docs/verification/",
    )

    assert not [path for path in tracked if path.startswith(forbidden_prefixes)]

    ignored = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    for prefix in forbidden_prefixes:
        assert prefix in ignored


def test_public_tree_excludes_developer_absolute_paths():
    tracked = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    ).stdout.split(b"\0")
    windows_sep = b"\\"
    forbidden = (
        b"C:" + windows_sep + b"Users" + windows_sep,
        b"D:" + windows_sep + b"Projects" + windows_sep,
        b"/home/" + b"runner/work/",
    )
    matches: list[str] = []

    for relative_path in filter(None, tracked):
        path = REPO_ROOT / relative_path.decode("utf-8", errors="surrogateescape")
        if path.is_file() and any(marker in path.read_bytes() for marker in forbidden):
            matches.append(path.relative_to(REPO_ROOT).as_posix())

    assert not matches


def _load_workflow(name: str) -> dict:
    workflow_path = REPO_ROOT / ".github" / "workflows" / name
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    assert isinstance(workflow, dict)
    assert isinstance(workflow.get("jobs"), dict)
    return workflow


def _uses_references(value: object):
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "uses" and isinstance(child, str):
                yield child
            yield from _uses_references(child)
    elif isinstance(value, list):
        for child in value:
            yield from _uses_references(child)


def test_workflows_do_not_use_pre_node24_action_majors():
    violations: list[str] = []
    workflow_paths = sorted(
        {
            *REPO_ROOT.glob(".github/workflows/*.yml"),
            *REPO_ROOT.glob(".github/workflows/*.yaml"),
        }
    )
    assert workflow_paths, "No GitHub Actions workflow files found"

    for workflow_path in workflow_paths:
        workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
        for reference in _uses_references(workflow):
            action_name, separator, version = reference.partition("@")
            if not separator:
                continue
            policy_name = next(
                (
                    name
                    for name in NODE24_ACTION_MINIMUM_MAJORS
                    if action_name == name or action_name.startswith(f"{name}/")
                ),
                None,
            )
            if policy_name is None:
                continue
            major_match = re.fullmatch(r"v(\d+)(?:\.\d+){0,2}", version)
            if major_match is None:
                continue
            minimum_major = NODE24_ACTION_MINIMUM_MAJORS[policy_name]
            if int(major_match.group(1)) < minimum_major:
                relative_path = workflow_path.relative_to(REPO_ROOT).as_posix()
                violations.append(
                    f"{relative_path}: {reference} requires {policy_name}@v{minimum_major}+"
                )

    assert not violations, "Deprecated GitHub Action versions:\n" + "\n".join(violations)


def _single_command(step: dict) -> str | None:
    run = step.get("run")
    if not isinstance(run, str):
        return None
    if len(run.splitlines()) != 1:
        return None
    command = run.strip()
    return command or None


def _working_directory(job: dict, step: dict) -> str | None:
    return step.get("working-directory") or job.get("defaults", {}).get("run", {}).get(
        "working-directory"
    )


def _command_occurrences(workflow: dict, command: str) -> list[tuple[str, int, str | None]]:
    return [
        (job_name, step_index, _working_directory(job, step))
        for job_name, job in workflow["jobs"].items()
        for step_index, step in enumerate(job["steps"])
        if _single_command(step) == command
    ]


def _command_step_indexes(job: dict, command: str) -> list[int]:
    return [
        step_index
        for step_index, step in enumerate(job["steps"])
        if _single_command(step) == command
    ]


def _required_command_step(job: dict, command: str) -> int:
    indexes = _command_step_indexes(job, command)
    assert len(indexes) == 1
    return indexes[0]


def _assert_owned_by(workflow: dict, command: str, job_name: str) -> None:
    occurrences = _command_occurrences(workflow, command)
    assert len(occurrences) == 1
    assert occurrences[0][0] == job_name


def test_required_command_lookup_rejects_multiline_shell_spoofs():
    required = "python -m pytest -q"
    spoofed_runs = (
        f'echo "{required}"',
        "echo continued \\" + "\n" + required,
        f"cat <<'COMMAND'\n{required}\nCOMMAND",
        f"# claimed gate\n{required}",
    )

    for run in spoofed_runs:
        workflow = {"jobs": {"spoof": {"steps": [{"run": run}]}}}
        assert _command_occurrences(workflow, required) == []

    workflow = {"jobs": {"real": {"steps": [{"run": required}]}}}
    assert _command_occurrences(workflow, required) == [("real", 0, None)]


def test_publish_workflow_is_main_only_and_runs_complete_release_gates():
    workflow = _load_workflow("publish.yml")
    tests_job = workflow["jobs"]["tests"]
    assert tests_job["if"] == "${{ github.event_name == 'release' || github.ref == 'refs/heads/main' }}"

    checkout = next(
        step for step in tests_job["steps"] if step.get("uses") == "actions/checkout@v5"
    )
    assert checkout["with"]["fetch-depth"] == 0

    main_gate = next(
        step for step in tests_job["steps"]
        if step.get("name") == "Verify release commit belongs to main"
    )
    assert "git fetch origin main --no-tags" in main_gate["run"]
    assert "git merge-base --is-ancestor" in main_gate["run"]

    install_step = next(
        step for step in tests_job["steps"]
        if step.get("name") == "Install dependencies"
    )
    install_lines = [line.strip() for line in install_step["run"].splitlines() if line.strip()]
    assert 'python -m pip install -e ".[dev,docs,databricks,viz]"' in install_lines

    required_commands = (
        "python scripts/smoke_examples.py",
        "python scripts/runtime_resilience.py",
        "npx playwright install --with-deps chromium",
        "npm run test:e2e",
    )
    for command in required_commands:
        _assert_owned_by(workflow, command, "tests")

    assert workflow["jobs"]["publish"]["needs"] == "tests"


def test_publishing_docs_require_manual_runs_from_main():
    publishing = (REPO_ROOT / "docs" / "PUBLISHING.md").read_text(encoding="utf-8")

    assert "select the `main` branch" in publishing
    assert "exact release branch or tag" not in publishing


def test_ci_splits_python_matrix_from_python_311_integration_gates():
    workflow = _load_workflow("ci.yml")
    jobs = workflow["jobs"]

    assert {"python", "integration"} <= set(jobs)

    python_job = jobs["python"]
    assert python_job["strategy"]["matrix"]["python-version"] == [
        "3.10",
        "3.11",
        "3.12",
        "3.13",
    ]
    python_setup = next(
        step for step in python_job["steps"] if step.get("uses") == "actions/setup-python@v6"
    )
    assert python_setup["with"]["python-version"] == "${{ matrix.python-version }}"
    python_install = 'python -m pip install -e ".[dev,viz]"'
    _required_command_step(python_job, python_install)
    for command in (
        "python -m pytest -q",
        "python -m ruff check brickflowui tests examples",
        "python -m mypy brickflowui",
    ):
        _assert_owned_by(workflow, command, "python")
    python_gate_order = (
        python_install,
        "python -m pytest -q",
        "python -m ruff check brickflowui tests examples",
        "python -m mypy brickflowui",
    )
    python_gate_steps = [
        _required_command_step(python_job, command) for command in python_gate_order
    ]
    assert python_gate_steps == sorted(python_gate_steps)

    integration_job = jobs["integration"]
    integration_setup = next(
        step for step in integration_job["steps"] if step.get("uses") == "actions/setup-python@v6"
    )
    assert integration_setup["with"]["python-version"] == "3.11"
    assert any(
        step.get("uses") == "actions/setup-node@v5" for step in integration_job["steps"]
    )

    integration_installs = (
        'python -m pip install -e ".[dev,docs,databricks,viz]"',
        "python -m pip install build",
    )
    for command in integration_installs:
        _required_command_step(integration_job, command)

    frontend_commands = (
        "npm ci",
        "npm test -- --run",
        "npm run lint",
        "npm audit --audit-level=high",
        "npm run typecheck",
        "npm run build",
        "npm run test:bundle",
        "npm run check:bundle",
    )
    for command in frontend_commands:
        _assert_owned_by(workflow, command, "integration")
        assert _command_occurrences(workflow, command)[0][2] == "frontend"

    for command in (
        "git diff --exit-code -- brickflowui/frontend/dist",
        "python scripts/smoke_examples.py",
        "python scripts/runtime_resilience.py",
        "python scripts/generate_component_reference.py",
        "git diff --exit-code -- docs/components/reference",
        "python -m mkdocs build --strict",
        "python -m build",
    ):
        _assert_owned_by(workflow, command, "integration")

    integration_gate_order = (
        *integration_installs,
        "npm ci",
        "npm test -- --run",
        "npm run lint",
        "npm audit --audit-level=high",
        "npm run typecheck",
        "npm run build",
        "npm run test:bundle",
        "npm run check:bundle",
        "git diff --exit-code -- brickflowui/frontend/dist",
        "python scripts/smoke_examples.py",
        "python scripts/runtime_resilience.py",
        "python scripts/generate_component_reference.py",
        "git diff --exit-code -- docs/components/reference",
        "python -m mkdocs build --strict",
        "python -m build",
    )
    integration_gate_steps = [
        _required_command_step(integration_job, command) for command in integration_gate_order
    ]
    assert integration_gate_steps == sorted(integration_gate_steps)


def test_security_audits_installed_project_dependencies():
    workflow = _load_workflow("security.yml")
    audit_job = workflow["jobs"]["audit"]
    assert any(step.get("uses") == "actions/setup-node@v5" for step in audit_job["steps"])

    audit_step = _required_command_step(audit_job, "python -m pip_audit")
    setuptools_upgrade = 'python -m pip install --upgrade pip "setuptools>=83"'
    assert _required_command_step(audit_job, setuptools_upgrade) < audit_step
    for install_command in (
        "python -m pip install pip-audit",
        'python -m pip install -e ".[dev]"',
        'python -m pip install -e ".[databricks,viz]"',
    ):
        assert _required_command_step(audit_job, install_command) < audit_step

    for frontend_command in ("npm ci", "npm audit --omit=dev"):
        occurrences = _command_occurrences(workflow, frontend_command)
        assert len(occurrences) == 1
        assert occurrences[0][0] == "audit"
        assert occurrences[0][2] == "frontend"
    assert _required_command_step(audit_job, "npm ci") < _required_command_step(
        audit_job, "npm audit --omit=dev"
    )


def test_source_checkout_docs_launch_flagship_as_a_module():
    """Keep local examples on checkout code instead of a stale site package."""
    examples_doc = (REPO_ROOT / "docs" / "EXAMPLES.md").read_text(encoding="utf-8")
    build_doc = (REPO_ROOT / "docs" / "BUILD.md").read_text(encoding="utf-8")
    module_command = "python -m examples.data_pipeline_command_center.app"

    assert module_command in examples_doc
    assert module_command in build_doc


def test_package_uses_canonical_async_framework_classifiers():
    with (REPO_ROOT / "pyproject.toml").open("rb") as pyproject_file:
        project = tomllib.load(pyproject_file)["project"]
    classifiers = project["classifiers"]

    assert classifiers.count("Framework :: AsyncIO") == 1
    assert classifiers.count("Framework :: FastAPI") == 1
    assert "Topic :: Internet :: WWW/HTTP :: ASGI :: Application" not in classifiers
    assert "Topic :: Internet :: WWW/HTTP :: WSGI :: Application" not in classifiers


def test_python_310_dev_dependencies_include_tomllib_backport():
    with (REPO_ROOT / "pyproject.toml").open("rb") as pyproject_file:
        project = tomllib.load(pyproject_file)["project"]

    assert 'tomli>=2.0.1; python_version < "3.11"' in project["optional-dependencies"]["dev"]


def test_current_changelog_does_not_claim_an_unconfigured_twine_gate():
    changelog = (REPO_ROOT / "docs" / "CHANGELOG.md").read_text(encoding="utf-8")
    current_release = changelog.split("## 0.1.14", maxsplit=1)[0]

    assert "Twine" not in current_release


def test_frontend_distribution_contains_only_one_current_entry_bundle():
    dist = REPO_ROOT / "brickflowui" / "frontend" / "dist"
    index_html = (dist / "index.html").read_text(encoding="utf-8")
    assets = dist / "assets"

    entry_bundles = list(assets.glob("index-*.js"))
    assert len(entry_bundles) == 1, (
        "frontend/dist contains stale entry bundles; run a clean frontend build"
    )

    references = re.findall(r'(?:src|href)="/assets/([^"]+)"', index_html)
    assert references
    assert all((assets / reference).is_file() for reference in references)
