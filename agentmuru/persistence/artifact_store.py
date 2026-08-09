from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any, Mapping

from agentmuru.artifacts import Artifact, ArtifactKind, ArtifactStore
from agentmuru.artifacts.store import validate_artifact_content
from agentmuru.core.errors import StorageCorruptError

from .codecs import decode_content, decode_json, encode_content, encode_json
from .database import SQLiteDatabase


def _timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("Persistent timestamps must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat()


def _datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise StorageCorruptError("Stored timestamp is invalid")
    return parsed.astimezone(timezone.utc)


def _artifact_from_row(row: sqlite3.Row) -> Artifact:
    try:
        kind = ArtifactKind(str(row["kind"]))
    except ValueError as exc:
        raise StorageCorruptError("Stored artifact kind is invalid") from exc
    metadata = decode_json(str(row["metadata"]))
    if not isinstance(metadata, dict):
        raise StorageCorruptError("Stored artifact metadata is invalid")
    return Artifact(
        id=str(row["id"]),
        session_id=str(row["session_id"]),
        run_id=str(row["run_id"]) if row["run_id"] is not None else None,
        kind=kind,
        name=str(row["name"]),
        content=decode_content(str(row["content_encoding"]), bytes(row["content"])),
        mime_type=str(row["mime_type"]),
        creator=str(row["creator"]),
        metadata=metadata,
        created_at=_datetime(str(row["created_at"])),
        updated_at=_datetime(str(row["updated_at"])),
    )


class SQLiteArtifactStore(ArtifactStore):
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    def create(
        self,
        *,
        session_id: str,
        kind: ArtifactKind,
        name: str,
        content: Any,
        mime_type: str,
        creator: str,
        run_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> Artifact:
        validate_artifact_content(content)
        safe_metadata = dict(metadata or {})
        content_encoding, encoded_content = encode_content(content)
        encoded_metadata = encode_json(safe_metadata)
        artifact = Artifact(
            session_id=session_id,
            run_id=run_id,
            kind=kind,
            name=name,
            content=content,
            mime_type=mime_type,
            creator=creator,
            metadata=safe_metadata,
        )

        def insert(connection: sqlite3.Connection) -> None:
            connection.execute(
                """
                INSERT INTO artifacts(
                    id, session_id, run_id, kind, name, content, content_encoding,
                    mime_type, creator, metadata, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact.id,
                    artifact.session_id,
                    artifact.run_id,
                    artifact.kind.value,
                    artifact.name,
                    encoded_content,
                    content_encoding,
                    artifact.mime_type,
                    artifact.creator,
                    encoded_metadata,
                    _timestamp(artifact.created_at),
                    _timestamp(artifact.updated_at),
                ),
            )

        self.database.write(insert, immediate=True)
        return artifact

    def get(self, artifact_id: str) -> Artifact:
        connection = self.database.connect()
        try:
            row = connection.execute(
                "SELECT * FROM artifacts WHERE id = ?", (artifact_id,)
            ).fetchone()
            if row is None:
                raise KeyError(f"Artifact '{artifact_id}' was not found")
            return _artifact_from_row(row)
        finally:
            connection.close()

    def list(self, *, session_id: str) -> list[Artifact]:
        connection = self.database.connect()
        try:
            rows = connection.execute(
                """
                SELECT * FROM artifacts
                WHERE session_id = ?
                ORDER BY created_at, rowid
                """,
                (session_id,),
            ).fetchall()
            return [_artifact_from_row(row) for row in rows]
        finally:
            connection.close()
