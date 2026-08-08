# Tools and approvals

`@tool` derives JSON Schema from Python annotations and dataclasses. A tool declares its
permission, risk, approval policy, side effects, timeout, retries, and sensitive fields.
The runtime validates arguments and policy before invoking the handler.

Approval-required calls produce a durable request, pause the run, and appear in Muru
Workspace. An approve or reject decision records actor, reason, and time, emits an audit
event, and resumes the run. A rejection is a modeled tool result, not an unhandled error.
