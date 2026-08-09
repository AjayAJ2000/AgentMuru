from __future__ import annotations

from pathlib import Path

from agentmuru.approvals import ApprovalService

from .approval_store import SQLiteApprovalStore
from .artifact_store import SQLiteArtifactStore
from .database import SQLiteDatabase
from .session_store import SQLiteSessionStore


class SQLitePersistence:
    """Compose AgentMuru's durable stores around one SQLite database file."""

    def __init__(
        self,
        path: str | Path,
        *,
        busy_timeout_ms: int = 5000,
        max_retries: int = 4,
        poll_interval: float = 0.05,
    ) -> None:
        self.database = SQLiteDatabase(
            path,
            busy_timeout_ms=busy_timeout_ms,
            max_retries=max_retries,
        )
        self.sessions = SQLiteSessionStore(
            self.database,
            poll_interval=poll_interval,
        )
        self.artifacts = SQLiteArtifactStore(self.database)
        self.approvals = SQLiteApprovalStore(self.database)

    def approval_service(self) -> ApprovalService:
        return ApprovalService(self.approvals)

