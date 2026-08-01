"""BrickflowUI CLI package."""

from typing import Any

__all__ = ["app"]


def __getattr__(name: str) -> Any:
    """Load the Typer app lazily so ``python -m brickflowui.cli.main`` stays warning-free."""
    if name == "app":
        from .main import app

        return app
    raise AttributeError(name)
