from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True, slots=True)
class CommandSpec:
    name: str
    argv: tuple[str, ...]
    cwd: Path
    environment: dict[str, str]


def clean_environment(source: Mapping[str, str] | None = None) -> dict[str, str]:
    environment = dict(source or os.environ)
    environment.pop("PYTHONPATH", None)
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def _venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def build_smoke_command(venv_dir: Path, smoke_script: Path) -> CommandSpec:
    return CommandSpec(
        name="installed_smoke",
        argv=(str(_venv_python(venv_dir)), str(smoke_script)),
        cwd=smoke_script.parent,
        environment=clean_environment(),
    )


def _run(command: CommandSpec, *, timeout: float = 600) -> dict[str, object]:
    started = time.perf_counter()
    completed = subprocess.run(
        command.argv,
        cwd=command.cwd,
        env=command.environment,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    return {
        "name": command.name,
        "argv": list(command.argv),
        "cwd": str(command.cwd),
        "exit_code": completed.returncode,
        "duration_seconds": round(time.perf_counter() - started, 3),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _server_check(
    python: Path,
    scaffold: Path,
    environment: dict[str, str],
) -> dict[str, object]:
    port = _free_port()
    argv = (
        str(python),
        "-m",
        "agentmuru.cli.main",
        "run",
        "app:application",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    )
    started = time.perf_counter()
    process = subprocess.Popen(
        argv,
        cwd=scaffold,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    health: dict[str, object] | None = None
    failure: str | None = None
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if process.poll() is not None:
                failure = "server_exited_before_health_check"
                break
            try:
                with urlopen(f"http://127.0.0.1:{port}/health", timeout=1) as response:
                    health = json.loads(response.read().decode("utf-8"))
                break
            except OSError:
                time.sleep(0.1)
        if health is None and failure is None:
            failure = "server_health_check_timed_out"
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        stdout, stderr = process.communicate(timeout=5)
    passed = health == {
        "status": "ok",
        "product": "AgentMuru",
        "protocol_version": 1,
    }
    return {
        "name": "installed_server_health",
        "argv": list(argv),
        "cwd": str(scaffold),
        "exit_code": 0 if passed else 1,
        "duration_seconds": round(time.perf_counter() - started, 3),
        "stdout": stdout,
        "stderr": stderr,
        "health": health,
        "failure": failure,
    }


def qualify(wheel: Path, report_path: Path) -> dict[str, object]:
    wheel = wheel.expanduser().resolve()
    if not wheel.is_file():
        raise FileNotFoundError(f"Wheel was not found: {wheel}")
    scratch_root = ROOT / ".tmp"
    scratch_root.mkdir(parents=True, exist_ok=True)
    workdir = Path(
        tempfile.mkdtemp(prefix=f"qualification-{wheel.stem}-", dir=scratch_root)
    ).resolve()
    venv_dir = workdir / "venv"
    smoke_script = workdir / "installed_smoke.py"
    scaffold = workdir / "scaffold"
    environment = clean_environment()
    commands: list[dict[str, object]] = []
    failures: list[str] = []
    scenarios: dict[str, object] = {}

    def execute(spec: CommandSpec, *, timeout: float = 600) -> dict[str, object]:
        result = _run(spec, timeout=timeout)
        commands.append(result)
        if result["exit_code"] != 0:
            failures.append(spec.name)
        return result

    execute(
        CommandSpec(
            name="create_venv",
            argv=(sys.executable, "-m", "venv", str(venv_dir)),
            cwd=workdir,
            environment=environment,
        )
    )
    python = _venv_python(venv_dir)
    if python.is_file():
        execute(
            CommandSpec(
                name="install_wheel_with_databricks_extra",
                argv=(
                    str(python),
                    "-m",
                    "pip",
                    "install",
                    "--disable-pip-version-check",
                    f"{wheel}[databricks]",
                ),
                cwd=workdir,
                environment=environment,
            ),
            timeout=900,
        )
        execute(
            CommandSpec(
                name="pip_check",
                argv=(str(python), "-m", "pip", "check"),
                cwd=workdir,
                environment=environment,
            )
        )
        execute(
            CommandSpec(
                name="cli_version",
                argv=(str(python), "-m", "agentmuru.cli.main", "version"),
                cwd=workdir,
                environment=environment,
            )
        )
        execute(
            CommandSpec(
                name="cli_doctor",
                argv=(str(python), "-m", "agentmuru.cli.main", "doctor"),
                cwd=workdir,
                environment=environment,
            )
        )
        execute(
            CommandSpec(
                name="cli_init",
                argv=(
                    str(python),
                    "-m",
                    "agentmuru.cli.main",
                    "init",
                    str(scaffold),
                    "--name",
                    "Qualified AgentMuru App",
                ),
                cwd=workdir,
                environment=environment,
            )
        )
        execute(
            CommandSpec(
                name="scaffold_import",
                argv=(
                    str(python),
                    "-c",
                    "from app import application; print(application.title)",
                ),
                cwd=scaffold,
                environment=environment,
            )
        )
        shutil.copy2(ROOT / "qualification" / "installed_smoke.py", smoke_script)
        smoke_result = execute(build_smoke_command(venv_dir, smoke_script))
        if smoke_result["exit_code"] == 0:
            try:
                scenarios = json.loads(str(smoke_result["stdout"]).strip().splitlines()[-1])
            except (IndexError, json.JSONDecodeError):
                failures.append("installed_smoke_report")
        server_result = _server_check(python, scaffold, environment)
        commands.append(server_result)
        if server_result["exit_code"] != 0:
            failures.append("installed_server_health")
    else:
        failures.append("venv_python_missing")

    report: dict[str, object] = {
        "environment": {
            "driver_python": sys.executable,
            "driver_version": sys.version,
            "workdir": str(workdir),
            "wheel": str(wheel),
            "installed_python": str(python),
            "source_checkout": str(ROOT),
        },
        "commands": commands,
        "scenarios": scenarios,
        "databricks_live": {
            "attempted": False,
            "reason": "Live network qualification requires an explicit opt-in environment.",
        },
        "failures": failures,
    }
    report_path = report_path.expanduser().resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Qualify an AgentMuru wheel in isolation")
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = qualify(args.wheel, args.report)
    print(json.dumps({"report": str(args.report), "failures": report["failures"]}))
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
