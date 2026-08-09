from __future__ import annotations

import json
from threading import RLock
from typing import Protocol

from agentmuru.core.errors import StorageSerializationError

from .models import ApprovalRequest


def validate_approval_arguments(request: ApprovalRequest) -> None:
    try:
        json.dumps(request.arguments, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise StorageSerializationError("Value cannot be stored safely") from exc


class ApprovalStore(Protocol):
    def create(self, request: ApprovalRequest) -> ApprovalRequest: ...

    def get(self, approval_id: str) -> ApprovalRequest: ...

    def list(self, *, session_id: str | None = None) -> list[ApprovalRequest]: ...

    def save(self, request: ApprovalRequest) -> ApprovalRequest: ...


class InMemoryApprovalStore:
    def __init__(self) -> None:
        self._requests: dict[str, ApprovalRequest] = {}
        self._lock = RLock()

    def create(self, request: ApprovalRequest) -> ApprovalRequest:
        validate_approval_arguments(request)
        with self._lock:
            self._requests[request.id] = request
        return request

    def get(self, approval_id: str) -> ApprovalRequest:
        with self._lock:
            try:
                return self._requests[approval_id]
            except KeyError as exc:
                raise KeyError(f"Approval '{approval_id}' was not found") from exc

    def list(self, *, session_id: str | None = None) -> list[ApprovalRequest]:
        with self._lock:
            requests = list(self._requests.values())
        if session_id is not None:
            requests = [item for item in requests if item.session_id == session_id]
        return requests

    def save(self, request: ApprovalRequest) -> ApprovalRequest:
        validate_approval_arguments(request)
        with self._lock:
            if request.id not in self._requests:
                raise KeyError(f"Approval '{request.id}' was not found")
            self._requests[request.id] = request
        return request

