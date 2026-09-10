#!/usr/bin/env python3
"""双链环境变量 helper（R1）。默认只打印，不改 os.environ。

用法（仓库根）：
  python3 config/env/load.py print-a
  eval "$(python3 config/env/load.py export-a)"
  python3 config/env/load.py apply-a   # 仅当前 Python 进程
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FASTDDS_XML = REPO_ROOT / "config" / "fastdds.xml"

# 契约值。导入本模块不会写入 os.environ。
CHAIN_A: dict[str, str] = {
    "RMW_IMPLEMENTATION": "rmw_fastrtps_cpp",
    "ROS_DOMAIN_ID": "42",
    "FASTRTPS_DEFAULT_PROFILES_FILE": str(FASTDDS_XML),
}

CHAIN_B: dict[str, str] = {
    "RMW_IMPLEMENTATION": "rmw_cyclonedds_cpp",
    "ROS_DOMAIN_ID": "0",
}

CHAIN_B_UNSET = ("CYCLONEDDS_URI",)


def describe(chain: str) -> dict[str, str]:
    if chain == "a":
        return dict(CHAIN_A)
    if chain == "b":
        return dict(CHAIN_B)
    raise ValueError(f"unknown chain: {chain}")


def export_shell(values: dict[str, str], unset: tuple[str, ...] = ()) -> str:
    lines = [f"export {key}={_sh_single(value)}" for key, value in values.items()]
    lines.extend(f"unset {key}" for key in unset)
    return "\n".join(lines) + "\n"


def apply(values: dict[str, str], *, unset: tuple[str, ...] = ()) -> None:
    """显式写入当前进程。调用方必须点名 apply，禁止在 import 时调用。"""
    os.environ.update(values)
    for key in unset:
        os.environ.pop(key, None)


def _sh_single(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=(
            "print-a",
            "print-b",
            "export-a",
            "export-b",
            "apply-a",
            "apply-b",
        ),
    )
    args = parser.parse_args(argv)
    chain = "a" if args.command.endswith("-a") else "b"
    values = describe(chain)
    unset = CHAIN_B_UNSET if chain == "b" else ()

    if args.command.startswith("print-"):
        for key, value in values.items():
            print(f"{key}={value}")
        return 0
    if args.command.startswith("export-"):
        print(export_shell(values, unset), end="")
        return 0
    apply(values, unset=unset)
    print(f"applied chain {chain} to current process only", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
