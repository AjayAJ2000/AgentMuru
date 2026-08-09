class AgentMuruError(Exception):
    """Base class for errors safe to classify at runtime boundaries."""

    code = "agentmuru_error"


class SessionNotFoundError(AgentMuruError):
    code = "session_not_found"


class RunNotFoundError(AgentMuruError):
    code = "run_not_found"


class ProtocolError(AgentMuruError):
    code = "protocol_error"


class StorageError(AgentMuruError):
    code = "storage_error"


class StorageBusyError(StorageError):
    code = "storage_busy"


class StorageSerializationError(StorageError):
    code = "storage_serialization"


class StorageCorruptError(StorageError):
    code = "storage_corrupt"


class StorageMigrationError(StorageError):
    code = "storage_migration"
