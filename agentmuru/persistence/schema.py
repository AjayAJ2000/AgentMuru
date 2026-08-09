from __future__ import annotations

SCHEMA_VERSION = 1

MIGRATION_1 = (
    """
    CREATE TABLE sessions (
        id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        user_id TEXT,
        title TEXT,
        metadata TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE messages (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
        position INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        name TEXT,
        tool_call_id TEXT,
        UNIQUE(session_id, position)
    )
    """,
    """
    CREATE TABLE runs (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
        agent_name TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        completed_at TEXT,
        error_code TEXT
    )
    """,
    """
    CREATE TABLE event_counters (
        session_id TEXT PRIMARY KEY REFERENCES sessions(id) ON DELETE CASCADE,
        next_sequence INTEGER NOT NULL CHECK(next_sequence > 0)
    )
    """,
    """
    CREATE TABLE events (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
        sequence INTEGER NOT NULL CHECK(sequence > 0),
        type TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        run_id TEXT,
        trace_id TEXT,
        parent_id TEXT,
        payload TEXT NOT NULL,
        UNIQUE(session_id, sequence)
    )
    """,
    """
    CREATE TABLE artifacts (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
        run_id TEXT,
        kind TEXT NOT NULL,
        name TEXT NOT NULL,
        content BLOB NOT NULL,
        content_encoding TEXT NOT NULL,
        mime_type TEXT NOT NULL,
        creator TEXT NOT NULL,
        metadata TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE approvals (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
        run_id TEXT NOT NULL,
        tool_call_id TEXT NOT NULL,
        tool_name TEXT NOT NULL,
        arguments TEXT NOT NULL,
        permission TEXT,
        risk TEXT NOT NULL,
        status TEXT NOT NULL,
        requested_at TEXT NOT NULL,
        expires_at TEXT,
        decided_at TEXT,
        actor TEXT,
        reason TEXT
    )
    """,
    """
    CREATE TABLE idempotency_keys (
        session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
        key TEXT NOT NULL,
        run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
        PRIMARY KEY(session_id, key)
    )
    """,
    "CREATE INDEX messages_session_position ON messages(session_id, position)",
    "CREATE INDEX runs_session_created ON runs(session_id, created_at)",
    "CREATE INDEX events_session_sequence ON events(session_id, sequence)",
    "CREATE INDEX artifacts_session_created ON artifacts(session_id, created_at)",
    "CREATE INDEX approvals_session_requested ON approvals(session_id, requested_at)",
)
