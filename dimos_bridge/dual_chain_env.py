"""薄包装：读双链环境契约，默认不改 os.environ。

``config/env/load.py`` 是双链契约（RMW 标识 / ROS_DOMAIN_ID / XML 路径）的
唯一可执行真源；本模块只做 importlib 重新导出，不得在此复制常量。
DimOS 已拷模块不要 import 本文件来「初始化」。需要对齐某条链时，由操作员显式
调用 ``apply_chain_a`` / ``apply_chain_b``，或 source ``config/env/chain_*.sh``。
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_ENV_PY = Path(__file__).resolve().parents[1] / "config" / "env" / "load.py"
_spec = importlib.util.spec_from_file_location("ros2_hzj_dual_chain_env_load", _ENV_PY)
if _spec is None or _spec.loader is None:
    raise ImportError(f"cannot load env helper at {_ENV_PY}")
_env = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_env)

CHAIN_A = _env.CHAIN_A
CHAIN_B = _env.CHAIN_B


def chain_a_env() -> dict[str, str]:
    return _env.describe("a")


def chain_b_env() -> dict[str, str]:
    return _env.describe("b")


def apply_chain_a() -> None:
    _env.apply(_env.CHAIN_A)


def apply_chain_b() -> None:
    _env.apply(_env.CHAIN_B, unset=_env.CHAIN_B_UNSET)


__all__ = [
    "CHAIN_A",
    "CHAIN_B",
    "apply_chain_a",
    "apply_chain_b",
    "chain_a_env",
    "chain_b_env",
]
