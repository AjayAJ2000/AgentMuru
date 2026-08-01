"""Identity-aware Databricks service adapters that return serializable records."""

from __future__ import annotations

import os
from typing import Any, Callable, Dict, List, Optional

from ..auth import Principal, current_principal


def _enum_value(value: Any, default: str = "UNKNOWN") -> str:
    if value is None:
        return default
    normalized = getattr(value, "value", value)
    return str(normalized) if normalized is not None else default


def workspace_client(
    *,
    identity: Optional[Principal] = None,
    client_factory: Optional[Callable[..., Any]] = None,
) -> Any:
    """Create a workspace client for the current operation's identity."""
    if client_factory is None:
        try:
            from databricks.sdk import WorkspaceClient
        except ImportError as exc:
            raise ImportError(
                "databricks-sdk is required for Databricks services. "
                "Install it with: pip install brickflowui[databricks]"
            ) from exc
        client_factory = WorkspaceClient

    principal = identity or current_principal()
    if principal.principal_type != "user":
        return client_factory()

    if not principal.access_token:
        raise ValueError("User authorization requires a forwarded Databricks access token.")
    host = os.getenv("DATABRICKS_HOST")
    if not host:
        raise ValueError("DATABRICKS_HOST environment variable is not set.")
    return client_factory(host=host, token=principal.access_token)


def list_warehouses(*, client: Any = None) -> List[Dict[str, str]]:
    """List warehouses as small stable records suitable for component props."""
    workspace = client or workspace_client()
    records: List[Dict[str, str]] = []
    for warehouse in workspace.warehouses.list():
        warehouse_id = getattr(warehouse, "id", None)
        if warehouse_id is None:
            continue
        normalized_id = str(warehouse_id)
        records.append(
            {
                "id": normalized_id,
                "name": getattr(warehouse, "name", None) or normalized_id,
                "state": _enum_value(getattr(warehouse, "state", None)),
            }
        )
    return records


def catalog_tree(*, client: Any = None) -> List[Dict[str, Any]]:
    """Return the accessible catalog hierarchy as plain serializable records."""
    workspace = client or workspace_client()
    catalogs: List[Dict[str, Any]] = []
    for catalog in workspace.catalogs.list():
        catalog_name = getattr(catalog, "name", None)
        if not catalog_name:
            continue
        schemas: List[Dict[str, Any]] = []
        for schema in workspace.schemas.list(catalog_name=catalog_name):
            schema_name = getattr(schema, "name", None)
            if not schema_name:
                continue
            tables: List[Dict[str, str]] = []
            for table in workspace.tables.list(
                catalog_name=catalog_name,
                schema_name=schema_name,
            ):
                table_name = getattr(table, "name", None)
                if not table_name:
                    continue
                tables.append(
                    {
                        "name": table_name,
                        "full_name": getattr(table, "full_name", None)
                        or f"{catalog_name}.{schema_name}.{table_name}",
                        "table_type": _enum_value(getattr(table, "table_type", None)),
                        "comment": getattr(table, "comment", None) or "",
                    }
                )
            schemas.append({"name": schema_name, "tables": tables})
        catalogs.append({"name": catalog_name, "schemas": schemas})
    return catalogs


def trigger_job(
    job_id: str,
    parameters: Optional[Dict[str, str]] = None,
    *,
    client: Any = None,
) -> Dict[str, str]:
    """Start a job run and return an immediately serializable queued-run record."""
    try:
        normalized_job_id = int(str(job_id))
    except (TypeError, ValueError) as exc:
        raise ValueError("job_id must be a positive integer.") from exc
    if normalized_job_id <= 0:
        raise ValueError("job_id must be a positive integer.")

    workspace = client or workspace_client()
    kwargs: Dict[str, Any] = {"job_id": normalized_job_id}
    if parameters:
        kwargs["job_parameters"] = dict(parameters)
    waiter = workspace.jobs.run_now(**kwargs)
    response = getattr(waiter, "response", waiter)
    run_id = getattr(response, "run_id", None)
    if run_id is None:
        raise RuntimeError("Databricks did not return a run identifier.")
    return {
        "job_id": str(normalized_job_id),
        "run_id": str(run_id),
        "status": "QUEUED",
    }
