from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from agentmuru.core.errors import StorageBusyError, StorageCorruptError, StorageMigrationError
from agentmuru.persistence.database import SQLiteDatabase
from agentmuru.persistence.schema import SCHEMA_VERSION


EXPECTED_TABLES = {
    "approvals",
    "artifacts",
    "event_counters",
    "events",
    "idempotency_keys",
    "messages",
    "runs",
    "schema_metadata",
    "sessions",
}


def test_database_initializes_versioned_schema_and_pragmas(tmp_path: Path) -> None:
    database = SQLiteDatabase(tmp_path / "state" / "agentmuru.db")
    connection = database.connect()
    try:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

        assert EXPECTED_TABLES <= tables
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
        assert connection.execute("SELECT version FROM schema_metadata").fetchone()[0] == 1
        assert SCHEMA_VERSION == 1
    finally:
        connection.close()


def test_database_rolls_back_failed_write(tmp_path: Path) -> None:
    database = SQLiteDatabase(tmp_path / "agentmuru.db")

    def fail_after_insert(connection: sqlite3.Connection) -> None:
        connection.execute(
            "INSERT INTO sessions(id, created_at, updated_at, metadata) VALUES (?, ?, ?, ?)",
            ("session-1", "2026-08-09T00:00:00+00:00", "2026-08-09T00:00:00+00:00", "{}"),
        )
        raise RuntimeError("stop")

    with pytest.raises(RuntimeError, match="stop"):
        database.write(fail_after_insert)

    connection = database.connect()
    try:
        assert connection.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0
    finally:
        connection.close()


def test_database_rejects_schema_from_a_newer_agentmuru(tmp_path: Path) -> None:
    path = tmp_path / "newer.db"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE schema_metadata(version INTEGER NOT NULL)")
        connection.execute("INSERT INTO schema_metadata VALUES (999)")

    with pytest.raises(StorageMigrationError) as exc_info:
        SQLiteDatabase(path)

    assert exc_info.value.code == "storage_migration"
    assert str(exc_info.value) == "Storage schema is newer than this AgentMuru version"


def test_database_classifies_invalid_file_as_corrupt(tmp_path: Path) -> None:
    path = tmp_path / "broken.db"
    path.write_bytes(b"this is not sqlite")

    with pytest.raises(StorageCorruptError) as exc_info:
        SQLiteDatabase(path)

    assert exc_info.value.code == "storage_corrupt"
    assert str(exc_info.value) == "Storage database is invalid"


def test_database_exhausts_bounded_retries_when_another_writer_holds_lock(
    tmp_path: Path,
) -> None:
    path = tmp_path / "busy.db"
    database = SQLiteDatabase(path, busy_timeout_ms=1, max_retries=1)
    blocker = database.connect()
    blocker.execute("BEGIN IMMEDIATE")
    try:
        with pytest.raises(StorageBusyError) as exc_info:
            database.write(lambda connection: connection.execute("UPDATE sessions SET title = ''"))
    finally:
        blocker.rollback()
        blocker.close()

    assert exc_info.value.code == "storage_busy"
    assert str(exc_info.value) == "Storage is busy"
