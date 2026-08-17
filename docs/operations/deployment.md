# Deployment

The 0.3 MVP is a Python ASGI application with a bundled static Workspace. Start with one runtime
process and one SQLite file, then replace storage or tracing behind their protocols as the
operational workload grows.

## Build the application environment

Pin the AgentMuru minor line and one provider extra:

```text
agentmuru[openai]>=0.3,<0.4
```

Build an immutable environment, run `muru doctor`, import the application target, and exercise
`GET /health` before promotion.

## Run behind a proxy

```powershell
muru run app:application --host 0.0.0.0 --port 8000
```

Terminate TLS at a maintained reverse proxy or load balancer. Forward WebSocket upgrades for
`/api/v1/sessions/*/stream`. Keep health checks on `/health` and do not expose a database or
backup directory through static-file routing.

## Configure durable state

Place the SQLite database on durable low-latency storage. Use one active AgentMuru runtime
process per database file. Configure operating-system permissions, online backup, retention,
restore tests, and enough free space for WAL activity.

`storage_busy` means bounded lock retries were exhausted. Move to an application-owned external
store when the workload needs sustained concurrent writers, multi-tenancy, replication,
managed backup, point-in-time recovery, or independent scaling.

## Configure identity and limits

Disable anonymous access, install an `AuthProvider`, set trusted hosts and exact HTTP and
WebSocket origins, then enforce authentication and session ownership. Align message, proxy, and
request-body limits.

## Manage provider credentials

Inject `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GOOGLE_API_KEY` through the deployment secret
system. Do not bake credentials into the image, generated starter, or application metadata.

## Release and rollback

Before deployment, test:

1. clean wheel installation and `muru doctor`;
2. session create, message submit, event stream, and cancellation;
3. approval grant, rejection, and expiry;
4. database backup and restore;
5. process loss with active work and `process_interrupted` recovery;
6. a real provider request in a restricted staging account.

Rollback the application and database schema together. AgentMuru refuses to open a database with
a schema newer than the installed package.
