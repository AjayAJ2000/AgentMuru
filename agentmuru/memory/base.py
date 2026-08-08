from __future__ import annotations

from typing import Protocol


class Memory(Protocol):
    async def save(self, session_id: str, value: str) -> None: ...

    async def recall(self, session_id: str) -> tuple[str, ...]: ...

    async def clear(self, session_id: str) -> None: ...
