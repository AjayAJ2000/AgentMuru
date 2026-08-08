from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from agentmuru.agents import Agent
from agentmuru.artifacts import ArtifactStore, InMemoryArtifactStore
from agentmuru.sessions import InMemorySessionStore, SessionStore


@dataclass(slots=True)
class Application:
    agent: Agent
    title: str = "AgentMuru"
    description: str = "A governed AI application"
    session_store: SessionStore = field(default_factory=InMemorySessionStore)
    artifact_store: ArtifactStore = field(default_factory=InMemoryArtifactStore)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def run(self, *, host: str = "127.0.0.1", port: int = 8000) -> None:
        from agentmuru.server import run_server

        run_server(self, host=host, port=port)
