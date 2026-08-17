# SQLite persistence

`SQLitePersistence` composes session, artifact, and approval stores around one standard-library
SQLite database.

```python
from agentmuru import Application, Runtime, SQLitePersistence

persistence = SQLitePersistence("agentmuru.db")
application = Application(
    agent=agent,
    session_store=persistence.sessions,
    artifact_store=persistence.artifacts,
)
runtime = Runtime(application, approvals=persistence.approval_service())
```

## Stored data

The current schema stores sessions, messages, complete assistant tool calls, runs, ordered
events, idempotency bindings, artifacts, and approval records. Text and bytes retain their type.
Event payloads and metadata must be finite JSON.

## Constructor

```python
SQLitePersistence(
    path,
    busy_timeout_ms=5000,
    max_retries=4,
    poll_interval=0.05,
)
```

The default busy timeout is 5,000 ms. Locked writes retry after 25, 50, 100, and 200 ms in
addition to SQLite's timeout. Exhaustion raises the stable `storage_busy` error.

## Ownership and concurrency

Operate one active AgentMuru runtime process for each database file. Multiple threads and store
clients may use it. WAL lets readers continue during a writer, while SQLite still serializes
writes.

Event sequences are allocated with `BEGIN IMMEDIATE` and a dedicated session counter. AgentMuru
commits an event before publishing it to subscribers.

Use another `SessionStore` implementation when sustained concurrent writers, replication,
managed point-in-time recovery, or independent compute and storage are requirements.

## Schema migration

First open creates the current schema and enables foreign keys, WAL, and the configured busy
timeout. An older AgentMuru schema migrates forward transactionally. A database created by a
newer AgentMuru schema fails closed instead of being opened with an older package.

## Restart recovery

Completed history reopens unchanged. Runtime construction marks queued, running, and
waiting-approval records failed with `process_interrupted`, stores a completion timestamp, and
appends `run.failed`. AgentMuru does not claim to resume a lost Python coroutine.

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

Test a restore by opening the backup with `SQLitePersistence` and reading known session, run,
and event IDs.

## Security

The database is not encrypted by AgentMuru. Restrict the database and backup paths with
operating-system permissions, use encrypted storage when required, and keep secrets out of
messages, events, artifact metadata, and approval reasons.
