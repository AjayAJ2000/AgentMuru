from __future__ import annotations

import asyncio
from typing import Any, Mapping

from .models import ApprovalDecision, ApprovalRequest, ApprovalStatus
from .store import ApprovalStore, InMemoryApprovalStore


class ApprovalService:
    def __init__(self, store: ApprovalStore | None = None) -> None:
        self.store = store or InMemoryApprovalStore()
        self._waiters: dict[str, asyncio.Future[ApprovalRequest]] = {}
        self._changed = asyncio.Condition()

    async def create(
        self,
        *,
        session_id: str,
        run_id: str,
        tool_call_id: str,
        tool_name: str,
        arguments: Mapping[str, Any],
        permission: str | None,
        risk: str,
        timeout: float | None = None,
    ) -> ApprovalRequest:
        request = ApprovalRequest.with_timeout(
            session_id=session_id,
            run_id=run_id,
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            arguments=arguments,
            permission=permission,
            risk=risk,
            timeout=timeout,
        )
        self.store.create(request)
        self._waiters[request.id] = asyncio.get_running_loop().create_future()
        async with self._changed:
            self._changed.notify_all()
        return request

    def get(self, approval_id: str) -> ApprovalRequest:
        return self.store.get(approval_id)

    def list(self, *, session_id: str | None = None) -> list[ApprovalRequest]:
        return self.store.list(session_id=session_id)

    async def wait(self, approval_id: str) -> ApprovalRequest:
        request = self.get(approval_id)
        if request.status is not ApprovalStatus.PENDING:
            return request
        waiter = self._waiters.get(approval_id)
        if waiter is None:
            waiter = asyncio.get_running_loop().create_future()
            self._waiters[approval_id] = waiter
        if request.expires_at is None:
            return await waiter
        timeout = max(
            0.0,
            (request.expires_at - request.requested_at).total_seconds(),
        )
        try:
            return await asyncio.wait_for(asyncio.shield(waiter), timeout=timeout)
        except asyncio.TimeoutError:
            current = self.get(approval_id)
            expired = current.expire()
            self.store.save(expired)
            if not waiter.done():
                waiter.set_result(expired)
            async with self._changed:
                self._changed.notify_all()
            return expired

    async def wait_for_run(self, run_id: str) -> ApprovalRequest:
        while True:
            pending = next(
                (
                    item
                    for item in self.store.list()
                    if item.run_id == run_id and item.status is ApprovalStatus.PENDING
                ),
                None,
            )
            if pending is not None:
                return pending
            async with self._changed:
                await self._changed.wait()

    async def decide(
        self,
        approval_id: str,
        decision: ApprovalDecision,
        *,
        actor: str,
        reason: str | None = None,
    ) -> ApprovalRequest:
        decided = self.get(approval_id).decide(decision, actor=actor, reason=reason)
        self.store.save(decided)
        waiter = self._waiters.get(approval_id)
        if waiter is not None and not waiter.done():
            waiter.set_result(decided)
        async with self._changed:
            self._changed.notify_all()
        return decided
