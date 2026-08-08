from __future__ import annotations

import builtins
from collections.abc import AsyncIterator
from threading import RLock
from typing import Protocol

from agentmuru.core.bus import EventBus
from agentmuru.core.errors import SessionNotFoundError
from agentmuru.core.events import RuntimeEvent

from .models import Session


class SessionStore(Protocol):
    def create(self, *, user_id: str | None = None, title: str | None = None) -> Session: ...

    def get(self, session_id: str) -> Session: ...

    def list(self, *, user_id: str | None = None) -> builtins.list[Session]: ...

    def save(self, session: Session) -> None: ...

    def append_event(self, session_id: str, event: RuntimeEvent) -> RuntimeEvent: ...

    def events(
        self, session_id: str, *, after_sequence: int = 0
    ) -> builtins.list[RuntimeEvent]: ...


class InMemorySessionStore:
    def __init__(self, *, subscriber_queue_size: int = 256) -> None:
        self._sessions: dict[str, Session] = {}
        self._lock = RLock()
        self._bus = EventBus(queue_size=subscriber_queue_size)

    def create(self, *, user_id: str | None = None, title: str | None = None) -> Session:
        session = Session(user_id=user_id, title=title)
        with self._lock:
            self._sessions[session.id] = session
        return session

    def get(self, session_id: str) -> Session:
        with self._lock:
            try:
                return self._sessions[session_id]
            except KeyError as exc:
                raise SessionNotFoundError(f"Session '{session_id}' was not found") from exc

    def list(self, *, user_id: str | None = None) -> builtins.list[Session]:
        with self._lock:
            sessions = list(self._sessions.values())
        if user_id is not None:
            sessions = [session for session in sessions if session.user_id == user_id]
        return sorted(sessions, key=lambda session: session.updated_at, reverse=True)

    def save(self, session: Session) -> None:
        with self._lock:
            if session.id not in self._sessions:
                raise SessionNotFoundError(f"Session '{session.id}' was not found")
            self._sessions[session.id] = session

    def append_event(self, session_id: str, event: RuntimeEvent) -> RuntimeEvent:
        if event.session_id != session_id:
            raise ValueError("Event session_id does not match the target session")
        with self._lock:
            session = self.get(session_id)
            persisted = event.with_sequence(len(session.events) + 1)
            session.events.append(persisted)
            session.updated_at = persisted.timestamp
        self._bus.publish(persisted)
        return persisted

    def events(
        self, session_id: str, *, after_sequence: int = 0
    ) -> builtins.list[RuntimeEvent]:
        with self._lock:
            return [event for event in self.get(session_id).events if event.sequence > after_sequence]

    async def subscribe(
        self,
        session_id: str,
        *,
        after_sequence: int = 0,
    ) -> AsyncIterator[RuntimeEvent]:
        queue = self._bus.subscribe(session_id)
        try:
            for event in self.events(session_id, after_sequence=after_sequence):
                yield event
            while True:
                event = await queue.get()
                if event.sequence > after_sequence:
                    after_sequence = event.sequence
                    yield event
        finally:
            self._bus.unsubscribe(session_id, queue)
