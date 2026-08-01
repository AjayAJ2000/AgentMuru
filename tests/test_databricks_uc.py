import sys
from types import SimpleNamespace

import pytest

from brickflowui.databricks import services, uc
from brickflowui.databricks.uc import _quote_identifier, _validated_limit


def test_quote_identifier_escapes_backticks():
    assert _quote_identifier("catalog`name") == "`catalog``name`"


def test_quote_identifier_rejects_empty_values():
    with pytest.raises(ValueError):
        _quote_identifier("")


def test_validated_limit_rejects_non_positive_values():
    with pytest.raises(ValueError):
        _validated_limit(0)


def test_unity_catalog_uses_identity_aware_workspace_client(monkeypatch):
    sentinel = object()
    legacy_client = object()
    monkeypatch.setattr(services, "workspace_client", lambda: sentinel)
    monkeypatch.setitem(
        sys.modules,
        "databricks.sdk",
        SimpleNamespace(WorkspaceClient=lambda: legacy_client),
    )

    assert uc._workspace_client() is sentinel
