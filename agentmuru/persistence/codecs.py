from __future__ import annotations

import json
from typing import Any

from agentmuru.core.errors import StorageCorruptError, StorageSerializationError


def encode_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise StorageSerializationError("Value cannot be stored safely") from exc


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"Unsupported JSON constant: {value}")


def decode_json(value: str) -> Any:
    try:
        return json.loads(value, parse_constant=_reject_json_constant)
    except (json.JSONDecodeError, ValueError) as exc:
        raise StorageCorruptError("Stored JSON content is invalid") from exc


def encode_content(value: Any) -> tuple[str, bytes]:
    if isinstance(value, str):
        return "text", value.encode("utf-8")
    if isinstance(value, bytes):
        return "bytes", value
    return "json", encode_json(value).encode("utf-8")


def decode_content(encoding: str, payload: bytes) -> Any:
    if encoding == "bytes":
        return payload
    if encoding == "text":
        try:
            return payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise StorageCorruptError("Stored text content is invalid") from exc
    if encoding == "json":
        try:
            return decode_json(payload.decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise StorageCorruptError("Stored JSON content is invalid") from exc
    raise StorageCorruptError("Stored content uses an unsupported encoding")
