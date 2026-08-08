# Sessions and memory

A `Session` explicitly contains messages, runs, ordered events, user ownership, and
metadata. `SessionStore` is the persistence boundary. The bundled in-memory store is
concurrency-safe and suitable for local development, tests, and a single process.

Memory is separate from message history. `ConversationMemory` retains nothing unless
constructed with `retain=True`. Production applications should state what is saved, for
how long, and how users can remove it.
