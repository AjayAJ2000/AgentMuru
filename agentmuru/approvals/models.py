from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"


@dataclass(frozen=True, slots=True)
class ApprovalRequest:
    session_id: str
    run_id: str
    tool_call_id: str
    tool_name: str
    arguments: Mapping[str, Any]
    permission: str | None
    risk: str
    id: str = field(default_factory=lambda: str(uuid4()))
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None
    decided_at: datetime | None = None
    actor: str | None = None
    reason: str | None = None

    def decide(
        self,
        decision: ApprovalDecision,
        *,
        actor: str,
        reason: str | None = None,
    ) -> "ApprovalRequest":
        if self.status is not ApprovalStatus.PENDING:
            raise ValueError("Approval request has already been decided")
        status = (
            ApprovalStatus.APPROVED
            if decision is ApprovalDecision.APPROVE
            else ApprovalStatus.REJECTED
        )
        return replace(
            self,
            status=status,
            decided_at=datetime.now(timezone.utc),
            actor=actor,
            reason=reason,
        )

    def expire(self) -> "ApprovalRequest":
        if self.status is not ApprovalStatus.PENDING:
            return self
        return replace(
            self,
            status=ApprovalStatus.EXPIRED,
            decided_at=datetime.now(timezone.utc),
            reason="Approval deadline elapsed",
        )

    @classmethod
    def with_timeout(cls, *, timeout: float | None = None, **values: Any) -> "ApprovalRequest":
        requested_at = datetime.now(timezone.utc)
        return cls(
            **values,
            requested_at=requested_at,
            expires_at=requested_at + timedelta(seconds=timeout) if timeout is not None else None,
        )
