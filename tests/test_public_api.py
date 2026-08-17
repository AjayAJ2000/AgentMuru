def test_agentmuru_public_api_exposes_runtime_primitives() -> None:
    import agentmuru

    assert agentmuru.__version__
    assert agentmuru.EventType
    assert agentmuru.RuntimeEvent
    assert agentmuru.Session
    assert agentmuru.InMemorySessionStore
    assert agentmuru.SQLitePersistence
    assert agentmuru.Agent
    assert agentmuru.FakeModel
    assert agentmuru.tool


def test_provider_public_modules_export_official_adapters() -> None:
    from agentmuru.integrations.anthropic import AnthropicModel
    from agentmuru.integrations.google import GoogleGenAIModel
    from agentmuru.integrations.openai import OpenAIModel

    assert OpenAIModel.name == "openai"
    assert AnthropicModel.name == "anthropic"
    assert GoogleGenAIModel.name == "google"
