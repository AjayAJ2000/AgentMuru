from __future__ import annotations

import builtins
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from threading import RLock
from typing import Protocol

from agentmuru.core.bus import EventBus
from agentmuru.core.errors import RunNotFoundError, SessionNotFoundError
from agentmuru.core.events import RuntimeEvent

from .models import Message, RunRecord, RunStatus, Session


class SessionStore(Protocol):
    def create(self, *, user_id: str | None = None, title: str | None = None) -> Session: ...

    def get(self, session_id: str) -> Session: ...

    def list(self, *, user_id: str | None = None) -> builtins.list[Session]: ...

    def save(self, session: Session) -> None: ...

    def append_message(self, session_id: str, message: Message) -> Message: ...

    def create_run(self, run: RunRecord) -> RunRecord: ...

    def update_run(self, run: RunRecord) -> RunRecord: ...

    def get_run(self, run_id: str) -> RunRecord: ...

    def get_idempotent_run(self, session_id: str, key: str) -> RunRecord | None: ...

    def bind_idempotency_key(self, session_id: str, key: str, run_id: str) -> None: ...

    def recover_interrupted_runs(self) -> builtins.list[RunRecord]: ...

    def append_event(self, session_id: str, event: RuntimeEvent) -> RuntimeEvent: ...

    def events(
        self, session_id: str, *, after_sequence: int = 0
    ) -> builtins.list[RuntimeEvent]: ...


class InMemorySessionStore:
    def __init__(self, *, subscriber_queue_size: int = 256) -> None:
        self._sessions: dict[str, Session] = {}
        self._runs: dict[str, RunRecord] = {}
        self._idempotency: dict[tuple[str, str], str] = {}
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
            for run in session.runs:
                self._runs[run.id] = run

    def append_message(self, session_id: str, message: Message) -> Message:
        with self._lock:
            session = self.get(session_id)
            session.messages.append(message)
            session.updated_at = message.created_at
        return message

    def create_run(self, run: RunRecord) -> RunRecord:
        with self._lock:
            session = self.get(run.session_id)
            if run.id in self._runs:
                raise ValueError(f"Run '{run.id}' already exists")
            session.runs.append(run)
            session.updated_at = run.created_at
            self._runs[run.id] = run
        return run

    def update_run(self, run: RunRecord) -> RunRecord:
        with self._lock:
            current = self.get_run(run.id)
            if current.session_id != run.session_id:
                raise ValueError("Run session_id cannot be changed")
            session = self.get(run.session_id)
            for index, item in enumerate(session.runs):
                if item.id == run.id:
                    session.runs[index] = run
                    break
            else:  # pragma: no cover - protected by the run index invariant
                raise RunNotFoundError(f"Run '{run.id}' was not found")
            session.updated_at = run.completed_at or datetime.now(timezone.utc)
            self._runs[run.id] = run
        return run

    def get_run(self, run_id: str) -> RunRecord:
        with self._lock:
            try:
                return self._runs[run_id]
            except KeyError as exc:
                raise RunNotFoundError(f"Run '{run_id}' was not found") from exc

    def get_idempotent_run(self, session_id: str, key: str) -> RunRecord | None:
        with self._lock:
            run_id = self._idempotency.get((session_id, key))
            return self.get_run(run_id) if run_id is not None else None

    def bind_idempotency_key(self, session_id: str, key: str, run_id: str) -> None:
        if not key:
            raise ValueError("Idempotency key cannot be empty")
        with self._lock:
            self.get(session_id)
            run = self.get_run(run_id)
            if run.session_id != session_id:
                raise ValueError("Idempotency key and run must belong to the same session")
            index_key = (session_id, key)
            existing = self._idempotency.get(index_key)
            if existing is not None and existing != run_id:
                raise ValueError("Idempotency key is already bound to another run")
            self._idempotency[index_key] = run_id

    def recover_interrupted_runs(self) -> builtins.list[RunRecord]:
        recovered: builtins.list[RunRecord] = []
        terminal = {RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED}
        with self._lock:
            for run in self._runs.values():
                if run.status in terminal:
                    continue
                run.status = RunStatus.FAILED
                run.error_code = "process_interrupted"
                run.completed_at = datetime.now(timezone.utc)
                self.update_run(run)
                recovered.append(run)
        return recovered

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
