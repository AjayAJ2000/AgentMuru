class ProviderConfigurationError(ValueError):
    """Raised before a provider request when AgentMuru settings are invalid."""


class ProviderDependencyError(ImportError):
    """Raised when an optional official provider SDK is not installed."""


__all__ = ["ProviderConfigurationError", "ProviderDependencyError"]
