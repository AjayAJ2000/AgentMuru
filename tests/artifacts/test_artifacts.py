from agentmuru.artifacts import ArtifactKind, InMemoryArtifactStore


def test_artifact_store_creates_and_filters_session_artifacts() -> None:
    store = InMemoryArtifactStore()
    artifact = store.create(
        session_id="session-1",
        run_id="run-1",
        kind=ArtifactKind.MARKDOWN,
        name="report.md",
        content="# Report",
        mime_type="text/markdown",
        creator="analyst",
    )

    assert store.get(artifact.id) == artifact
    assert store.list(session_id="session-1") == [artifact]
    assert store.list(session_id="session-2") == []


def test_runtime_artifact_creation_emits_a_reference_without_inlining_content() -> None:
    from agentmuru import Agent, Application, FakeModel, Runtime
    from agentmuru.core.events import EventType

    runtime = Runtime(
        Application(agent=Agent(name="writer", instructions="", model=FakeModel.responses("ok")))
    )
    session = runtime.create_session()

    artifact = runtime.create_artifact(
        session_id=session.id,
        run_id=None,
        kind=ArtifactKind.MARKDOWN,
        name="report.md",
        content="# confidential report body",
        mime_type="text/markdown",
        creator="writer",
    )

    event = next(item for item in session.events if item.type is EventType.ARTIFACT_CREATED)
    assert event.payload["artifact_id"] == artifact.id
    assert "content" not in event.payload
