from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class GuardrailResult(Generic[T]):
    allowed: bool
    value: T | None = None
    reason: str | None = None

    @classmethod
    def allow(cls, value: T) -> "GuardrailResult[T]":
        return cls(allowed=True, value=value)

    @classmethod
    def reject(cls, reason: str) -> "GuardrailResult[T]":
        return cls(allowed=False, reason=reason)


Guardrail = Callable[[T], GuardrailResult[T] | Awaitable[GuardrailResult[T]]]


async def apply_guardrails(value: T, guardrails: Sequence[Guardrail[T]]) -> GuardrailResult[T]:
    current = value
    for guardrail in guardrails:
        result = guardrail(current)
        if inspect.isawaitable(result):
            result = await result
        if not result.allowed:
            return result
        if result.value is not None:
            current = result.value
    return GuardrailResult.allow(current)
