from __future__ import annotations

import asyncio
from collections import defaultdict
from threading import RLock

from .events import RuntimeEvent


class EventBus:
    """Bounded in-process fan-out for already-persisted runtime events."""

    def __init__(self, queue_size: int = 256) -> None:
        if queue_size < 1:
            raise ValueError("queue_size must be positive")
        self._queue_size = queue_size
        self._subscribers: dict[str, set[asyncio.Queue[RuntimeEvent]]] = defaultdict(set)
        self._lock = RLock()

    def subscribe(self, session_id: str) -> asyncio.Queue[RuntimeEvent]:
        queue: asyncio.Queue[RuntimeEvent] = asyncio.Queue(maxsize=self._queue_size)
        with self._lock:
            self._subscribers[session_id].add(queue)
        return queue

    def unsubscribe(self, session_id: str, queue: asyncio.Queue[RuntimeEvent]) -> None:
        with self._lock:
            queues = self._subscribers.get(session_id)
            if queues is None:
                return
            queues.discard(queue)
            if not queues:
                self._subscribers.pop(session_id, None)

    def publish(self, event: RuntimeEvent) -> None:
        with self._lock:
            queues = tuple(self._subscribers.get(event.session_id, ()))
        for queue in queues:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                queue.put_nowait(event)
