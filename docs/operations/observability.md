# Observability

AgentMuru exposes two complementary observability streams: ordered runtime events for product
state and traces for timing and usage.

## Runtime events

Events explain what the application decided and persisted. Each event has session-local order,
a type, IDs, UTC timestamp, and JSON-safe payload. Persisted events drive Workspace replay and
the HTTP and WebSocket APIs.

Consume history through
`GET /api/v1/sessions/{session_id}/events?after=N` or follow the session WebSocket. Store the
last processed sequence as the reconnect cursor.

## Traces

The default `Tracer` creates one trace per run and spans around model and tool work. Spans include
name, kind, parent, status, start, end, duration, and attributes. Normalized provider usage adds
input and output token totals to the trace.

Read a run through `GET /api/v1/runs/{run_id}/traces`.

## Stable error codes

Use run and model error codes for alerts and dashboards. Do not parse exception text. Useful
operational signals include:

| Code | Meaning | Typical action |
| --- | --- | --- |
| `model_rate_limit` | Provider asked the caller to slow down | Retry with bounded backoff |
| `model_timeout` | Provider request exceeded its time budget | Retry if the application permits |
| `model_unavailable` | Connection or provider server failure | Retry and alert on sustained failures |
| `storage_busy` | SQLite lock retries were exhausted | Reduce writers or move the workload |
| `process_interrupted` | Prior process ended with active work | Start a new run after operator review |
| `approval_expired` | No decision arrived before the deadline | Ask for a fresh request |

## Redaction

Tool fields declared in `sensitive_fields` are replaced with `[REDACTED]` in public event
payloads. Provider failure messages are fixed AgentMuru strings and do not include provider
response bodies.

Redaction is not a substitute for data minimization. Do not pass secrets through model prompts,
artifact metadata, trace attributes, or approval reasons.

## Retention boundary

SQLite persists events and artifacts. The default tracer is in memory. Export traces to an
application-owned backend when process-independent retention, aggregation, or alerting is
required.
