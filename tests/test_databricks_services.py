from types import SimpleNamespace

from brickflowui.auth import Principal, reset_current_principal, set_current_principal
from brickflowui.databricks.services import (
    catalog_tree,
    list_warehouses,
    trigger_job,
    workspace_client,
)


class FakeWorkspaceClient:
    def __init__(self):
        self.warehouses = SimpleNamespace(
            list=lambda: [
                SimpleNamespace(id="w1", name="Starter", state=SimpleNamespace(value="RUNNING")),
                SimpleNamespace(id="w2", name=None, state=None),
            ]
        )
        self.catalogs = SimpleNamespace(
            list=lambda: [SimpleNamespace(name="main"), SimpleNamespace(name=None)]
        )
        self.schemas = SimpleNamespace(
            list=lambda catalog_name: [
                SimpleNamespace(name="default", catalog_name=catalog_name),
            ]
        )
        self.tables = SimpleNamespace(
            list=lambda catalog_name, schema_name: [
                SimpleNamespace(
                    name="events",
                    full_name=f"{catalog_name}.{schema_name}.events",
                    table_type=SimpleNamespace(value="MANAGED"),
                    comment="Event stream",
                )
            ]
        )
        self.jobs = SimpleNamespace(
            run_now=lambda **kwargs: SimpleNamespace(response=SimpleNamespace(run_id=99))
        )


def test_list_warehouses_returns_stable_serializable_records():
    assert list_warehouses(client=FakeWorkspaceClient()) == [
        {"id": "w1", "name": "Starter", "state": "RUNNING"},
        {"id": "w2", "name": "w2", "state": "UNKNOWN"},
    ]


def test_catalog_tree_returns_nested_serializable_records():
    assert catalog_tree(client=FakeWorkspaceClient()) == [
        {
            "name": "main",
            "schemas": [
                {
                    "name": "default",
                    "tables": [
                        {
                            "name": "events",
                            "full_name": "main.default.events",
                            "table_type": "MANAGED",
                            "comment": "Event stream",
                        }
                    ],
                }
            ],
        }
    ]


def test_trigger_job_returns_stable_run_record_and_forwards_parameters():
    client = FakeWorkspaceClient()
    calls = []
    client.jobs.run_now = lambda **kwargs: (
        calls.append(kwargs) or SimpleNamespace(response=SimpleNamespace(run_id=99))
    )

    result = trigger_job("42", parameters={"environment": "prod"}, client=client)

    assert result == {"job_id": "42", "run_id": "99", "status": "QUEUED"}
    assert calls == [{"job_id": 42, "job_parameters": {"environment": "prod"}}]


def test_trigger_job_rejects_empty_or_non_numeric_job_ids():
    client = FakeWorkspaceClient()

    for invalid in ("", "abc", "-1"):
        try:
            trigger_job(invalid, client=client)
        except ValueError as exc:
            assert "positive integer" in str(exc)
        else:
            raise AssertionError(f"Expected {invalid!r} to be rejected")


def test_workspace_client_uses_current_user_token_without_caching(monkeypatch):
    monkeypatch.setenv("DATABRICKS_HOST", "https://workspace.databricks.com")
    calls = []
    factory = lambda **kwargs: calls.append(kwargs) or object()
    principal = Principal(
        subject="alice",
        principal_type="user",
        authenticated=True,
        access_token="secret-user-token",
    )
    token = set_current_principal(principal)
    try:
        first = workspace_client(client_factory=factory)
        second = workspace_client(client_factory=factory)
    finally:
        reset_current_principal(token)

    assert first is not second
    assert calls == [
        {"host": "https://workspace.databricks.com", "token": "secret-user-token"},
        {"host": "https://workspace.databricks.com", "token": "secret-user-token"},
    ]
