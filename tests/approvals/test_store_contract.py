from __future__ import annotations

from collections.abc import Callable

import pytest

from agentmuru.approvals import (
    ApprovalDecision,
    ApprovalRequest,
    ApprovalService,
    ApprovalStatus,
    ApprovalStore,
    InMemoryApprovalStore,
)
from agentmuru.core.errors import StorageSerializationError


StoreFactory = Callable[[], tuple[ApprovalStore, str]]


def assert_approval_store_contract(factory: StoreFactory) -> None:
    store, session_id = factory()
    pending = ApprovalRequest.with_timeout(
        session_id=session_id,
        run_id="run-1",
        tool_call_id="call-1",
        tool_name="write_record",
        arguments={"record": {"name": "Muru"}, "attempt": 1},
        permission="database.write",
        risk="high",
        timeout=30,
    )

    assert store.create(pending) == pending
    assert store.get(pending.id) == pending
    assert store.list(session_id=session_id) == [pending]

    decided = pending.decide(
        ApprovalDecision.APPROVE,
        actor="reviewer@example.com",
        reason="validated",
    )
    assert store.save(decided) == decided
    reloaded = store.get(pending.id)
    assert reloaded.status is ApprovalStatus.APPROVED
    assert reloaded.actor == "reviewer@example.com"
    assert reloaded.reason == "validated"
    assert reloaded.arguments == {"record": {"name": "Muru"}, "attempt": 1}


def test_in_memory_approval_store_contract() -> None:
    assert_approval_store_contract(lambda: (InMemoryApprovalStore(), "session-1"))


def test_in_memory_store_rejects_unsafe_arguments_without_inserting() -> None:
    store = InMemoryApprovalStore()
    request = ApprovalRequest(
        session_id="session-1",
        run_id="run-1",
        tool_call_id="call-1",
        tool_name="unsafe",
        arguments={"value": object()},
        permission=None,
        risk="low",
    )

    with pytest.raises(StorageSerializationError):
        store.create(request)

    assert store.list() == []


@pytest.mark.asyncio
async def test_approval_service_delegates_audit_records_to_store() -> None:
    store = InMemoryApprovalStore()
    service = ApprovalService(store)

    request = await service.create(
        session_id="session-1",
        run_id="run-1",
        tool_call_id="call-1",
        tool_name="deploy",
        arguments={"environment": "preview"},
        permission="deploy.write",
        risk="high",
    )
    decided = await service.decide(
        request.id,
        ApprovalDecision.REJECT,
        actor="release-manager",
        reason="missing evidence",
    )

    assert store.get(request.id) == decided
    assert decided.status is ApprovalStatus.REJECTED

