from __future__ import annotations

import pytest

from agentmuru.core.errors import StorageCorruptError, StorageSerializationError
from agentmuru.persistence.codecs import decode_content, decode_json, encode_content, encode_json


@pytest.mark.parametrize(
    ("value", "encoding", "payload"),
    [
        ("hello", "text", b"hello"),
        (b"\x00\x01", "bytes", b"\x00\x01"),
        ({"rows": [1, 2], "ready": True}, "json", b'{"ready":true,"rows":[1,2]}'),
        ([True, None, 3.5], "json", b"[true,null,3.5]"),
    ],
)
def test_content_codec_round_trips_supported_values(
    value: object,
    encoding: str,
    payload: bytes,
) -> None:
    encoded = encode_content(value)

    assert encoded == (encoding, payload)
    assert decode_content(*encoded) == value


def test_json_codec_is_deterministic_and_round_trips_unicode() -> None:
    encoded = encode_json({"z": "முரு", "a": 1})

    assert encoded == '{"a":1,"z":"முரு"}'
    assert decode_json(encoded) == {"a": 1, "z": "முரு"}


@pytest.mark.parametrize(
    "value",
    [
        {"value": float("nan")},
        {"value": float("inf")},
        object(),
    ],
)
def test_content_codec_rejects_values_that_cannot_be_persisted(value: object) -> None:
    with pytest.raises(StorageSerializationError) as exc_info:
        encode_content(value)

    assert exc_info.value.code == "storage_serialization"
    assert str(exc_info.value) == "Value cannot be stored safely"


def test_content_codec_classifies_unknown_encoding_as_corrupt_storage() -> None:
    with pytest.raises(StorageCorruptError) as exc_info:
        decode_content("pickle", b"unsafe")

    assert exc_info.value.code == "storage_corrupt"
    assert str(exc_info.value) == "Stored content uses an unsupported encoding"


def test_json_codec_classifies_malformed_stored_json_as_corrupt_storage() -> None:
    with pytest.raises(StorageCorruptError) as exc_info:
        decode_json("{not-json")

    assert exc_info.value.code == "storage_corrupt"
    assert str(exc_info.value) == "Stored JSON content is invalid"
