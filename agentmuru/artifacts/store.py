from __future__ import annotations

import json
from threading import RLock
from typing import Any, Mapping, Protocol

from agentmuru.core.errors import StorageSerializationError

from .models import Artifact, ArtifactKind


def validate_artifact_content(value: Any) -> None:
    if isinstance(value, (str, bytes)):
        return
    try:
        json.dumps(value, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise StorageSerializationError("Value cannot be stored safely") from exc


def _validated_metadata(value: Mapping[str, Any] | None) -> dict[str, Any]:
    metadata = dict(value or {})
    try:
        json.dumps(metadata, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise StorageSerializationError("Value cannot be stored safely") from exc
    return metadata


class ArtifactStore(Protocol):
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
    ) -> Artifact: ...

    def get(self, artifact_id: str) -> Artifact: ...

    def list(self, *, session_id: str) -> list[Artifact]: ...


class InMemoryArtifactStore:
    def __init__(self) -> None:
        self._artifacts: dict[str, Artifact] = {}
        self._lock = RLock()

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
        safe_metadata = _validated_metadata(metadata)
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
        with self._lock:
            self._artifacts[artifact.id] = artifact
        return artifact

    def get(self, artifact_id: str) -> Artifact:
        with self._lock:
            try:
                return self._artifacts[artifact_id]
            except KeyError as exc:
                raise KeyError(f"Artifact '{artifact_id}' was not found") from exc

    def list(self, *, session_id: str) -> list[Artifact]:
        with self._lock:
            return [item for item in self._artifacts.values() if item.session_id == session_id]
