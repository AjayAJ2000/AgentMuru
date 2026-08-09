from __future__ import annotations

import asyncio
import builtins
import sqlite3
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any

from agentmuru.core.bus import EventBus
from agentmuru.core.errors import (
    RunNotFoundError,
    SessionNotFoundError,
    StorageCorruptError,
)
from agentmuru.core.events import EventType, RuntimeEvent
from agentmuru.sessions import Message, MessageRole, RunRecord, RunStatus, Session

from .codecs import decode_json, encode_json
from .database import SQLiteDatabase


def _timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("Persistent timestamps must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat()


def _datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise StorageCorruptError("Stored timestamp is invalid")
    return parsed.astimezone(timezone.utc)


def _metadata(value: str) -> dict[str, Any]:
    decoded = decode_json(value)
    if not isinstance(decoded, dict):
        raise StorageCorruptError("Stored session metadata is invalid")
    return decoded


def _message_from_row(row: sqlite3.Row) -> Message:
    created_at = _datetime(str(row["created_at"]))
    assert created_at is not None
    try:
        role = MessageRole(str(row["role"]))
    except ValueError as exc:
        raise StorageCorruptError("Stored message role is invalid") from exc
    return Message(
        id=str(row["id"]),
        role=role,
        content=str(row["content"]),
        created_at=created_at,
        name=str(row["name"]) if row["name"] is not None else None,
        tool_call_id=(
            str(row["tool_call_id"]) if row["tool_call_id"] is not None else None
        ),
    )


def _run_from_row(row: sqlite3.Row) -> RunRecord:
    created_at = _datetime(str(row["created_at"]))
    assert created_at is not None
    try:
        status = RunStatus(str(row["status"]))
    except ValueError as exc:
        raise StorageCorruptError("Stored run status is invalid") from exc
    return RunRecord(
        id=str(row["id"]),
        session_id=str(row["session_id"]),
        agent_name=str(row["agent_name"]),
        status=status,
        created_at=created_at,
        completed_at=_datetime(
            str(row["completed_at"]) if row["completed_at"] is not None else None
        ),
        error_code=str(row["error_code"]) if row["error_code"] is not None else None,
    )


def _event_from_row(row: sqlite3.Row) -> RuntimeEvent:
    return RuntimeEvent(
        id=str(row["id"]),
        type=EventType(str(row["type"])),
        timestamp=_datetime(str(row["timestamp"])) or datetime.now(timezone.utc),
        session_id=str(row["session_id"]),
        sequence=int(row["sequence"]),
        run_id=str(row["run_id"]) if row["run_id"] is not None else None,
        trace_id=str(row["trace_id"]) if row["trace_id"] is not None else None,
        parent_id=str(row["parent_id"]) if row["parent_id"] is not None else None,
        payload=decode_json(str(row["payload"])),
    )


class SQLiteSessionStore:
    def __init__(
        self,
        database: SQLiteDatabase,
        *,
        poll_interval: float = 0.05,
        subscriber_queue_size: int = 256,
    ) -> None:
        if poll_interval <= 0:
            raise ValueError("poll_interval must be positive")
        self.database = database
        self.poll_interval = poll_interval
        self._bus = EventBus(queue_size=subscriber_queue_size)

    def create(self, *, user_id: str | None = None, title: str | None = None) -> Session:
        session = Session(user_id=user_id, title=title)
        metadata = encode_json(session.metadata)

        def insert(connection: sqlite3.Connection) -> None:
            connection.execute(
                """
                INSERT INTO sessions(id, created_at, updated_at, user_id, title, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session.id,
                    _timestamp(session.created_at),
                    _timestamp(session.updated_at),
                    session.user_id,
                    session.title,
                    metadata,
                ),
            )
            connection.execute(
                "INSERT INTO event_counters(session_id, next_sequence) VALUES (?, 1)",
                (session.id,),
            )

        self.database.write(insert, immediate=True)
        return session

    def get(self, session_id: str) -> Session:
        connection = self.database.connect()
        try:
            row = connection.execute(
                "SELECT * FROM sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
            if row is None:
                raise SessionNotFoundError(f"Session '{session_id}' was not found")
            messages = [
                _message_from_row(item)
                for item in connection.execute(
                    "SELECT * FROM messages WHERE session_id = ? ORDER BY position",
                    (session_id,),
                ).fetchall()
            ]
            runs = [
                _run_from_row(item)
                for item in connection.execute(
                    "SELECT * FROM runs WHERE session_id = ? ORDER BY created_at, id",
                    (session_id,),
                ).fetchall()
            ]
            events = [
                _event_from_row(item)
                for item in connection.execute(
                    "SELECT * FROM events WHERE session_id = ? ORDER BY sequence",
                    (session_id,),
                ).fetchall()
            ]
            created_at = _datetime(str(row["created_at"]))
            updated_at = _datetime(str(row["updated_at"]))
            assert created_at is not None and updated_at is not None
            return Session(
                id=str(row["id"]),
                created_at=created_at,
                updated_at=updated_at,
                user_id=str(row["user_id"]) if row["user_id"] is not None else None,
                title=str(row["title"]) if row["title"] is not None else None,
                metadata=_metadata(str(row["metadata"])),
                messages=messages,
                runs=runs,
                events=events,
            )
        finally:
            connection.close()

    def list(self, *, user_id: str | None = None) -> builtins.list[Session]:
        connection = self.database.connect()
        try:
            if user_id is None:
                rows = connection.execute(
                    "SELECT id FROM sessions ORDER BY updated_at DESC, id"
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT id FROM sessions WHERE user_id = ? ORDER BY updated_at DESC, id",
                    (user_id,),
                ).fetchall()
        finally:
            connection.close()
        return [self.get(str(row["id"])) for row in rows]

    def save(self, session: Session) -> None:
        metadata = encode_json(session.metadata)
        updated_at = datetime.now(timezone.utc)

        def update(connection: sqlite3.Connection) -> None:
            cursor = connection.execute(
                """
                UPDATE sessions
                SET user_id = ?, title = ?, metadata = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    session.user_id,
                    session.title,
                    metadata,
                    _timestamp(updated_at),
                    session.id,
                ),
            )
            if cursor.rowcount != 1:
                raise SessionNotFoundError(f"Session '{session.id}' was not found")

        self.database.write(update, immediate=True)
        session.updated_at = updated_at

    def append_message(self, session_id: str, message: Message) -> Message:
        def insert(connection: sqlite3.Connection) -> None:
            row = connection.execute(
                "SELECT COALESCE(MAX(position), 0) + 1 FROM messages WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            assert row is not None
            try:
                connection.execute(
                    """
                    INSERT INTO messages(
                        id, session_id, position, role, content, created_at, name, tool_call_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        message.id,
                        session_id,
                        int(row[0]),
                        message.role.value,
                        message.content,
                        _timestamp(message.created_at),
                        message.name,
                        message.tool_call_id,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                if connection.execute(
                    "SELECT 1 FROM sessions WHERE id = ?", (session_id,)
                ).fetchone() is None:
                    raise SessionNotFoundError(f"Session '{session_id}' was not found") from exc
                raise
            connection.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (_timestamp(message.created_at), session_id),
            )

        self.database.write(insert, immediate=True)
        return message

    def create_run(self, run: RunRecord) -> RunRecord:
        def insert(connection: sqlite3.Connection) -> None:
            try:
                connection.execute(
                    """
                    INSERT INTO runs(
                        id, session_id, agent_name, status, created_at, completed_at, error_code
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run.id,
                        run.session_id,
                        run.agent_name,
                        run.status.value,
                        _timestamp(run.created_at),
                        _timestamp(run.completed_at) if run.completed_at else None,
                        run.error_code,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                if connection.execute(
                    "SELECT 1 FROM sessions WHERE id = ?", (run.session_id,)
                ).fetchone() is None:
                    raise SessionNotFoundError(
                        f"Session '{run.session_id}' was not found"
                    ) from exc
                raise ValueError(f"Run '{run.id}' already exists") from exc
            connection.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (_timestamp(run.created_at), run.session_id),
            )

        self.database.write(insert, immediate=True)
        return run

    def update_run(self, run: RunRecord) -> RunRecord:
        updated_at = run.completed_at or datetime.now(timezone.utc)

        def update(connection: sqlite3.Connection) -> None:
            cursor = connection.execute(
                """
                UPDATE runs
                SET agent_name = ?, status = ?, completed_at = ?, error_code = ?
                WHERE id = ? AND session_id = ?
                """,
                (
                    run.agent_name,
                    run.status.value,
                    _timestamp(run.completed_at) if run.completed_at else None,
                    run.error_code,
                    run.id,
                    run.session_id,
                ),
            )
            if cursor.rowcount != 1:
                raise RunNotFoundError(f"Run '{run.id}' was not found")
            connection.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (_timestamp(updated_at), run.session_id),
            )

        self.database.write(update, immediate=True)
        return run

    def get_run(self, run_id: str) -> RunRecord:
        connection = self.database.connect()
        try:
            row = connection.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
            if row is None:
                raise RunNotFoundError(f"Run '{run_id}' was not found")
            return _run_from_row(row)
        finally:
            connection.close()

    def get_idempotent_run(self, session_id: str, key: str) -> RunRecord | None:
        connection = self.database.connect()
        try:
            row = connection.execute(
                "SELECT run_id FROM idempotency_keys WHERE session_id = ? AND key = ?",
                (session_id, key),
            ).fetchone()
        finally:
            connection.close()
        return self.get_run(str(row["run_id"])) if row is not None else None

    def bind_idempotency_key(self, session_id: str, key: str, run_id: str) -> None:
        if not key:
            raise ValueError("Idempotency key cannot be empty")

        def bind(connection: sqlite3.Connection) -> None:
            run = connection.execute(
                "SELECT session_id FROM runs WHERE id = ?", (run_id,)
            ).fetchone()
            if run is None:
                raise RunNotFoundError(f"Run '{run_id}' was not found")
            if str(run["session_id"]) != session_id:
                raise ValueError("Idempotency key and run must belong to the same session")
            existing = connection.execute(
                "SELECT run_id FROM idempotency_keys WHERE session_id = ? AND key = ?",
                (session_id, key),
            ).fetchone()
            if existing is not None:
                if str(existing["run_id"]) != run_id:
                    raise ValueError("Idempotency key is already bound to another run")
                return
            connection.execute(
                "INSERT INTO idempotency_keys(session_id, key, run_id) VALUES (?, ?, ?)",
                (session_id, key, run_id),
            )

        self.database.write(bind, immediate=True)

    def recover_interrupted_runs(self) -> builtins.list[RunRecord]:
        terminal = (
            RunStatus.COMPLETED.value,
            RunStatus.FAILED.value,
            RunStatus.CANCELLED.value,
        )
        completed_at = datetime.now(timezone.utc)

        def recover(connection: sqlite3.Connection) -> builtins.list[str]:
            rows = connection.execute(
                """
                SELECT id FROM runs
                WHERE status NOT IN (?, ?, ?)
                ORDER BY created_at, id
                """,
                terminal,
            ).fetchall()
            run_ids = [str(row["id"]) for row in rows]
            if run_ids:
                connection.executemany(
                    """
                    UPDATE runs
                    SET status = ?, completed_at = ?, error_code = ?
                    WHERE id = ?
                    """,
                    [
                        (
                            RunStatus.FAILED.value,
                            _timestamp(completed_at),
                            "process_interrupted",
                            run_id,
                        )
                        for run_id in run_ids
                    ],
                )
            return run_ids

        run_ids = self.database.write(recover, immediate=True)
        return [self.get_run(run_id) for run_id in run_ids]

    def append_event(self, session_id: str, event: RuntimeEvent) -> RuntimeEvent:
        if event.session_id != session_id:
            raise ValueError("Event session_id does not match the target session")
        payload = encode_json(dict(event.payload))

        def append(connection: sqlite3.Connection) -> RuntimeEvent:
            row = connection.execute(
                """
                UPDATE event_counters
                SET next_sequence = next_sequence + 1
                WHERE session_id = ?
                RETURNING next_sequence - 1 AS sequence
                """,
                (session_id,),
            ).fetchone()
            if row is None:
                if connection.execute(
                    "SELECT 1 FROM sessions WHERE id = ?", (session_id,)
                ).fetchone() is None:
                    raise SessionNotFoundError(f"Session '{session_id}' was not found")
                raise StorageCorruptError("Stored event counter is missing")
            persisted = event.with_sequence(int(row["sequence"]))
            connection.execute(
                """
                INSERT INTO events(
                    id, session_id, sequence, type, timestamp,
                    run_id, trace_id, parent_id, payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    persisted.id,
                    session_id,
                    persisted.sequence,
                    persisted.type.value,
                    _timestamp(persisted.timestamp),
                    persisted.run_id,
                    persisted.trace_id,
                    persisted.parent_id,
                    payload,
                ),
            )
            connection.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (_timestamp(persisted.timestamp), session_id),
            )
            return persisted

        persisted = self.database.write(append, immediate=True)
        self._bus.publish(persisted)
        return persisted

    def events(
        self,
        session_id: str,
        *,
        after_sequence: int = 0,
    ) -> builtins.list[RuntimeEvent]:
        connection = self.database.connect()
        try:
            if connection.execute(
                "SELECT 1 FROM sessions WHERE id = ?", (session_id,)
            ).fetchone() is None:
                raise SessionNotFoundError(f"Session '{session_id}' was not found")
            rows = connection.execute(
                """
                SELECT * FROM events
                WHERE session_id = ? AND sequence > ?
                ORDER BY sequence
                """,
                (session_id, after_sequence),
            ).fetchall()
            return [_event_from_row(row) for row in rows]
        finally:
            connection.close()

    async def subscribe(
        self,
        session_id: str,
        *,
        after_sequence: int = 0,
    ) -> AsyncIterator[RuntimeEvent]:
        queue = self._bus.subscribe(session_id)
        cursor = after_sequence
        try:
            while True:
                pending = self.events(session_id, after_sequence=cursor)
                if pending:
                    for event in pending:
                        cursor = event.sequence
                        yield event
                    continue
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=self.poll_interval)
                except asyncio.TimeoutError:
                    continue
                if event.sequence > cursor:
                    cursor = event.sequence
                    yield event
        finally:
            self._bus.unsubscribe(session_id, queue)
