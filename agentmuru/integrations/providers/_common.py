from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from . import ProviderConfigurationError, ProviderDependencyError

NORMALIZED_SETTINGS = frozenset(
    {"max_output_tokens", "temperature", "top_p", "stop", "tool_choice"}
)
RESERVED_PROVIDER_OPTIONS = frozenset(
    {
        "api_key",
        "base_url",
        "base_urls",
        "client",
        "input",
        "instructions",
        "messages",
        "model",
        "stream",
        "tools",
    }
)
PROVIDER_NAMES = {
    "anthropic": "Anthropic",
    "google": "Google",
    "openai": "OpenAI",
}


def validate_settings(
    settings: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    unknown = sorted(set(settings) - NORMALIZED_SETTINGS - {"provider_options"})
    if unknown:
        raise ProviderConfigurationError(f"unsupported model setting '{unknown[0]}'")
    provider_options = settings.get("provider_options", {})
    if not isinstance(provider_options, Mapping):
        raise ProviderConfigurationError("provider_options must be a mapping")
    reserved = sorted(set(provider_options) & RESERVED_PROVIDER_OPTIONS)
    if reserved:
        raise ProviderConfigurationError(f"reserved provider option '{reserved[0]}'")
    common = {key: settings[key] for key in NORMALIZED_SETTINGS if key in settings}
    return common, dict(provider_options)


def parse_tool_arguments(value: str) -> dict[str, Any]:
    try:
        decoded = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ProviderConfigurationError("tool arguments must be a valid JSON object") from exc
    if not isinstance(decoded, dict):
        raise ProviderConfigurationError("tool arguments must be a valid JSON object")
    return decoded


def dependency_error(extra: str, module_name: str) -> ProviderDependencyError:
    display_name = PROVIDER_NAMES.get(extra, module_name)
    return ProviderDependencyError(
        f"{display_name} support requires an optional dependency. "
        f'Install it with: python -m pip install "agentmuru[{extra}]"'
    )
