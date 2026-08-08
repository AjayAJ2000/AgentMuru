from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4


class ArtifactKind(str, Enum):
    MARKDOWN = "markdown"
    CODE = "code"
    JSON = "json"
    TABLE = "table"
    CHART = "chart"
    FILE = "file"
    IMAGE = "image"
    SQL = "sql"
    REPORT = "report"


@dataclass(frozen=True, slots=True)
class Artifact:
    session_id: str
    kind: ArtifactKind
    name: str
    content: Any
    mime_type: str
    creator: str
    id: str = field(default_factory=lambda: str(uuid4()))
    run_id: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
