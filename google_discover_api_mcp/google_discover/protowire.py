"""The few protobuf wire helpers the feed needs: encode the request, list the strings of the answer.

Field numbers come from Chromium components/feed/core/proto/v2/wire (request.proto, feed_request.proto,
client_info.proto, version.proto, display_info.proto, feed_query.proto, capability.proto). No schema
compiler: the request is small and fixed, and the answer is read as the strings it carries, in order.
"""

from __future__ import annotations

import struct

# Nested messages deeper than this are read as bytes, not walked.
_MAX_DEPTH = 80


def _varint(value: int) -> bytes:
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def uint(field: int, value: int) -> bytes:
    return _varint(field << 3) + _varint(value)


def message(field: int, body: bytes) -> bytes:
    return _varint(field << 3 | 2) + _varint(len(body)) + body


def float32(field: int, value: float) -> bytes:
    return _varint(field << 3 | 5) + struct.pack("<f", value)


def _read_varint(data: bytes, at: int) -> tuple[int, int]:
    shift = result = 0
    while True:
        byte = data[at]
        at += 1
        result |= (byte & 0x7F) << shift
        shift += 7
        if byte < 0x80:
            return result, at


def _strings(data: bytes, depth: int) -> list[str] | None:
    """The strings of `data` read as a message, depth first; None when `data` is not a message."""
    at, end, found = 0, len(data), []
    try:
        while at < end:
            key, at = _read_varint(data, at)
            kind = key & 7
            if key >> 3 == 0:
                return None
            if kind == 0:
                _, at = _read_varint(data, at)
            elif kind == 1:
                at += 8
            elif kind == 5:
                at += 4
            elif kind == 2:
                size, at = _read_varint(data, at)
                if at + size > end:
                    return None
                part = data[at : at + size]
                at += size
                inner = _strings(part, depth + 1) if depth < _MAX_DEPTH and size > 1 else None
                if inner:
                    found.extend(inner)
                    continue
                try:
                    text = part.decode()
                except UnicodeDecodeError:
                    continue
                if text.isprintable():
                    found.append(text)
            else:
                return None
    except IndexError:
        return None
    return found if at == end else None


def strings(data: bytes) -> list[str]:
    return _strings(data, 0) or []
