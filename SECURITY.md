# AgentMuru security

Report vulnerabilities through the repository's
[private security advisory form](https://github.com/AjayAJ2000/AgentMuru/security/advisories/new).
Do not open a public issue containing exploit details, credentials, or sensitive traces.

## Supported versions

| Version | Security updates |
| --- | --- |
| 0.3.x | Yes |
| Earlier versions | No |

## Security boundary

AgentMuru validates tool arguments and policy before invoking handlers, but Python tool
handlers execute with the host process's authority. Run untrusted tools in an external
sandbox. Production deployments must configure authentication, trusted hosts, allowed
WebSocket origins, TLS, secret storage, and durable-store encryption.

Public runtime events redact declared sensitive arguments and avoid exception details.
Application authors must mark sensitive tool fields and must not return secrets as tool
results or artifact content. Review custom exporters and model adapters for accidental
prompt, trace, or credential disclosure.
