import pytest
from concurrent.futures import ThreadPoolExecutor
from threading import Event

from brickflowui.auth import Principal
from brickflowui.databricks import sql
from brickflowui.databricks.sql import _normalized_host


class FakeCursor:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, statement, parameters=None):
        return None


class FakeConnection:
    def __init__(self, name):
        self.name = name
        self.closed = False

    def cursor(self):
        return FakeCursor()

    def close(self):
        self.closed = True


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://test.cloud.databricks.com", "test.cloud.databricks.com"),
        ("http://example.databricks.com/", "example.databricks.com"),
        ("workspace.databricks.com", "workspace.databricks.com"),
    ],
)
def test_normalized_host_removes_only_the_url_scheme(raw, expected):
    assert _normalized_host(raw) == expected


def test_user_connection_is_operation_scoped_and_never_reused(monkeypatch):
    created = []

    def fake_connect(*, principal=None):
        connection = FakeConnection(f"user-{len(created)}")
        created.append((principal, connection))
        return connection

    monkeypatch.setattr(sql, "_connect", fake_connect, raising=False)
    user = Principal(
        subject="alice",
        principal_type="user",
        authenticated=True,
        access_token="secret-user-token",
    )

    with sql.connection(user) as first:
        assert first.name == "user-0"
        assert not first.closed
    with sql.connection(user) as second:
        assert second.name == "user-1"

    assert first.closed
    assert second.closed
    assert [principal for principal, _ in created] == [user, user]


def test_app_connection_is_reused_and_guarded_by_provider(monkeypatch):
    created = []

    def fake_connect(*, principal=None):
        connection = FakeConnection(f"app-{len(created)}")
        created.append((principal, connection))
        return connection

    monkeypatch.setattr(sql, "_connect", fake_connect, raising=False)
    monkeypatch.setattr(sql, "_app_connection", None, raising=False)
    app_principal = Principal(subject="app", principal_type="app", authenticated=True)

    with sql.connection(app_principal) as first:
        assert first.name == "app-0"
    with sql.connection(app_principal) as second:
        assert second is first

    assert len(created) == 1
    assert not first.closed


def test_app_connection_serializes_concurrent_operations(monkeypatch):
    shared = FakeConnection("app")
    first_entered = Event()
    second_entered = Event()
    release_first = Event()
    monkeypatch.setattr(sql, "_connect", lambda *, principal=None: shared)
    monkeypatch.setattr(sql, "_app_connection", None)
    principal = Principal(subject="app", principal_type="app", authenticated=True)

    def first_operation():
        with sql.connection(principal):
            first_entered.set()
            release_first.wait(timeout=2)

    def second_operation():
        with sql.connection(principal):
            second_entered.set()

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(first_operation)
        assert first_entered.wait(timeout=1)
        second = executor.submit(second_operation)
        assert not second_entered.wait(timeout=0.1)
        release_first.set()
        first.result(timeout=1)
        second.result(timeout=1)

    assert second_entered.is_set()
