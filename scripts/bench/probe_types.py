"""IDL probe type for scripts/bench/pingpong.py (must not live in __main__).

Do not use ``from __future__ import annotations`` here: cyclonedds IdlStruct
needs real ``sequence[uint8]`` objects at class-body time.
"""

from dataclasses import dataclass

from cyclonedds.idl import IdlStruct
from cyclonedds.idl.types import sequence, uint32, uint64, uint8


@dataclass
class BenchProbe(IdlStruct):  # type: ignore[misc]
    seq: uint32  # type: ignore[valid-type]
    t0_ns: uint64  # type: ignore[valid-type]
    payload: sequence[uint8]  # type: ignore[valid-type]
