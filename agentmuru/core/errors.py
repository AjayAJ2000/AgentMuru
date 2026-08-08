class AgentMuruError(Exception):
    """Base class for errors safe to classify at runtime boundaries."""

    code = "agentmuru_error"


class SessionNotFoundError(AgentMuruError):
    code = "session_not_found"


class RunNotFoundError(AgentMuruError):
    code = "run_not_found"


class ProtocolError(AgentMuruError):
    code = "protocol_error"
