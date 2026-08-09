from __future__ import annotations

import sqlite3
import time
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from agentmuru.core.errors import (
    StorageBusyError,
    StorageCorruptError,
    StorageError,
    StorageMigrationError,
)

from .schema import MIGRATION_1, SCHEMA_VERSION

T = TypeVar("T")


def _is_busy(error: BaseException) -> bool:
    message = str(error).lower()
    return "locked" in message or "busy" in message


def _translate_database_error(error: sqlite3.DatabaseError) -> StorageError:
    if _is_busy(error):
        return StorageBusyError("Storage is busy")
    message = str(error).lower()
    if "not a database" in message or "malformed" in message:
        return StorageCorruptError("Storage database is invalid")
    return StorageError("Storage operation failed")


class SQLiteDatabase:
    def __init__(
        self,
        path: str | Path,
        *,
        busy_timeout_ms: int = 5000,
        max_retries: int = 4,
    ) -> None:
        if busy_timeout_ms < 0:
            raise ValueError("busy_timeout_ms cannot be negative")
        if max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        self.path = Path(path).expanduser().resolve()
        self.busy_timeout_ms = busy_timeout_ms
        self.max_retries = max_retries
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def connect(self) -> sqlite3.Connection:
        try:
            connection = sqlite3.connect(
                self.path,
                timeout=self.busy_timeout_ms / 1000,
                isolation_level=None,
                check_same_thread=False,
            )
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(f"PRAGMA busy_timeout = {self.busy_timeout_ms}")
            connection.execute("PRAGMA journal_mode = WAL")
            return connection
        except sqlite3.DatabaseError as exc:
            raise _translate_database_error(exc) from exc

    def write(
        self,
        operation: Callable[[sqlite3.Connection], T],
        *,
        immediate: bool = False,
    ) -> T:
        for attempt in range(self.max_retries + 1):
            connection: sqlite3.Connection | None = None
            try:
                connection = self.connect()
                connection.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
                value = operation(connection)
                connection.commit()
                return value
            except StorageBusyError:
                if attempt == self.max_retries:
                    raise
                time.sleep(0.025 * (2**attempt))
            except sqlite3.OperationalError as exc:
                if connection is not None:
                    connection.rollback()
                translated = _translate_database_error(exc)
                if isinstance(translated, StorageBusyError) and attempt < self.max_retries:
                    time.sleep(0.025 * (2**attempt))
                    continue
                raise translated from exc
            except sqlite3.DatabaseError as exc:
                if connection is not None:
                    connection.rollback()
                raise _translate_database_error(exc) from exc
            except Exception:
                if connection is not None:
                    connection.rollback()
                raise
            finally:
                if connection is not None:
                    connection.close()
        raise AssertionError("unreachable")

    def _initialize(self) -> None:
        connection = self.connect()
        try:
            metadata_exists = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'schema_metadata'"
            ).fetchone()
            if metadata_exists is None:
                connection.execute("BEGIN IMMEDIATE")
                try:
                    connection.execute(
                        "CREATE TABLE schema_metadata(version INTEGER NOT NULL)"
                    )
                    for statement in MIGRATION_1:
                        connection.execute(statement)
                    connection.execute(
                        "INSERT INTO schema_metadata(version) VALUES (?)",
                        (SCHEMA_VERSION,),
                    )
                    connection.commit()
                except Exception:
                    connection.rollback()
                    raise
                return

            row = connection.execute("SELECT version FROM schema_metadata").fetchone()
            if row is None:
                raise StorageCorruptError("Storage database is invalid")
            version = int(row[0])
            if version > SCHEMA_VERSION:
                raise StorageMigrationError(
                    "Storage schema is newer than this AgentMuru version"
                )
            if version < SCHEMA_VERSION:
                raise StorageMigrationError("Storage schema version is unsupported")
        except sqlite3.DatabaseError as exc:
            raise _translate_database_error(exc) from exc
        finally:
            connection.close()
