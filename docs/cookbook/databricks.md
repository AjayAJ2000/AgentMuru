# Check Databricks readiness

**Outcome:** inspect the optional SDK and host configuration without making a network call.

Module: `examples.databricks_agent`

```powershell
python examples/databricks_agent.py
```

Expected result always includes `network_attempted=false`, plus truthful booleans for the
SDK and `DATABRICKS_HOST`. Contract tests exercise identity-aware clients, catalog trees,
warehouse records, job triggers, SQL connection ownership, and identifier validation with
fakes. The clean-wheel gate installs and imports both Databricks optional modules.

That evidence is not a credential-backed workspace call. Live verification requires an
explicit environment, valid identity, and user authorization; the qualification report
records it separately.

Qualified by `tests/qualification/test_scenarios.py::test_databricks_scenario_is_safe_without_credentials_or_network`
and the integration contract tests.
