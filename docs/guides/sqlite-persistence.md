# Operate SQLite persistence

AgentMuru 0.2 uses Python's standard-library `sqlite3` module to persist sessions,
messages, runs, ordered events, artifacts, approvals, and idempotency bindings in one file.

## Configure it

```python
from agentmuru import Agent, Application, FakeModel, Runtime, SQLitePersistence

persistence = SQLitePersistence("agentmuru.db")
application = Application(
    agent=Agent(name="assistant", instructions="", model=FakeModel.responses("Ready.")),
    session_store=persistence.sessions,
    artifact_store=persistence.artifacts,
)
runtime = Runtime(application, approvals=persistence.approval_service())
```

The constructor is `SQLitePersistence(path, *, busy_timeout_ms=5000, max_retries=4,
poll_interval=0.05)`. The default busy timeout is 5,000 ms. Locked writes use a bounded
25/50/100/200 ms retry schedule. Exhaustion raises `storage_busy`.

## Ownership and concurrency

Use **one active AgentMuru runtime process** for each database file. Multiple store clients
and threads may access it: WAL permits readers during a writer, while SQLite serializes
writes. Each event sequence is allocated in a `BEGIN IMMEDIATE` transaction with a
dedicated counter row. AgentMuru commits before publishing.

This is a modest-concurrency design. Sustained multi-tenant writes, replication,
point-in-time recovery, or independent compute/storage are signals for PostgreSQL behind
the same protocols.

## Schema and content

First open creates schema version 1 and enables foreign keys, WAL, and the configured busy
timeout. Newer schemas fail closed. Text and bytes retain type; finite JSON is encoded
deterministically. Unsupported content is rejected before insert.

## Restart behavior

Completed history reopens unchanged. Runtime construction marks queued, running, and
waiting-approval records failed with `process_interrupted`, stores a completion timestamp,
and appends `run.failed`. AgentMuru does not pretend to resurrect a lost Python coroutine.
Idempotency bindings also survive reopen.

## Backup and restore

Use SQLite's online backup API instead of copying a hot file:

```python
import sqlite3

source = sqlite3.connect("agentmuru.db")
target = sqlite3.connect("backups/agentmuru.db")
with target:
    source.backup(target)
target.close()
source.close()
```

Test restore by opening the backup with `SQLitePersistence` and reading known session and
event IDs.

## Security limitations

The SQLite file is **not encrypted** by AgentMuru. Restrict the database path with OS
permissions, use encrypted storage when needed, keep secrets out of durable records, and
never put the file under a public static directory.

## Cross-instance replay

Store clients poll committed rows after the last sequence and use a local event bus for
same-process delivery. A reconnecting Workspace sends `after=<sequence>` and receives
every committed later event in order.
