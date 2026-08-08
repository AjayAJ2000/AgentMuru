# Architecture before AgentMuru

The former project was a Python UI framework. Public component constructors produced
`VNode` trees. Hook state lived in per-WebSocket render contexts. FastAPI serialized full
trees or diffs to a generic React renderer, and UI callbacks executed application logic.

Useful engineering included WebSocket lifecycle handling, auth and origin checks, safe
asset serving, the React/Vite pipeline, and Databricks identity isolation. The component
catalog, VDOM protocol, page callbacks, and hook state could not naturally represent
long-running model streams, replayable sessions, tools, approvals, artifacts, or traces.
