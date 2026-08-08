import pytest

from agentmuru.agents import Agent
from agentmuru.models import FakeModel


def test_agent_requires_a_stable_machine_name() -> None:
    with pytest.raises(ValueError, match="name"):
        Agent(name="   ", instructions="help", model=FakeModel.responses("ok"))


def test_agent_rejects_duplicate_tool_names() -> None:
    from agentmuru.tools import tool

    @tool
    def lookup(value: str) -> str:
        return value

    with pytest.raises(ValueError, match="Duplicate tool"):
        Agent(
            name="researcher",
            instructions="help",
            model=FakeModel.responses("ok"),
            tools=(lookup, lookup),
        )
