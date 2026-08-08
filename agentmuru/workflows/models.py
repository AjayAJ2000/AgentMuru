from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

WorkflowState = Mapping[str, Any]
StepHandler = Callable[[dict[str, Any]], "StepResult | Any"]


@dataclass(frozen=True, slots=True)
class StepResult:
    state: WorkflowState
    next_step: str | None = None


@dataclass(frozen=True, slots=True)
class Step:
    name: str
    handler: StepHandler
    retries: int = 0

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Workflow step name cannot be empty")
        if self.retries < 0:
            raise ValueError("Workflow step retries cannot be negative")


@dataclass(frozen=True, slots=True)
class Workflow:
    name: str
    steps: tuple[Step, ...]

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Workflow name cannot be empty")
        if not self.steps:
            raise ValueError("Workflow requires at least one step")
        names = [step.name for step in self.steps]
        if len(names) != len(set(names)):
            raise ValueError("Workflow step names must be unique")


class WorkflowStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class Checkpoint:
    step_name: str
    state: WorkflowState
    completed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True, slots=True)
class WorkflowResult:
    status: WorkflowStatus
    state: WorkflowState
    checkpoints: tuple[Checkpoint, ...] = ()
    error_code: str | None = None
