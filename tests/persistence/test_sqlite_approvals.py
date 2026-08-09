from __future__ import annotations

import pytest

from agentmuru.approvals import ApprovalRequest
from agentmuru.core.errors import StorageSerializationError
from agentmuru.persistence import SQLiteApprovalStore, SQLiteDatabase, SQLiteSessionStore

from tests.approvals.test_store_contract import assert_approval_store_contract


def _store(tmp_path):
    database = SQLiteDatabase(tmp_path / "agentmuru.db")
    sessions = SQLiteSessionStore(database)
    session = sessions.create()
    return SQLiteApprovalStore(database), session.id


def test_sqlite_approval_store_contract_and_reopen(tmp_path) -> None:
    database_path = tmp_path / "agentmuru.db"

    def factory():
        database = SQLiteDatabase(database_path)
        sessions = SQLiteSessionStore(database)
        session = sessions.create()
        return SQLiteApprovalStore(database), session.id

    store, session_id = factory()
    assert_approval_store_contract(lambda: (store, session_id))

    reopened = SQLiteApprovalStore(SQLiteDatabase(database_path))
    approval = reopened.list(session_id=session_id)[0]
    assert approval.arguments["record"] == {"name": "Muru"}
    assert approval.actor == "reviewer@example.com"


def test_sqlite_approval_store_rejects_unsafe_arguments_atomically(tmp_path) -> None:
    store, session_id = _store(tmp_path)
    request = ApprovalRequest(
        session_id=session_id,
        run_id="run-1",
        tool_call_id="call-1",
        tool_name="unsafe",
        arguments={"value": float("nan")},
        permission=None,
        risk="low",
    )

    with pytest.raises(StorageSerializationError):
        store.create(request)

    assert store.list(session_id=session_id) == []

