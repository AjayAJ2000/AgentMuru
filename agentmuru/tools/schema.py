from __future__ import annotations

import types
from dataclasses import MISSING, fields, is_dataclass
from enum import Enum
from typing import Any, Literal, Union, get_args, get_origin


def json_schema(annotation: Any) -> dict[str, Any]:
    if annotation is Any:
        return {}
    if annotation is None or annotation is type(None):
        return {"type": "null"}
    if annotation is str:
        return {"type": "string"}
    if annotation is bool:
        return {"type": "boolean"}
    if annotation is int:
        return {"type": "integer"}
    if annotation is float:
        return {"type": "number"}

    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin in (list, tuple, set):
        return {"type": "array", "items": json_schema(args[0] if args else Any)}
    if origin is dict:
        return {"type": "object", "additionalProperties": json_schema(args[1] if args else Any)}
    if origin is Literal:
        return {"enum": list(args)}
    if origin in (Union, types.UnionType):
        return {"anyOf": [json_schema(arg) for arg in args]}
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return {"enum": [member.value for member in annotation]}
    if isinstance(annotation, type) and is_dataclass(annotation):
        properties: dict[str, Any] = {}
        required: list[str] = []
        for item in fields(annotation):
            properties[item.name] = json_schema(item.type)
            if item.default is not MISSING:
                properties[item.name]["default"] = item.default
            elif item.default_factory is MISSING:
                required.append(item.name)
        schema: dict[str, Any] = {"type": "object", "properties": properties}
        if required:
            schema["required"] = required
        return schema
    return {"type": "string"}


def coerce_value(annotation: Any, value: Any, path: str) -> Any:
    if annotation is Any:
        return value
    if isinstance(annotation, type) and is_dataclass(annotation):
        if not isinstance(value, dict):
            raise TypeError(f"{path} must be an object")
        kwargs: dict[str, Any] = {}
        for item in fields(annotation):
            if item.name in value:
                kwargs[item.name] = coerce_value(item.type, value[item.name], f"{path}.{item.name}")
            elif item.default is MISSING and item.default_factory is MISSING:
                raise TypeError(f"{path}.{item.name} is required")
        return annotation(**kwargs)
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin is list:
        if not isinstance(value, list):
            raise TypeError(f"{path} must be an array")
        return [coerce_value(args[0] if args else Any, item, path) for item in value]
    if origin in (Union, types.UnionType):
        for candidate in args:
            try:
                return coerce_value(candidate, value, path)
            except (TypeError, ValueError):
                continue
        raise TypeError(f"{path} has an invalid value")
    if annotation in (str, bool, int, float) and not isinstance(value, annotation):
        raise TypeError(f"{path} must be {annotation.__name__}")
    return value
