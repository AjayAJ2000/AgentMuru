from __future__ import annotations

from collections.abc import AsyncIterator, Iterable, Sequence

from .base import (
    ModelCapabilities,
    ModelCompleted,
    ModelEvent,
    ModelRequest,
    TextDelta,
)


class FakeModel:
    """Deterministic provider used by tests, examples, and local exploration."""

    name = "fake"
    capabilities = ModelCapabilities(text=True, streaming=True, tool_calling=True)

    def __init__(self, turns: Sequence[Sequence[ModelEvent]]) -> None:
        if not turns:
            raise ValueError("FakeModel requires at least one scripted turn")
        self._turns = [tuple(turn) for turn in turns]
        self._cursor = 0
        self.requests: list[ModelRequest] = []

    @classmethod
    def script(cls, events: Iterable[ModelEvent]) -> "FakeModel":
        return cls([tuple(events)])

    @classmethod
    def turns(cls, *turns: Sequence[ModelEvent]) -> "FakeModel":
        return cls(turns)

    @classmethod
    def responses(cls, *responses: str) -> "FakeModel":
        if not responses:
            raise ValueError("At least one response is required")
        return cls([(TextDelta(response), ModelCompleted()) for response in responses])

    async def stream(self, request: ModelRequest) -> AsyncIterator[ModelEvent]:
        self.requests.append(request)
        index = min(self._cursor, len(self._turns) - 1)
        self._cursor += 1
        for event in self._turns[index]:
            yield event
