from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from agentmuru.agents import Agent
from agentmuru.artifacts import ArtifactStore, InMemoryArtifactStore
from agentmuru.sessions import InMemorySessionStore, SessionStore


@dataclass(slots=True)
class Application:
    agent: Agent
    agents: tuple[Agent, ...] = ()
    title: str = "AgentMuru"
    description: str = "A governed AI application"
    session_store: SessionStore = field(default_factory=InMemorySessionStore)
    artifact_store: ArtifactStore = field(default_factory=InMemoryArtifactStore)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        all_agents = (self.agent, *self.agents)
        names = [agent.name for agent in all_agents]
        if len(names) != len(set(names)):
            raise ValueError("Application agent names must be unique")

    def get_agent(self, name: str) -> Agent:
        for agent in (self.agent, *self.agents):
            if agent.name == name:
                return agent
        raise KeyError(f"Application has no agent named '{name}'")

    def run(self, *, host: str = "127.0.0.1", port: int = 8000) -> None:
        from agentmuru.server import run_server

        run_server(self, host=host, port=port)
