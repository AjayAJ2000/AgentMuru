"""
Unity Catalog helpers for BrickflowUI.

Provides functions to list catalogs, schemas, and tables using
the Databricks SDK or SQL queries as fallback.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger("brickflowui.databricks.uc")


def _quote_identifier(value: str) -> str:
    """Safely quote Spark SQL identifiers used in fallback SQL statements."""
    if not value or "\x00" in value:
        raise ValueError("Identifier must be a non-empty string.")
    escaped = value.replace("`", "``")
    return f"`{escaped}`"


def _validated_limit(limit: int) -> int:
    if limit <= 0:
        raise ValueError("limit must be greater than 0.")
    return limit


def _workspace_client():
    """Get a workspace client bound to the current BrickflowUI identity."""
    from . import services

    return services.workspace_client()


def list_catalogs() -> List[str]:
    """List all accessible Unity Catalog catalogs."""
    try:
        w = _workspace_client()
        return [c.name for c in w.catalogs.list() if c.name]
    except Exception as e:
        logger.warning(f"Unity Catalog SDK failed, trying SQL fallback: {e}")
        from .sql import query_to_records
        rows = query_to_records("SHOW CATALOGS")
        return [r.get("catalog", r.get("catalog_name", "")) for r in rows]


def list_schemas(catalog: str) -> List[str]:
    """List all schemas in a catalog."""
    try:
        w = _workspace_client()
        return [s.name for s in w.schemas.list(catalog_name=catalog) if s.name]
    except Exception as e:
        logger.warning(f"Unity Catalog SDK failed, trying SQL fallback: {e}")
        from .sql import query_to_records
        rows = query_to_records(f"SHOW SCHEMAS IN {_quote_identifier(catalog)}")
        return [r.get("databaseName", r.get("schema_name", "")) for r in rows]


def list_tables(catalog: str, schema: str) -> List[Dict[str, Any]]:
    """List all tables in a catalog.schema."""
    try:
        w = _workspace_client()
        tables = w.tables.list(catalog_name=catalog, schema_name=schema)
        return [
            {
                "name": t.name,
                "full_name": t.full_name,
                "table_type": str(t.table_type.value) if t.table_type else "UNKNOWN",
                "comment": t.comment or "",
            }
            for t in tables
            if t.name
        ]
    except Exception as e:
        logger.warning(f"Unity Catalog SDK failed, trying SQL fallback: {e}")
        from .sql import query_to_records
        rows = query_to_records(
            f"SHOW TABLES IN {_quote_identifier(catalog)}.{_quote_identifier(schema)}"
        )
        return [
            {
                "name": r.get("tableName", r.get("table_name", "")),
                "full_name": f"{catalog}.{schema}.{r.get('tableName', '')}",
                "table_type": r.get("isTemporary", "false") == "true" and "TEMP" or "TABLE",
                "comment": "",
            }
            for r in rows
        ]


def table_schema(catalog: str, schema: str, table: str) -> List[Dict[str, Any]]:
    """Return column definitions for a table."""
    try:
        w = _workspace_client()
        t = w.tables.get(f"{catalog}.{schema}.{table}")
        if t.columns:
            return [
                {
                    "name": col.name,
                    "type": str(col.type_name.value) if col.type_name else "STRING",
                    "nullable": col.nullable,
                    "comment": col.comment or "",
                }
                for col in t.columns
            ]
    except Exception as e:
        logger.warning(f"Unity Catalog SDK failed, trying SQL fallback: {e}")

    from .sql import query_to_records
    rows = query_to_records(
        "DESCRIBE TABLE "
        f"{_quote_identifier(catalog)}.{_quote_identifier(schema)}.{_quote_identifier(table)}"
    )
    return [
        {
            "name": r.get("col_name", ""),
            "type": r.get("data_type", "STRING"),
            "nullable": True,
            "comment": r.get("comment", ""),
        }
        for r in rows
        if r.get("col_name") and not r.get("col_name", "").startswith("#")
    ]


def get_table(
    catalog: str,
    schema: str,
    table: str,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Read rows from a Unity Catalog table."""
    from .sql import query_to_records
    safe_limit = _validated_limit(limit)
    return query_to_records(
        "SELECT * FROM "
        f"{_quote_identifier(catalog)}.{_quote_identifier(schema)}.{_quote_identifier(table)} "
        f"LIMIT {safe_limit}"
    )
