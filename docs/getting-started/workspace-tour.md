# Workspace tour

Muru Workspace is an operator view of the same application state exposed by the runtime. It
does not own a second agent model or hide execution state in the browser.

## Sessions

The left rail lists sessions visible to the current principal. Select a session to restore its
messages, runs, current event sequence, artifacts, and pending approvals.

With in-memory storage, sessions last for one process lifetime. With `SQLitePersistence`, they
survive process restarts.

## Conversation

The central pane shows user, assistant, and tool-result messages. Assistant messages keep the
complete tool calls that produced later tool results. This makes a reopened provider
conversation structurally valid.

Submitting a message creates a run and returns immediately. Streaming events update the view
until that run completes, fails, waits for approval, or is cancelled.

## Timeline

Every `RuntimeEvent` has a session-local sequence. The Timeline presents those ordered events,
including model requests, text deltas, tool calls, approval decisions, usage, and terminal run
state.

The WebSocket reconnect cursor uses the last observed sequence. Reconnecting after sequence 12
requests only later events, so the browser can resume without duplicating earlier entries.

## Approvals

Tools marked for approval pause before their handler runs. The Approvals area shows the tool,
its public arguments, permission, risk, and decision state. Sensitive fields are redacted from
public events before the browser receives them.

Approve or reject explicitly. The actor and optional reason become part of the audit record.

## Artifacts

Artifacts are named outputs associated with a session and optional run. The Artifacts area can
open Markdown, code, JSON, tables, charts, files, images, SQL, and reports stored by the
application.

## Traces and usage

Run traces group spans and provider token usage. They help answer where time was spent and how
much model input and output a run consumed. Cost remains optional because not every provider or
deployment supplies it.

## Operator boundary

The bundled Workspace is an MVP operator surface. Add authentication, trusted-host and origin
controls, TLS, and tool isolation before exposing it beyond a trusted development network.
