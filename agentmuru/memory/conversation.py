from __future__ import annotations

from threading import RLock


class ConversationMemory:
    """Explicit, in-memory retention; disabled unless ``retain=True`` is provided."""

    def __init__(self, *, retain: bool = False) -> None:
        self.retain = retain
        self._values: dict[str, list[str]] = {}
        self._lock = RLock()

    async def save(self, session_id: str, value: str) -> None:
        if not self.retain:
            return
        with self._lock:
            self._values.setdefault(session_id, []).append(value)

    async def recall(self, session_id: str) -> tuple[str, ...]:
        with self._lock:
            return tuple(self._values.get(session_id, ()))

    async def clear(self, session_id: str) -> None:
        with self._lock:
            self._values.pop(session_id, None)
