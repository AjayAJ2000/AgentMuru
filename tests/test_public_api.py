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
