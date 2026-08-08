"""
Databricks environment helpers.

Reads DATABRICKS_* environment variables injected by Databricks Apps runtime
and provides sensible local-development fallbacks via python-dotenv.
"""

from __future__ import annotations

import os
from typing import Optional, Tuple

# Load .env file if present (local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def resolve_host_port(
    host: Optional[str] = None,
    port: Optional[int] = None,
) -> Tuple[str, int]:
    """
    Resolve the server bind address.
    - host defaults to 0.0.0.0 (Databricks Apps requires this)
    - port: uses DATABRICKS_APP_PORT if set, else 8050 for local dev
    """
    if host is None:
        host = "0.0.0.0"
    if port is None:
        env_port = os.getenv("DATABRICKS_APP_PORT")
        port = int(env_port) if env_port else 8050
    return host, port


def workspace_host() -> Optional[str]:
    """Returns the Databricks workspace URL (e.g. https://adb-123.azuredatabricks.net)."""
    return os.getenv("DATABRICKS_HOST")


def app_name() -> Optional[str]:
    """Returns the Databricks App name as set in the workspace."""
    return os.getenv("DATABRICKS_APP_NAME")


def warehouse_id() -> Optional[str]:
    """Returns the SQL warehouse ID from environment."""
    return os.getenv("DATABRICKS_WAREHOUSE_ID")


def volume_uri() -> Optional[str]:
    """Returns the Unity Catalog volume URI for file storage."""
    return os.getenv("DATABRICKS_VOLUME_URI")


def databricks_token() -> Optional[str]:
    """Returns the Databricks Personal Access Token or OAuth token."""
    return os.getenv("DATABRICKS_TOKEN")


def is_databricks_runtime() -> bool:
    """True if running inside a Databricks Apps container."""
    return bool(os.getenv("DATABRICKS_APP_PORT") or os.getenv("DATABRICKS_APP_NAME"))


def runtime_summary() -> dict:
    """Returns a dict of all resolved Databricks env vars for debugging."""
    return {
        "host": workspace_host(),
        "app_name": app_name(),
        "warehouse_id": warehouse_id(),
        "volume_uri": volume_uri(),
        "is_databricks_runtime": is_databricks_runtime(),
        "app_port": os.getenv("DATABRICKS_APP_PORT"),
    }
