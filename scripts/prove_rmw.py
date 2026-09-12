#!/usr/bin/env python3
"""Print which RMW the current process would load (wiki3 §6.3).

Vanilla box (no ROS): still exit 0 and say "ROS not loaded".
No extra dependencies. Patterns follow scripts/bench/collect_env.py.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys


def _run(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return ""


def _env(name: str) -> str:
    value = os.environ.get(name)
    return value if value else "(unset)"


def _unique_existing(paths: list[Path]) -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for path in paths:
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if resolved in seen or not resolved.is_dir():
            continue
        seen.add(resolved)
        out.append(resolved)
    return out


def _lib_search_dirs() -> list[Path]:
    dirs: list[Path] = []
    for part in (os.environ.get("LD_LIBRARY_PATH") or "").split(os.pathsep):
        if part:
            dirs.append(Path(part))
    for part in (os.environ.get("PATH") or "").split(os.pathsep):
        if not part:
            continue
        path = Path(part)
        dirs.append(path)
        if path.name == "bin":
            dirs.append(path.parent / "lib")
            dirs.append(path.parent / "lib" / "x86_64-linux-gnu")
    distro = os.environ.get("ROS_DISTRO")
    if distro:
        prefix = Path("/opt/ros") / distro
        dirs.append(prefix / "lib")
        dirs.append(prefix / "lib" / "x86_64-linux-gnu")
    ros2 = shutil.which("ros2")
    if ros2:
        parent = Path(ros2).resolve().parent
        if parent.name == "bin":
            dirs.append(parent.parent / "lib")
            dirs.append(parent.parent / "lib" / "x86_64-linux-gnu")
    ament = os.environ.get("AMENT_PREFIX_PATH") or ""
    for part in ament.split(os.pathsep):
        if part:
            prefix = Path(part)
            dirs.append(prefix / "lib")
            dirs.append(prefix / "lib" / "x86_64-linux-gnu")
    return _unique_existing(dirs)


def _find_rmw_sos() -> list[Path]:
    hits: list[Path] = []
    seen: set[Path] = set()
    for directory in _lib_search_dirs():
        try:
            candidates = list(directory.glob("librmw_*.so*"))
            candidates += list(directory.glob("librmw.so*"))
        except OSError:
            continue
        for path in sorted(candidates):
            if not path.is_file():
                continue
            try:
                key = path.resolve()
            except OSError:
                continue
            if key in seen:
                continue
            seen.add(key)
            hits.append(key)
    return hits


def _ldd_rmw_lines(path: Path) -> list[str]:
    out = _run(["ldd", str(path)])
    if not out:
        return []
    return [line.strip() for line in out.splitlines() if "rmw" in line.lower()]


def _try_rclpy_identifier() -> tuple[str, str | None, Path | None]:
    """Return (status, identifier_or_none, extension_so_or_none)."""
    try:
        import rclpy  # type: ignore
    except Exception as exc:  # ImportError, OSError, missing .so
        return f"not importable ({type(exc).__name__}: {exc})", None, None

    ident = None
    try:
        from rclpy.utilities import get_rmw_implementation_identifier  # type: ignore

        ident = get_rmw_implementation_identifier()
    except Exception:
        getter = getattr(rclpy, "get_rmw_implementation_identifier", None)
        if callable(getter):
            try:
                ident = getter()
            except Exception:
                ident = None

    ext_path = None
    try:
        import rclpy._rclpy_pybind11 as ext  # type: ignore

        raw = getattr(ext, "__file__", None)
        if raw:
            ext_path = Path(raw)
    except Exception:
        raw = getattr(rclpy, "__file__", None)
        if raw:
            ext_path = Path(raw)

    if ident:
        return "imported", str(ident), ext_path
    return "imported, identifier unavailable", None, ext_path


def render() -> str:
    rclpy_status, ident, ext_path = _try_rclpy_identifier()
    sos = _find_rmw_sos()
    ros_loaded = ident is not None or bool(sos) or rclpy_status.startswith("imported")

    lines = [
        "# prove_rmw (wiki3 §6.3)",
        "",
        f"- **ROS_DISTRO:** `{_env('ROS_DISTRO')}`",
        f"- **RMW_IMPLEMENTATION:** `{_env('RMW_IMPLEMENTATION')}`",
        f"- **ROS_DOMAIN_ID:** `{_env('ROS_DOMAIN_ID')}`",
        f"- **FASTRTPS_DEFAULT_PROFILES_FILE:** `{_env('FASTRTPS_DEFAULT_PROFILES_FILE')}`",
        f"- **CYCLONEDDS_URI:** `{_env('CYCLONEDDS_URI')}`",
        f"- **rclpy:** {rclpy_status}",
        f"- **rmw identifier (runtime):** `{ident or '(not loaded)'}`",
        f"- **which ros2:** `{shutil.which('ros2') or '(not on PATH)'}`",
        f"- **which ldd:** `{shutil.which('ldd') or '(not on PATH)'}`",
        "",
    ]

    if ext_path is not None:
        lines.append(f"- **rclpy extension / module file:** `{ext_path}`")
        ldd_hits = _ldd_rmw_lines(ext_path) if ext_path.is_file() else []
        if ldd_hits:
            lines.append("- **ldd rmw lines (rclpy module):**")
            lines.extend(f"  - `{row}`" for row in ldd_hits)
        lines.append("")

    if sos:
        lines.append(f"- **librmw_*.so on PATH / LD_LIBRARY_PATH ({len(sos)}):**")
        for path in sos[:20]:
            lines.append(f"  - `{path}`")
            ldd_hits = _ldd_rmw_lines(path)
            for row in ldd_hits[:8]:
                lines.append(f"    - ldd: `{row}`")
        if len(sos) > 20:
            lines.append(f"  - … {len(sos) - 20} more omitted")
        lines.append("")
    else:
        lines.extend(
            [
                "- **librmw_*.so:** (none on PATH / LD_LIBRARY_PATH / AMENT_PREFIX_PATH /opt/ros/$ROS_DISTRO)",
                "",
            ]
        )

    lines.extend(
        [
            "Env and filesystem facts only. This is **not** end-to-end delivery,",
            "not a latency measurement, and not Feishu field proof.",
            "`RMW_IMPLEMENTATION` in the environment is a request; the runtime",
            "identifier (if rclpy loaded) is what the process actually linked.",
            "",
        ]
    )

    if not ros_loaded:
        lines.append(
            "ROS not loaded: rclpy is not importable and no librmw_*.so was found. "
            "Env printed above is still valid. Exit 0."
        )
    elif ident is None:
        lines.append(
            "ROS libraries were found or rclpy imported, but the RMW implementation "
            "identifier is unavailable. Exit 0."
        )
    else:
        lines.append(f"ROS loaded: runtime RMW identifier is `{ident}`. Exit 0.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    sys.stdout.write(render())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
