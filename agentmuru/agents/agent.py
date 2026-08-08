from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from agentmuru.models import ModelProvider
from agentmuru.tools import Tool


@dataclass(frozen=True, slots=True)
class Agent:
    name: str
    instructions: str
    model: ModelProvider
    description: str = ""
    tools: tuple[Tool, ...] = ()
    permissions: frozenset[str] = field(default_factory=frozenset)
    model_settings: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        normalized = self.name.strip()
        if not normalized:
            raise ValueError("Agent name cannot be empty")
        object.__setattr__(self, "name", normalized)
        names = [item.name for item in self.tools]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise ValueError(f"Duplicate tool name: {', '.join(duplicates)}")

    def tool(self, name: str) -> Tool:
        for item in self.tools:
            if item.name == name:
                return item
        raise KeyError(f"Agent '{self.name}' has no tool named '{name}'")
