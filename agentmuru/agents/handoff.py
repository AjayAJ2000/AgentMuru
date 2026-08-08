from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class Handoff:
    from_agent: str
    to_agent: str
    reason: str
    context: Mapping[str, Any] = field(default_factory=dict)
