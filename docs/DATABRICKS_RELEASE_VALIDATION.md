# Databricks Release Validation

Use this procedure after deploying the exact candidate artifact to a
non-production Databricks App. Local tests cannot prove workspace OAuth,
Unity Catalog grants, SQL warehouse permissions, Jobs permissions, or managed
platform routing.

## Prerequisites

Configure two Databricks CLI profiles for two different people:

- profile A can read the chosen catalog, warehouse, and job;
- profile B represents a lower-privilege user and differs on at least one of
  those resources;
- both profiles target the workspace that hosts the candidate app.

Install the repository development dependencies, which include the Databricks
SDK. Do not put tokens in the command, source tree, or output path.

## Collect read-only evidence

```bash
python scripts/validate_databricks_workspace.py \
  --app-url "https://your-app-host.example" \
  --profile-a release-owner \
  --profile-b release-viewer \
  --catalog main \
  --warehouse-id 0123456789abcdef \
  --job-id 12345 \
  --output .tmp/databricks-release-evidence.json
```

The harness performs only these operations:

- resolves the current user for each profile;
- reads catalog, warehouse, and job metadata;
- sends one authenticated `GET` to the app root with profile A;
- writes a sanitized JSON report after collection finishes.

It does not deploy the app, run a job, execute SQL, change permissions, or
mutate any workspace resource. Error messages in evidence contain exception
type names only. The app URL is reduced to its origin, and authentication
headers and tokens are never serialized.

A successful report has an empty `validation_errors` list, two different
`subject` values, full resource access for profile A, at least one differing
resource result for profile B, and `app_root.reachable: true`.

## Manual operator checks

The harness intentionally does not perform state-changing validation. A
workspace operator must separately confirm, using designated test resources:

1. Open the deployed app as each user at the same time and confirm state and
   visible data remain isolated.
2. Run one harmless, bounded SQL query through the app and confirm its result
   and audit identity.
3. Trigger a designated non-production job through the app, confirm the run
   identity and outcome, and cancel it if it exceeds the agreed deadline.
4. Revoke one expected permission from profile B's user or group, verify the
   app shows a safe authorization error, then restore the original grant.
5. Leave and return to the app long enough to exercise managed routing and a
   WebSocket reconnect.

These actions require explicit operator approval because they can consume
compute, start jobs, or alter workspace grants.

## Cleanup

Remove the local JSON evidence when it is no longer needed, or store it in the
approved release-evidence system. Stop any test job run and restore any grant
changed during manual checks. The harness itself creates no remote resources,
so it requires no remote cleanup.
