from __future__ import annotations

from typing import Any, Mapping, Protocol


class AgentInteropAdapter(Protocol):
    async def send(self, agent: str, message: Mapping[str, Any]) -> Mapping[str, Any]: ...
