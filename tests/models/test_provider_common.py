from __future__ import annotations

import pytest

from agentmuru.integrations.providers import (
    ProviderConfigurationError,
    ProviderDependencyError,
)
from agentmuru.integrations.providers._common import (
    dependency_error,
    parse_tool_arguments,
    validate_settings,
)


def test_provider_settings_split_common_and_vendor_options() -> None:
    common, vendor = validate_settings(
        {
            "temperature": 0.2,
            "max_output_tokens": 64,
            "provider_options": {"effort": "low"},
        }
    )

    assert common == {"temperature": 0.2, "max_output_tokens": 64}
    assert vendor == {"effort": "low"}


def test_provider_settings_reject_unknown_normalized_key() -> None:
    with pytest.raises(ProviderConfigurationError, match="unsupported model setting 'seed'"):
        validate_settings({"seed": 42})


def test_provider_settings_reject_reserved_provider_option() -> None:
    with pytest.raises(
        ProviderConfigurationError,
        match="reserved provider option 'model'",
    ):
        validate_settings({"provider_options": {"model": "override"}})


def test_provider_settings_require_provider_options_mapping() -> None:
    with pytest.raises(
        ProviderConfigurationError,
        match="provider_options must be a mapping",
    ):
        validate_settings({"provider_options": "effort=low"})


def test_parse_tool_arguments_requires_json_object() -> None:
    assert parse_tool_arguments('{"query":"muru"}') == {"query": "muru"}

    with pytest.raises(ProviderConfigurationError, match="valid JSON object"):
        parse_tool_arguments('["muru"]')

    with pytest.raises(ProviderConfigurationError, match="valid JSON object"):
        parse_tool_arguments('{"query":')


def test_dependency_error_names_the_exact_extra() -> None:
    error = dependency_error("openai", "openai")

    assert isinstance(error, ProviderDependencyError)
    assert str(error) == (
        "OpenAI support requires an optional dependency. "
        'Install it with: python -m pip install "agentmuru[openai]"'
    )
