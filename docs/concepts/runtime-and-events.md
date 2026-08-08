# Runtime and events

`Application` composes agents and stores. `Runtime` owns execution, cancellation,
approvals, event ordering, and publication. Every state transition is a `RuntimeEvent`
with a stable ID, UTC timestamp, session/run/trace relationships, JSON-safe payload, and
monotonic session sequence.

Stores append an event before subscribers see it. A WebSocket reconnect sends its last
sequence, replays later events, then follows the live stream. This makes the workspace a
projection rather than the source of truth.
