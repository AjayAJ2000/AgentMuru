from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from agentmuru.approvals import ApprovalRequest, ApprovalStatus, ApprovalStore
from agentmuru.approvals.store import validate_approval_arguments
from agentmuru.core.errors import StorageCorruptError

from .codecs import decode_json, encode_json
from .database import SQLiteDatabase


def _timestamp(value: datetime | None) -> str | None:
    if value is None:
        return None
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


def _approval_from_row(row: sqlite3.Row) -> ApprovalRequest:
    try:
        status = ApprovalStatus(str(row["status"]))
    except ValueError as exc:
        raise StorageCorruptError("Stored approval status is invalid") from exc
    arguments = decode_json(str(row["arguments"]))
    if not isinstance(arguments, dict):
        raise StorageCorruptError("Stored approval arguments are invalid")
    requested_at = _datetime(str(row["requested_at"]))
    assert requested_at is not None
    return ApprovalRequest(
        id=str(row["id"]),
        session_id=str(row["session_id"]),
        run_id=str(row["run_id"]),
        tool_call_id=str(row["tool_call_id"]),
        tool_name=str(row["tool_name"]),
        arguments=arguments,
        permission=str(row["permission"]) if row["permission"] is not None else None,
        risk=str(row["risk"]),
        status=status,
        requested_at=requested_at,
        expires_at=_datetime(str(row["expires_at"])) if row["expires_at"] is not None else None,
        decided_at=_datetime(str(row["decided_at"])) if row["decided_at"] is not None else None,
        actor=str(row["actor"]) if row["actor"] is not None else None,
        reason=str(row["reason"]) if row["reason"] is not None else None,
    )


class SQLiteApprovalStore(ApprovalStore):
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    def create(self, request: ApprovalRequest) -> ApprovalRequest:
        validate_approval_arguments(request)
        arguments = encode_json(dict(request.arguments))

        def insert(connection: sqlite3.Connection) -> None:
            connection.execute(
                """
                INSERT INTO approvals(
                    id, session_id, run_id, tool_call_id, tool_name, arguments,
                    permission, risk, status, requested_at, expires_at,
                    decided_at, actor, reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request.id,
                    request.session_id,
                    request.run_id,
                    request.tool_call_id,
                    request.tool_name,
                    arguments,
                    request.permission,
                    request.risk,
                    request.status.value,
                    _timestamp(request.requested_at),
                    _timestamp(request.expires_at),
                    _timestamp(request.decided_at),
                    request.actor,
                    request.reason,
                ),
            )

        self.database.write(insert, immediate=True)
        return request

    def get(self, approval_id: str) -> ApprovalRequest:
        connection = self.database.connect()
        try:
            row = connection.execute(
                "SELECT * FROM approvals WHERE id = ?", (approval_id,)
            ).fetchone()
            if row is None:
                raise KeyError(f"Approval '{approval_id}' was not found")
            return _approval_from_row(row)
        finally:
            connection.close()

    def list(self, *, session_id: str | None = None) -> list[ApprovalRequest]:
        connection = self.database.connect()
        try:
            if session_id is None:
                rows = connection.execute(
                    "SELECT * FROM approvals ORDER BY requested_at, rowid"
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT * FROM approvals
                    WHERE session_id = ?
                    ORDER BY requested_at, rowid
                    """,
                    (session_id,),
                ).fetchall()
            return [_approval_from_row(row) for row in rows]
        finally:
            connection.close()

    def save(self, request: ApprovalRequest) -> ApprovalRequest:
        validate_approval_arguments(request)
        arguments = encode_json(dict(request.arguments))

        def update(connection: sqlite3.Connection) -> None:
            cursor = connection.execute(
                """
                UPDATE approvals SET
                    session_id = ?, run_id = ?, tool_call_id = ?, tool_name = ?,
                    arguments = ?, permission = ?, risk = ?, status = ?,
                    requested_at = ?, expires_at = ?, decided_at = ?, actor = ?, reason = ?
                WHERE id = ?
                """,
                (
                    request.session_id,
                    request.run_id,
                    request.tool_call_id,
                    request.tool_name,
                    arguments,
                    request.permission,
                    request.risk,
                    request.status.value,
                    _timestamp(request.requested_at),
                    _timestamp(request.expires_at),
                    _timestamp(request.decided_at),
                    request.actor,
                    request.reason,
                    request.id,
                ),
            )
            if cursor.rowcount == 0:
                raise KeyError(f"Approval '{request.id}' was not found")

        self.database.write(update, immediate=True)
        return request

