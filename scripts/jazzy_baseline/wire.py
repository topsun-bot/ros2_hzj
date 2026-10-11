"""On-the-wire probe layout shared by the rclpy worker and a future Rust worker.

Layout (little-endian), total length = requested message size::

    magic  u32  = 0x4A5A4253  ("JZBS")
    seq    u32
    t0_ns  u64  CLOCK_MONOTONIC on same-host / same-process
    payload     zero-padded to size
"""

from __future__ import annotations

from dataclasses import dataclass
import struct

from defaults import HEADER_SIZE, WIRE_MAGIC

_HEADER = struct.Struct("<IIQ")


@dataclass(frozen=True)
class ProbeHeader:
    magic: int
    seq: int
    t0_ns: int


def pack(seq: int, t0_ns: int, size_bytes: int) -> bytes:
    if size_bytes < HEADER_SIZE:
        raise ValueError(f"size_bytes must be >= {HEADER_SIZE}, got {size_bytes}")
    header = _HEADER.pack(WIRE_MAGIC, int(seq) & 0xFFFFFFFF, int(t0_ns) & 0xFFFFFFFFFFFFFFFF)
    return header + bytes(size_bytes - HEADER_SIZE)


def unpack(blob: bytes) -> ProbeHeader:
    if len(blob) < HEADER_SIZE:
        raise ValueError(f"blob shorter than header: {len(blob)}")
    magic, seq, t0_ns = _HEADER.unpack_from(blob)
    return ProbeHeader(magic=magic, seq=seq, t0_ns=t0_ns)


def magic_ok(header: ProbeHeader) -> bool:
    return header.magic == WIRE_MAGIC
