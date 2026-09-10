#!/usr/bin/env python3
"""Write environment.md for a bench artifact directory. No fake numbers."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import platform
import shutil
import socket
import subprocess
import sys


def _run(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return ""


def _cpu_model() -> str:
    path = Path("/proc/cpuinfo")
    if path.is_file():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.lower().startswith("model name"):
                return line.split(":", 1)[1].strip()
    return platform.processor() or "unknown"


def _pkg_ver(name: str) -> str:
    try:
        import importlib.metadata as md

        return md.version(name)
    except Exception:
        return "not-installed"


def _cyclonedds_c() -> str:
    out = _run(["idlc", "-v"])
    if out:
        return out.splitlines()[0]
    so = Path("/usr/lib/x86_64-linux-gnu/libddsc.so.0.10.4")
    if so.exists():
        return "libddsc.so.0.10.4 (apt)"
    return "unknown"


def _git_sha(root: Path) -> str:
    return _run(["git", "-C", str(root), "rev-parse", "HEAD"]) or "unknown"


def _os_pretty() -> str:
    try:
        return platform.freedesktop_os_release().get("PRETTY_NAME", platform.system())
    except OSError:
        return platform.system()


def _nproc() -> str:
    try:
        return str(os.cpu_count() or "?")
    except OSError:
        return "?"


def render(args: argparse.Namespace) -> str:
    repo = Path(args.repo_root).resolve()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    host = socket.gethostname()
    host_class = args.hostname_class or (
        "cursor-cloud-vm" if host in {"cursor", "codespaces"} else "unknown"
    )
    lines = [
        f"# Environment — {args.chain} / `{args.topology}`",
        "",
        f"- **STATUS:** `{args.status}`",
        f"- **UTC:** `{now}`",
        f"- **Topology (required label):** `{args.topology}`",
        f"- **Chain:** `{args.chain}`",
        f"- **hostname:** `{host}`",
        f"- **hostname class:** `{host_class}`",
        f"- **OS:** `{platform.platform()}` / `{_os_pretty()}`",
        f"- **CPU:** `{_cpu_model()}` × {_nproc()} logical",
        f"- **Python:** `{sys.version.split()[0]}` (`{sys.executable}`)",
        f"- **ROS_DISTRO:** `{os.environ.get('ROS_DISTRO') or args.ros_distro or '(unset)'}`",
        f"- **RMW_IMPLEMENTATION:** `{os.environ.get('RMW_IMPLEMENTATION') or args.rmw or '(unset)'}`",
        f"- **ROS_DOMAIN_ID:** `{os.environ.get('ROS_DOMAIN_ID') or args.ros_domain_id or '(unset)'}`",
        f"- **FASTRTPS_DEFAULT_PROFILES_FILE:** `{os.environ.get('FASTRTPS_DEFAULT_PROFILES_FILE') or '(unset)'}`",
        f"- **CYCLONEDDS_HOME:** `{os.environ.get('CYCLONEDDS_HOME') or '(unset)'}`",
        f"- **CYCLONEDDS_URI:** `{os.environ.get('CYCLONEDDS_URI') or '(unset)'}`",
        f"- **cyclonedds C:** `{_cyclonedds_c()}`",
        f"- **cyclonedds Python:** `{_pkg_ver('cyclonedds')}`",
        f"- **pytest:** `{_pkg_ver('pytest')}`",
        f"- **numpy:** `{_pkg_ver('numpy')}`",
        f"- **pydantic:** `{_pkg_ver('pydantic')}`",
        f"- **rclpy:** `{_pkg_ver('rclpy')}`",
        f"- **git SHA ros2_hzj:** `{_git_sha(repo)}`",
        f"- **DimOS deps source:** `{args.dimos_source}`",
        f"- **DimOS tree:** `{args.dimos_root or '(none)'}`",
        f"- **DimOS git SHA:** `{args.dimos_sha or '(n/a)'}`",
        f"- **which docker:** `{shutil.which('docker') or '(not on PATH)'}`",
        f"- **which ros2:** `{shutil.which('ros2') or '(not on PATH)'}`",
        "",
        "## Notes",
        "",
        args.notes.strip() if args.notes else "(none)",
        "",
        "These facts describe the measurement environment. They are **not** a",
        "root-cause analysis. Do not mix Chain A and Chain B in one table.",
        "",
    ]
    if args.blocked_reason:
        lines[3:3] = [
            f"- **blocked reason:** {args.blocked_reason}",
        ]
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", required=True, help="environment.md path")
    p.add_argument("--repo-root", required=True)
    p.add_argument("--chain", required=True, choices=("A", "B"))
    p.add_argument(
        "--topology",
        required=True,
        choices=("same-process", "same-host", "cross-host-UDP"),
    )
    p.add_argument("--status", required=True, choices=("ok", "blocked", "partial"))
    p.add_argument("--dimos-source", default="unknown")
    p.add_argument("--dimos-root", default="")
    p.add_argument("--dimos-sha", default="")
    p.add_argument("--ros-distro", default="")
    p.add_argument("--rmw", default="")
    p.add_argument("--ros-domain-id", default="")
    p.add_argument("--hostname-class", default="")
    p.add_argument("--blocked-reason", default="")
    p.add_argument("--notes", default="")
    args = p.parse_args()
    text = render(args)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
