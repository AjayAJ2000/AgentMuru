from __future__ import annotations

import importlib
import os
import platform
import sys
from enum import Enum
from pathlib import Path
from typing import Any

import typer

from agentmuru.core.application import Application
from agentmuru.server import create_asgi_app
from agentmuru.version import __version__

app = typer.Typer(
    name="muru",
    help="Build and run observable, governed AI applications with AgentMuru.",
    no_args_is_help=True,
)


class ProviderChoice(str, Enum):
    FAKE = "fake"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


PROVIDER_TEMPLATES = {
    ProviderChoice.FAKE: {
        "import": "from agentmuru import Agent, Application, FakeModel, tool",
        "model": 'FakeModel.responses("AgentMuru is ready. Choose a provider when you are ready.")',
        "requirement": "agentmuru>=0.3,<0.4",
        "setup": "This starter uses AgentMuru's deterministic fake model, so no credentials are required.",
    },
    ProviderChoice.OPENAI: {
        "import": (
            "from agentmuru import Agent, Application, tool\n"
            "from agentmuru.integrations.openai import OpenAIModel"
        ),
        "model": "OpenAIModel()",
        "requirement": "agentmuru[openai]>=0.3,<0.4",
        "setup": "Set `OPENAI_API_KEY` in your environment before starting the application.",
    },
    ProviderChoice.ANTHROPIC: {
        "import": (
            "from agentmuru import Agent, Application, tool\n"
            "from agentmuru.integrations.anthropic import AnthropicModel"
        ),
        "model": "AnthropicModel()",
        "requirement": "agentmuru[anthropic]>=0.3,<0.4",
        "setup": "Set `ANTHROPIC_API_KEY` in your environment before starting the application.",
    },
    ProviderChoice.GOOGLE: {
        "import": (
            "from agentmuru import Agent, Application, tool\n"
            "from agentmuru.integrations.google import GoogleGenAIModel"
        ),
        "model": "GoogleGenAIModel()",
        "requirement": "agentmuru[google]>=0.3,<0.4",
        "setup": "Set `GOOGLE_API_KEY` in your environment before starting the application.",
    },
}


def load_application(target: str) -> Application:
    module_name, separator, attribute = target.partition(":")
    if not separator or not module_name or not attribute:
        raise typer.BadParameter("Application target must use module:attribute syntax")
    module = importlib.import_module(module_name)
    value = getattr(module, attribute, None)
    if not isinstance(value, Application):
        raise typer.BadParameter(f"'{target}' does not resolve to an AgentMuru Application")
    return value


def create_reload_app() -> Any:
    return create_asgi_app(load_application(os.environ["AGENTMURU_APP"]))


@app.command()
def version() -> None:
    """Print the installed AgentMuru version."""
    typer.echo(f"AgentMuru {__version__}")


@app.command()
def doctor() -> None:
    """Check the local runtime, package, and bundled workspace assets."""
    checks = [
        ("Python", sys.version_info >= (3, 10), platform.python_version()),
        (
            "Workspace assets",
            (Path(__file__).resolve().parents[1] / "frontend" / "dist" / "index.html").exists(),
            "bundled",
        ),
    ]
    failed = False
    for name, ready, detail in checks:
        failed = failed or not ready
        typer.echo(f"{'ready' if ready else 'missing':>7}  {name}: {detail}")
    if failed:
        raise typer.Exit(code=1)
    typer.echo("AgentMuru is ready.")


@app.command("init")
def init_project(
    path: Path = typer.Argument(..., help="Directory for the new project"),
    name: str = typer.Option("My AgentMuru App", "--name", help="Application display name"),
    provider: ProviderChoice = typer.Option(
        ProviderChoice.FAKE,
        "--provider",
        help="Model provider to configure",
        case_sensitive=False,
    ),
) -> None:
    """Create a minimal local AgentMuru project."""
    target = path.expanduser().resolve()
    if target.exists() and any(target.iterdir()):
        typer.echo(f"Refusing to overwrite nonempty directory: {target}", err=True)
        raise typer.Exit(code=2)
    target.mkdir(parents=True, exist_ok=True)
    template_root = Path(__file__).resolve().parent / "templates" / "default"
    provider_template = PROVIDER_TEMPLATES[provider]
    replacements = {
        "{{APP_NAME}}": name,
        (
            "from agentmuru import Agent, Application, FakeModel, tool  "
            "# {{PROVIDER_IMPORT}}"
        ): provider_template["import"],
        (
            '    model=FakeModel.responses("AgentMuru starter"),  '
            "# {{MODEL_CONSTRUCTOR}}"
        ): f'    model={provider_template["model"]},',
        "{{REQUIREMENT}}": provider_template["requirement"],
        "{{PROVIDER_SETUP}}": provider_template["setup"],
    }
    for source in template_root.iterdir():
        if source.is_file():
            content = source.read_text(encoding="utf-8")
            for marker, value in replacements.items():
                content = content.replace(marker, value)
            output_name = source.name.removesuffix(".template")
            (target / output_name).write_text(content, encoding="utf-8")
    typer.echo(f"Created AgentMuru project at {target}")
    typer.echo(f"Next: cd {target.name} && muru dev app:application")


def _serve(target: str, host: str, port: int, *, reload: bool) -> None:
    import uvicorn

    if reload:
        os.environ["AGENTMURU_APP"] = target
        uvicorn.run(
            "agentmuru.cli.main:create_reload_app",
            factory=True,
            host=host,
            port=port,
            reload=True,
        )
        return
    uvicorn.run(create_asgi_app(load_application(target)), host=host, port=port)


@app.command()
def dev(
    target: str = typer.Argument("app:application"),
    host: str = typer.Option("127.0.0.1"),
    port: int = typer.Option(8000),
) -> None:
    """Run an application with source reload for local development."""
    _serve(target, host, port, reload=True)


@app.command("run")
def run_application(
    target: str = typer.Argument("app:application"),
    host: str = typer.Option("0.0.0.0"),
    port: int = typer.Option(8000),
) -> None:
    """Run an application without source reload."""
    _serve(target, host, port, reload=False)


if __name__ == "__main__":
    app()
