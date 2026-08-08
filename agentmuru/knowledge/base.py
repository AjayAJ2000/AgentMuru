from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, Sequence


@dataclass(frozen=True, slots=True)
class Document:
    id: str
    content: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


class KnowledgeSource(Protocol):
    async def documents(self) -> Sequence[Document]: ...


class Retriever(Protocol):
    async def retrieve(self, query: str, *, limit: int = 5) -> Sequence[Document]: ...


class EmbeddingProvider(Protocol):
    async def embed(self, texts: Sequence[str]) -> Sequence[Sequence[float]]: ...
