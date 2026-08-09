from __future__ import annotations

from pathlib import Path

import pytest

from agentmuru.artifacts import ArtifactKind
from agentmuru.core.errors import StorageSerializationError
from agentmuru.persistence.artifact_store import SQLiteArtifactStore
from agentmuru.persistence.database import SQLiteDatabase
from agentmuru.persistence.session_store import SQLiteSessionStore
from tests.artifacts.test_store_contract import assert_artifact_store_contract


def test_sqlite_artifact_store_satisfies_contract_and_survives_reopen(
    tmp_path: Path,
) -> None:
    path = tmp_path / "agentmuru.db"
    database = SQLiteDatabase(path)
    session = SQLiteSessionStore(database).create()
    first = SQLiteArtifactStore(database)

    assert_artifact_store_contract(first, session.id)

    second = SQLiteArtifactStore(SQLiteDatabase(path))
    assert [artifact.name for artifact in second.list(session_id=session.id)] == [
        "report.md",
        "data.bin",
        "summary.json",
    ]


@pytest.mark.parametrize("kind", list(ArtifactKind))
def test_sqlite_artifact_store_round_trips_every_artifact_kind(
    tmp_path: Path,
    kind: ArtifactKind,
) -> None:
    database = SQLiteDatabase(tmp_path / f"{kind.value}.db")
    session = SQLiteSessionStore(database).create()
    store = SQLiteArtifactStore(database)

    artifact = store.create(
        session_id=session.id,
        kind=kind,
        name=f"sample.{kind.value}",
        content={"kind": kind.value},
        mime_type="application/json",
        creator="qualification",
    )

    assert store.get(artifact.id) == artifact


def test_sqlite_artifact_store_rejects_unsupported_content_before_insert(
    tmp_path: Path,
) -> None:
    database = SQLiteDatabase(tmp_path / "agentmuru.db")
    session = SQLiteSessionStore(database).create()
    store = SQLiteArtifactStore(database)

    with pytest.raises(StorageSerializationError):
        store.create(
            session_id=session.id,
            kind=ArtifactKind.FILE,
            name="unsafe.bin",
            content=object(),
            mime_type="application/octet-stream",
            creator="qualification",
        )

    assert store.list(session_id=session.id) == []
