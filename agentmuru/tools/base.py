from __future__ import annotations

import asyncio
import inspect
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, get_type_hints

from .schema import coerce_value, json_schema


class ApprovalMode(str, Enum):
    AUTO = "auto"
    REQUIRED = "required"
    NEVER = "never"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ToolExecutionError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class Tool:
    name: str
    description: str
    handler: Callable[..., Any]
    input_schema: Mapping[str, Any]
    permission: str | None = None
    approval: ApprovalMode = ApprovalMode.AUTO
    risk: RiskLevel = RiskLevel.LOW
    timeout: float = 30.0
    retries: int = 0
    side_effects: bool = False
    sensitive_fields: frozenset[str] = field(default_factory=frozenset)
    _signature: inspect.Signature = field(repr=False, compare=False, default_factory=inspect.Signature)
    _hints: Mapping[str, Any] = field(repr=False, compare=False, default_factory=dict)

    def provider_schema(self) -> dict[str, Any]:
        return {"name": self.name, "description": self.description, "input_schema": dict(self.input_schema)}

    def redact_arguments(self, arguments: Mapping[str, Any]) -> dict[str, Any]:
        return {
            key: "[REDACTED]" if key in self.sensitive_fields else value
            for key, value in arguments.items()
        }

    async def invoke(self, arguments: Mapping[str, Any]) -> Any:
        unknown = set(arguments) - set(self._signature.parameters)
        if unknown:
            raise ToolExecutionError(f"Unknown tool arguments: {', '.join(sorted(unknown))}")
        kwargs: dict[str, Any] = {}
        for name, parameter in self._signature.parameters.items():
            if name in arguments:
                try:
                    kwargs[name] = coerce_value(self._hints.get(name, Any), arguments[name], name)
                except (TypeError, ValueError) as exc:
                    raise ToolExecutionError(str(exc)) from exc
            elif parameter.default is inspect.Parameter.empty:
                raise ToolExecutionError(f"Tool argument '{name}' is required")

        async def call() -> Any:
            if inspect.iscoroutinefunction(self.handler):
                result = self.handler(**kwargs)
                return await result
            return await asyncio.to_thread(self.handler, **kwargs)

        last_error: Exception | None = None
        for _ in range(self.retries + 1):
            try:
                return await asyncio.wait_for(call(), timeout=self.timeout)
            except Exception as exc:
                last_error = exc
        raise ToolExecutionError(f"Tool '{self.name}' failed: {last_error}") from last_error


def tool(
    function: Callable[..., Any] | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    permission: str | None = None,
    approval: str | ApprovalMode = ApprovalMode.AUTO,
    risk: str | RiskLevel = RiskLevel.LOW,
    timeout: float = 30.0,
    retries: int = 0,
    side_effects: bool = False,
    sensitive_fields: set[str] | frozenset[str] | None = None,
) -> Tool | Callable[[Callable[..., Any]], Tool]:
    def decorate(handler: Callable[..., Any]) -> Tool:
        signature = inspect.signature(handler)
        hints = get_type_hints(handler)
        properties: dict[str, Any] = {}
        required: list[str] = []
        for parameter_name, parameter in signature.parameters.items():
            schema = json_schema(hints.get(parameter_name, Any))
            if parameter.default is inspect.Parameter.empty:
                required.append(parameter_name)
            else:
                schema["default"] = parameter.default
            properties[parameter_name] = schema
        input_schema: dict[str, Any] = {"type": "object", "properties": properties}
        if required:
            input_schema["required"] = required
        return Tool(
            name=name or handler.__name__,
            description=description or inspect.getdoc(handler) or handler.__name__.replace("_", " "),
            handler=handler,
            input_schema=input_schema,
            permission=permission,
            approval=ApprovalMode(approval),
            risk=RiskLevel(risk),
            timeout=timeout,
            retries=retries,
            side_effects=side_effects,
            sensitive_fields=frozenset(sensitive_fields or ()),
            _signature=signature,
            _hints=hints,
        )

    if function is None:
        return decorate
    return decorate(function)
