# Deployment checklist

AgentMuru 0.2 is qualified for one Runtime process per SQLite file and modest concurrency.

1. Install the exact wheel and run `muru doctor`.
2. Put the database path on durable storage with least-privilege permissions.
3. Configure backup, retention, and a tested restore path.
4. Disable anonymous access and configure authentication.
5. Restrict trusted hosts, CORS, and WebSocket origins.
6. Terminate TLS at a maintained proxy or load balancer.
7. Set Runtime and proxy payload limits.
8. Store provider credentials in a secret manager.
9. Grant minimum tool permissions and require approvals for mutations.
10. Exercise cancellation, expiry, reconnect replay, and process restart.

SQLite is not encrypted; use encrypted storage if required. `storage_busy` means bounded
lock retries were exhausted. Move to PostgreSQL when you need sustained concurrent writers,
multi-tenancy, replication, managed backup/PITR, or independently scaled compute.
