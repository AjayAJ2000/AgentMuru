# Add a session store

Implement `SessionStore`: create, get, list, save, append event, and event history. Event
append must atomically allocate the next sequence for one session. Publish only after the
transaction commits. A production adapter also needs ownership queries, retention rules,
encryption, backup, and a reconnect subscription mechanism.
