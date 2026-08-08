from __future__ import annotations

from collections.abc import Callable

from .base import ModelProvider

ModelFactory = Callable[[], ModelProvider]


class ModelRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, ModelFactory] = {}

    def register(self, name: str, factory: ModelFactory) -> None:
        key = name.strip().lower()
        if not key:
            raise ValueError("Model registry name cannot be empty")
        if key in self._factories:
            raise ValueError(f"Model '{name}' is already registered")
        self._factories[key] = factory

    def get(self, name: str) -> ModelProvider:
        key = name.strip().lower()
        try:
            return self._factories[key]()
        except KeyError as exc:
            raise KeyError(f"Model '{name}' is not registered") from exc

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._factories))
