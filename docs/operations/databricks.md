# Databricks

Databricks support is optional and outside the core dependency direction.

```powershell
python -m pip install "agentmuru[databricks]>=0.3,<0.4"
```

The executable readiness scenario is `examples.databricks_agent`:

```powershell
python examples/databricks_agent.py
```

It checks package and environment readiness without attempting the network.

## Environment

Configure the values used by the integration path:

- `DATABRICKS_HOST`
- `DATABRICKS_WAREHOUSE_ID`
- `DATABRICKS_TOKEN` or an approved Databricks SDK credential source
- `DATABRICKS_VOLUME_URI` when the application uses a Unity Catalog volume
- `DATABRICKS_APP_PORT` and `DATABRICKS_APP_NAME` inside Databricks Apps

## Identity handling

`workspace_client()` binds a client to the current operation identity. A user principal requires
a forwarded Databricks access token and creates an operation-scoped client. User-scoped clients
are never cached across identities.

Application identities can use SDK credential discovery. SQL connections for an application
identity may be reused behind a lock after a health check. User SQL connections are created and
closed per operation.

## Available helpers

Workspace service helpers list warehouses, build a serializable catalog tree, and trigger a job.
SQL helpers query records, execute statements, and manage transactions. Unity Catalog helpers
list catalogs, schemas, tables, schemas, and bounded table rows.

Pass SQL values as parameters. Catalog, schema, and table helpers quote identifiers, but dynamic
identity and authorization decisions still belong to the application.

## Qualification boundary

Offline tests validate identity isolation, input validation, serialization, SQL parameter
handling, and missing-configuration failures with fake clients. A deployment must separately
qualify credential-backed calls against its workspace, warehouse, Unity Catalog permissions,
network policy, and audit requirements.
