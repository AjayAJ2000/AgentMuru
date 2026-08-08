from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence


class MCPToolSource(Protocol):
    async def list_tools(self) -> Sequence[Mapping[str, Any]]: ...

    async def call_tool(self, name: str, arguments: Mapping[str, Any]) -> Any: ...
