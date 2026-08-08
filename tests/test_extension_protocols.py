import pytest

from agentmuru.guardrails import GuardrailResult, apply_guardrails
from agentmuru.knowledge import Document
from agentmuru.memory import ConversationMemory


@pytest.mark.asyncio
async def test_conversation_memory_retention_is_opt_in() -> None:
    default_memory = ConversationMemory()
    retained_memory = ConversationMemory(retain=True)

    await default_memory.save("session-1", "secret")
    await retained_memory.save("session-1", "remembered")

    assert await default_memory.recall("session-1") == ()
    assert await retained_memory.recall("session-1") == ("remembered",)


def test_document_is_provider_neutral() -> None:
    document = Document(id="doc-1", content="hello", metadata={"source": "local"})
    assert document.metadata["source"] == "local"


@pytest.mark.asyncio
async def test_guardrail_pipeline_stops_on_rejection() -> None:
    async def allow(value: str) -> GuardrailResult:
        return GuardrailResult.allow(value.strip())

    async def reject(value: str) -> GuardrailResult:
        return GuardrailResult.reject("blocked")

    result = await apply_guardrails(" input ", (allow, reject))

    assert not result.allowed
    assert result.reason == "blocked"
