from __future__ import annotations

from collections.abc import AsyncIterator, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from agentmuru.sessions import Message


@dataclass(frozen=True, slots=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float | None = None

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass(frozen=True, slots=True)
class ModelCapabilities:
    text: bool = True
    streaming: bool = True
    tool_calling: bool = False
    structured_output: bool = False
    vision: bool = False
    audio: bool = False
    reasoning: bool = False
    embeddings: bool = False

    def require(self, capability: str) -> None:
        if not hasattr(self, capability):
            raise ValueError(f"Unknown model capability '{capability}'")
        if not bool(getattr(self, capability)):
            raise ValueError(f"Model does not support required capability '{capability}'")


@dataclass(frozen=True, slots=True)
class ModelRequest:
    messages: Sequence[Message]
    instructions: str = ""
    tools: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    settings: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TextDelta:
    text: str


@dataclass(frozen=True, slots=True)
class ToolCall:
    id: str
    name: str
    arguments: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class ModelCompleted:
    usage: Usage = field(default_factory=Usage)


@dataclass(frozen=True, slots=True)
class ModelFailed:
    code: str
    message: str
    retryable: bool = False


ModelEvent = TextDelta | ToolCall | ModelCompleted | ModelFailed


class ModelProvider(Protocol):
    name: str
    model_id: str
    capabilities: ModelCapabilities

    def stream(self, request: ModelRequest) -> AsyncIterator[ModelEvent]: ...
