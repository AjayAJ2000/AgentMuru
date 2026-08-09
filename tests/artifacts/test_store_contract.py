from __future__ import annotations

import pytest

from agentmuru.artifacts import ArtifactKind, ArtifactStore, InMemoryArtifactStore
from agentmuru.core.errors import StorageSerializationError


def assert_artifact_store_contract(store: ArtifactStore, session_id: str) -> None:
    text = store.create(
        session_id=session_id,
        kind=ArtifactKind.MARKDOWN,
        name="report.md",
        content="# Report",
        mime_type="text/markdown",
        creator="analyst",
        metadata={"audience": "operator"},
    )
    binary = store.create(
        session_id=session_id,
        run_id="run-1",
        kind=ArtifactKind.FILE,
        name="data.bin",
        content=b"\x00\x01",
        mime_type="application/octet-stream",
        creator="analyst",
    )
    structured = store.create(
        session_id=session_id,
        kind=ArtifactKind.JSON,
        name="summary.json",
        content={"rows": [1, 2], "ready": True},
        mime_type="application/json",
        creator="analyst",
    )

    assert store.get(text.id).content == "# Report"
    assert store.get(text.id).metadata == {"audience": "operator"}
    assert store.get(binary.id).content == b"\x00\x01"
    assert store.get(binary.id).run_id == "run-1"
    assert store.get(structured.id).content == {"ready": True, "rows": [1, 2]}
    assert [item.id for item in store.list(session_id=session_id)] == [
        text.id,
        binary.id,
        structured.id,
    ]


def test_in_memory_artifact_store_satisfies_persistent_content_contract() -> None:
    assert_artifact_store_contract(InMemoryArtifactStore(), "session-1")


def test_in_memory_artifact_store_rejects_unsupported_content_before_insert() -> None:
    store = InMemoryArtifactStore()

    with pytest.raises(StorageSerializationError):
        store.create(
            session_id="session-1",
            kind=ArtifactKind.FILE,
            name="unsafe.bin",
            content=object(),
            mime_type="application/octet-stream",
            creator="analyst",
        )

    assert store.list(session_id="session-1") == []
