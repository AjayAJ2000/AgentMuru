# Databricks

Install the optional integration:

```powershell
python -m pip install "agentmuru[databricks]"
```

Adapters live under `agentmuru.integrations.databricks`. User-scoped workspace and SQL
clients are operation-scoped and never cached across identities. Application-identity
connections can be reused behind a lock. Configure `DATABRICKS_HOST`,
`DATABRICKS_WAREHOUSE_ID`, and an approved OAuth or token credential source.
