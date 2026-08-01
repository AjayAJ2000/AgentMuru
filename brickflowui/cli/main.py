"""
BrickflowUI CLI for scaffolding and running apps.

Commands:
  brickflowui new <name>    Scaffold a new Databricks App
  brickflowui dev           Run the local dev server with hot reload
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import typer

app = typer.Typer(
    name="brickflowui",
    help="BrickflowUI - Databricks-first Python UI framework",
    add_completion=False,
    rich_markup_mode="rich",
)

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def _env_copy_hint(app_name: str) -> str:
    if os.name == "nt":
        return f"cd {app_name}\n    copy .env.example .env"
    return f"cd {app_name}\n    cp .env.example .env"


def _cleanup_scaffold(path: Path) -> None:
    if not path.exists():
        return

    def _on_error(func, target, exc_info):
        try:
            os.chmod(target, 0o700)
        except OSError:
            pass
        try:
            func(target)
        except OSError:
            pass

    shutil.rmtree(path, onerror=_on_error)


def _validated_project_name(name: str) -> str:
    """Validate that a scaffold target is one direct child directory."""
    candidate = name.strip()
    path = Path(candidate)
    device_name = candidate.rstrip(" .").split(".", 1)[0].upper()
    cwd = Path.cwd().resolve()

    invalid = (
        not candidate
        or candidate != name
        or candidate in {".", ".."}
        or path.is_absolute()
        or "/" in candidate
        or "\\" in candidate
        or path.name != candidate
        or device_name in _WINDOWS_RESERVED_NAMES
        or (cwd / candidate).resolve().parent != cwd
    )
    if invalid:
        typer.echo(
            "[ERROR] Project name must be a single safe directory name.",
            err=True,
        )
        raise typer.Exit(2)

    return candidate


@app.command()
def new(
    name: str = typer.Argument(..., help="Name of the new Databricks App"),
):
    """
    Scaffold a new BrickflowUI Databricks App.

    Creates a folder with app.py, app.yaml, requirements.txt, and .env.example.
    """
    name = _validated_project_name(name)
    target = Path.cwd() / name
    if target.exists():
        typer.echo(f"[ERROR] Directory '{name}' already exists.", err=True)
        raise typer.Exit(1)

    template_dir = _TEMPLATES_DIR / "default"

    try:
        target.mkdir(parents=True, exist_ok=False)

        for template_file in template_dir.iterdir():
            if not template_file.is_file():
                continue
            content = template_file.read_text(encoding="utf-8")
            content = content.replace("{{APP_NAME}}", name)
            (target / template_file.name).write_text(content, encoding="utf-8")
    except PermissionError as exc:
        _cleanup_scaffold(target)
        typer.echo(
            f"[ERROR] BrickflowUI could not finish scaffolding '{name}' because of a filesystem permission error: {exc}",
            err=True,
        )
        raise typer.Exit(1) from exc
    except Exception:
        _cleanup_scaffold(target)
        raise

    typer.echo(
        f"""
Created BrickflowUI app: {name}/

  Files created:
    {name}/app.py           -> Root app and pages
    {name}/app.yaml         -> Databricks Apps config
    {name}/requirements.txt -> Python dependencies
    {name}/.env.example     -> Environment variables template

  Next steps:
    {_env_copy_hint(name)}
    # Edit .env with your DATABRICKS_HOST and DATABRICKS_TOKEN
    brickflowui dev
"""
    )


@app.command()
def dev(
    file: str = typer.Option("app.py", "--file", "-f", help="App entry point file"),
    port: int = typer.Option(8050, "--port", "-p", help="Dev server port"),
    reload: bool = typer.Option(True, "--reload/--no-reload", help="Enable hot reload"),
):
    """
    Run the local development server with hot reload.
    """
    app_file = Path.cwd() / file
    if not app_file.exists():
        typer.echo(f"[ERROR] {file} not found in current directory.", err=True)
        raise typer.Exit(1)

    typer.echo(f"BrickflowUI Dev Server -> http://localhost:{port}")
    typer.echo("Press Ctrl+C to stop.\n")

    os.environ.setdefault("BRICKFLOWUI_DEV", "1")

    if reload:
        import uvicorn

        spec_name = app_file.stem
        sys.path.insert(0, str(Path.cwd()))

        uvicorn.run(
            f"{spec_name}:app.server",
            host="0.0.0.0",
            port=port,
            reload=True,
            reload_dirs=[str(Path.cwd())],
        )
    else:
        subprocess.run([sys.executable, file], check=False)


if __name__ == "__main__":
    app()
