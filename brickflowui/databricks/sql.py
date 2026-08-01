"""
Databricks SQL Connector helpers for BrickflowUI.

Provides a simple interface to execute SQL queries against a Databricks SQL warehouse,
using environment variables set by Databricks Apps or local .env files.
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from importlib import import_module
from threading import RLock
from typing import Any, Dict, Iterator, List, Optional
from urllib.parse import urlparse

from ..auth import Principal, current_principal

logger = logging.getLogger("brickflowui.databricks.sql")

_app_connection = None
_app_connection_lock = RLock()


def _normalized_host(value: str) -> str:
    """Return a Databricks server hostname without stripping hostname characters."""
    raw = value.strip()
    if not raw:
        return ""
    parsed = urlparse(raw if "://" in raw else f"//{raw}")
    return (parsed.netloc or parsed.path).rstrip("/")


def _connect(*, principal: Optional[Principal] = None):
    """Create a connector connection for one normalized identity."""
    try:
        db_sql = import_module("databricks.sql")
    except ImportError:
        raise ImportError(
            "databricks-sql-connector is required for SQL integration. "
            "Install it with: pip install brickflowui[databricks]"
        )

    host = _normalized_host(os.getenv("DATABRICKS_HOST", ""))
    token = (
        principal.access_token
        if principal and principal.principal_type == "user"
        else os.getenv("DATABRICKS_TOKEN") or os.getenv("DATABRICKS_OAUTH_TOKEN")
    )
    http_path = os.getenv("DATABRICKS_WAREHOUSE_ID")

    if not host:
        raise ValueError("DATABRICKS_HOST environment variable is not set.")
    if not http_path:
        raise ValueError("DATABRICKS_WAREHOUSE_ID environment variable is not set.")

    # Normalize http_path: if it's just a warehouse ID, build the path
    if not http_path.startswith("/sql/"):
        http_path = f"/sql/1.0/warehouses/{http_path}"

    connect_args: Dict[str, Any] = {
        "server_hostname": host,
        "http_path": http_path,
    }

    if principal and principal.principal_type == "user" and not token:
        raise ValueError("User authorization requires a forwarded Databricks access token.")

    if token:
        connect_args["access_token"] = token
    else:
        # Try Databricks SDK auth (OAuth, instance profiles, etc.)
        try:
            from databricks.sdk import WorkspaceClient
            w = WorkspaceClient()
            connect_args["credentials_provider"] = lambda: w.config.authenticate
        except Exception:
            raise ValueError(
                "No authentication found. Set DATABRICKS_TOKEN or configure Databricks SDK auth."
            )

    logger.info(f"Connecting to Databricks SQL warehouse at {host}")
    return db_sql.connect(**connect_args)


def _healthy_app_connection(principal: Principal):
    """Return the guarded app connection, replacing it when its health check fails."""
    global _app_connection

    if _app_connection is not None:
        try:
            with _app_connection.cursor() as cur:
                cur.execute("SELECT 1")
            return _app_connection
        except Exception:
            try:
                _app_connection.close()
            except Exception:
                pass
            _app_connection = None

    _app_connection = _connect(principal=principal)
    return _app_connection


@contextmanager
def connection(identity: Optional[Principal] = None) -> Iterator[Any]:
    """Acquire a connection without allowing user identities to cross operation boundaries."""
    principal = identity or current_principal()
    if principal.principal_type == "user":
        conn = _connect(principal=principal)
        try:
            yield conn
        finally:
            conn.close()
        return

    with _app_connection_lock:
        yield _healthy_app_connection(principal)


def close_app_connection() -> None:
    """Close the cached app-identity connection, if one exists."""
    global _app_connection
    with _app_connection_lock:
        if _app_connection is not None:
            try:
                _app_connection.close()
            finally:
                _app_connection = None


def query(sql: str, params: Optional[List[Any]] = None) -> "Any":
    """
    Execute a SQL query and return results as a pandas DataFrame.

    Example:
        df = query("SELECT * FROM catalog.schema.table LIMIT 100")
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("pandas is required. Install with: pip install brickflowui[databricks]")

    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, parameters=params)
            results = cur.fetchall()
            columns = [desc[0] for desc in cur.description] if cur.description else []
            return pd.DataFrame(results, columns=columns)


def execute(sql: str, params: Optional[List[Any]] = None) -> None:
    """
    Execute a non-returning SQL statement (INSERT, UPDATE, DELETE, etc.)

    Example:
        execute("UPDATE catalog.schema.table SET status = ? WHERE id = ?", ["active", 42])
    """
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, parameters=params)


def query_to_records(sql: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
    """
    Execute a SQL query and return results as a list of dicts (for Table component).

    Example:
        rows = query_to_records("SELECT id, name, status FROM my_table LIMIT 50")
        return db.Table(data=rows)
    """
    df = query(sql, params)
    return df.to_dict(orient="records")


@contextmanager
def transaction():
    """Context manager for a SQL transaction (commit on success, rollback on error)."""
    with connection() as conn:
        try:
            yield conn
            with conn.cursor() as cur:
                cur.execute("COMMIT")
        except Exception:
            try:
                with conn.cursor() as cur:
                    cur.execute("ROLLBACK")
            except Exception:
                pass
            raise
