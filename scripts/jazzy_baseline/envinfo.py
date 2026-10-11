"""Hardware / software environment capture. No ROS import required."""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import platform
import shutil
import socket
import subprocess
from typing import Any


def _run(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return ""


def cpu_model() -> str:
    path = Path("/proc/cpuinfo")
    if path.is_file():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.lower().startswith("model name"):
                return line.split(":", 1)[1].strip()
    return platform.processor() or "unknown"


def os_pretty() -> str:
    try:
        return platform.freedesktop_os_release().get("PRETTY_NAME", platform.system())
    except OSError:
        return platform.system()


def mem_kb() -> int | None:
    path = Path("/proc/meminfo")
    if not path.is_file():
        return None
    for line in path.read_text(encoding="ascii", errors="replace").splitlines():
        if line.startswith("MemTotal:"):
            try:
                return int(line.split()[1])
            except (IndexError, ValueError):
                return None
    return None


def git_sha(root: Path) -> str:
    return (
        _run(["git", "-C", str(root), "-c", f"safe.directory={root}", "rev-parse", "HEAD"])
        or _run(["git", "-C", str(root), "rev-parse", "HEAD"])
        or "unknown"
    )


def hostname_class(host: str | None = None) -> str:
    name = host or socket.gethostname()
    if name in {"cursor", "codespaces"} or name.startswith("cursor"):
        return "cursor-cloud-vm"
    return "unknown"


def dpkg_version(pkg: str) -> str:
    out = _run(["dpkg-query", "-W", "-f=${Version}", pkg])
    return out or "not-installed"


def rmw_so_paths(rmw: str) -> list[Path]:
    names = (f"lib{rmw}.so", f"lib{rmw}.so.1")
    prefixes: list[Path] = []
    for raw in os.environ.get("AMENT_PREFIX_PATH", "").split(":"):
        if raw:
            prefixes.append(Path(raw))
    distro = os.environ.get("ROS_DISTRO") or "jazzy"
    prefixes.append(Path(f"/opt/ros/{distro}"))
    found: list[Path] = []
    seen: set[str] = set()
    for prefix in prefixes:
        for libdir in (prefix / "lib", prefix / "lib" / "x86_64-linux-gnu", prefix / "lib" / "aarch64-linux-gnu"):
            for name in names:
                cand = libdir / name
                key = str(cand)
                if key in seen:
                    continue
                seen.add(key)
                if cand.is_file():
                    found.append(cand)
    return found


def rmw_available(rmw: str) -> bool:
    return bool(rmw_so_paths(rmw))


def ros_sourced() -> bool:
    if os.environ.get("ROS_DISTRO") and shutil.which("ros2"):
        return True
    distro = os.environ.get("ROS_DISTRO") or "jazzy"
    return Path(f"/opt/ros/{distro}/setup.bash").is_file() and bool(
        os.environ.get("AMENT_PREFIX_PATH")
    )


def collect(repo_root: Path, *, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    host = socket.gethostname()
    mem = mem_kb()
    distro = os.environ.get("ROS_DISTRO") or ""
    pkg_prefix = f"ros-{distro}-" if distro else "ros-jazzy-"
    env: dict[str, Any] = {
        "utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hostname": host,
        "host_class": hostname_class(host),
        "not_final_baseline": True,
        "disclaimer": (
            "Cloud / lab measurement only. Not the final 10× denominator "
            "until repeated on the target robot or HIL host."
        ),
        "os": platform.platform(),
        "os_pretty": os_pretty(),
        "kernel": platform.release(),
        "cpu": cpu_model(),
        "nproc": os.cpu_count() or 0,
        "mem_kb": mem,
        "python": platform.python_version(),
        "ros_distro": distro or "(unset)",
        "ros2_which": shutil.which("ros2") or "",
        "rmw_implementation_env": os.environ.get("RMW_IMPLEMENTATION") or "",
        "ros_domain_id": os.environ.get("ROS_DOMAIN_ID") or "",
        "fastrtps_default_profiles_file": os.environ.get("FASTRTPS_DEFAULT_PROFILES_FILE") or "",
        "cyclonedds_uri": os.environ.get("CYCLONEDDS_URI") or "",
        "ros_localhost_only": os.environ.get("ROS_LOCALHOST_ONLY") or "",
        "packages": {
            "rmw_fastrtps_cpp": dpkg_version(f"{pkg_prefix}rmw-fastrtps-cpp"),
            "rmw_cyclonedds_cpp": dpkg_version(f"{pkg_prefix}rmw-cyclonedds-cpp"),
            "rclpy": dpkg_version(f"{pkg_prefix}rclpy"),
            "fastdds": dpkg_version(f"{pkg_prefix}fastdds"),
            "cyclonedds": dpkg_version(f"{pkg_prefix}cyclonedds"),
        },
        "git_sha_ros2_hzj": git_sha(repo_root),
    }
    if extra:
        env.update(extra)
    return env


def render_md(env: dict[str, Any]) -> str:
    pkgs = env.get("packages") or {}
    mem = env.get("mem_kb")
    mem_s = f"{mem} kB" if mem else "unknown"
    lines = [
        "# Environment — Jazzy ROS 2 baseline",
        "",
        f"- **STATUS:** `{env.get('status', 'unknown')}`",
        f"- **not_final_baseline:** `{env.get('not_final_baseline', True)}`",
        f"- **UTC:** `{env.get('utc', '')}`",
        f"- **hostname / class:** `{env.get('hostname', '')}` / `{env.get('host_class', '')}`",
        f"- **OS:** `{env.get('os_pretty', '')}` (`{env.get('os', '')}`)",
        f"- **kernel:** `{env.get('kernel', '')}`",
        f"- **CPU:** `{env.get('cpu', '')}` × {env.get('nproc', '?')} logical",
        f"- **MemTotal:** `{mem_s}`",
        f"- **Python:** `{env.get('python', '')}`",
        f"- **ROS_DISTRO:** `{env.get('ros_distro', '')}`",
        f"- **which ros2:** `{env.get('ros2_which') or '(not on PATH)'}`",
        f"- **RMW_IMPLEMENTATION (env):** `{env.get('rmw_implementation_env') or '(unset)'}`",
        f"- **ROS_DOMAIN_ID:** `{env.get('ros_domain_id') or '(unset)'}`",
        f"- **FASTRTPS_DEFAULT_PROFILES_FILE:** `{env.get('fastrtps_default_profiles_file') or '(unset — stock Jazzy)'}`",
        f"- **CYCLONEDDS_URI:** `{env.get('cyclonedds_uri') or '(unset — stock Jazzy)'}`",
        f"- **ROS_LOCALHOST_ONLY:** `{env.get('ros_localhost_only') or '(unset)'}`",
        f"- **dpkg rmw_fastrtps_cpp:** `{pkgs.get('rmw_fastrtps_cpp', '')}`",
        f"- **dpkg rmw_cyclonedds_cpp:** `{pkgs.get('rmw_cyclonedds_cpp', '')}`",
        f"- **dpkg rclpy:** `{pkgs.get('rclpy', '')}`",
        f"- **dpkg fastdds:** `{pkgs.get('fastdds', '')}`",
        f"- **dpkg cyclonedds:** `{pkgs.get('cyclonedds', '')}`",
        f"- **git SHA ros2_hzj:** `{env.get('git_sha_ros2_hzj', '')}`",
        "",
        "## Notes",
        "",
        env.get("disclaimer", ""),
        "",
        "Stock Jazzy RMW defaults. This harness does **not** `source`",
        "`config/env/chain_a.sh` and does **not** point at `config/fastdds.xml`.",
        "Those are the Humble dual-chain contract, not the 10× denominator.",
        "",
        "Do not paste these numbers into `docs/artifacts/bench/SCOREBOARD.md`.",
        "",
    ]
    if env.get("blocked_reason"):
        lines.insert(3, f"- **blocked reason:** {env['blocked_reason']}")
    return "\n".join(lines)
