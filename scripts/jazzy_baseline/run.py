#!/usr/bin/env python3
"""Orchestrate the Jazzy FastDDS / Cyclone baseline matrix.

Does not source ``config/env/chain_a.sh`` and does not load
``config/fastdds.xml``. Stock Jazzy RMW defaults are the 10× denominator.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from defaults import (  # noqa: E402
    DEFAULT_DISCOVER_S,
    DEFAULT_DOMAIN,
    DEFAULT_DURATION_S,
    DEFAULT_MARGIN_S,
    DEFAULT_MODES,
    DEFAULT_QOS,
    DEFAULT_REPEATS,
    DEFAULT_RMWS,
    DEFAULT_SIZES,
    DEFAULT_TOPOLOGY,
    DEFAULT_WARMUP_S,
    HEADER_SIZE,
    SMOKE_DURATION_S,
    SMOKE_HZ,
    SMOKE_QOS,
    SMOKE_REPEATS,
    SMOKE_SIZES,
    SMOKE_WARMUP_S,
    hz_for_size,
)
from envinfo import collect, rmw_available, ros_sourced  # noqa: E402
from report import write_reports  # noqa: E402

WORKER = SCRIPT_DIR / "worker.py"


def _csv_list(raw: str, fallback: tuple[str, ...] | tuple[int, ...]) -> list[Any]:
    if not raw:
        return list(fallback)
    out: list[Any] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        out.append(part)
    return out


def _csv_ints(raw: str, fallback: tuple[int, ...]) -> list[int]:
    if not raw:
        return list(fallback)
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rmw", default="", help="comma list, default both stock RMWs")
    p.add_argument("--sizes", default="", help="comma bytes, default 1k,64k,1M,4M")
    p.add_argument("--qos", default="", help="comma: reliable,best_effort")
    p.add_argument("--mode", default="oneway", choices=("oneway", "rtt", "oneway,rtt"))
    p.add_argument(
        "--topology",
        default=DEFAULT_TOPOLOGY,
        choices=("same-host", "same-process", "cross-host"),
    )
    p.add_argument("--hz", type=float, default=None, help="override per-size default Hz")
    p.add_argument("--duration", type=float, default=DEFAULT_DURATION_S)
    p.add_argument("--warmup", type=float, default=DEFAULT_WARMUP_S)
    p.add_argument("--repeats", type=int, default=DEFAULT_REPEATS)
    p.add_argument("--discover", type=float, default=DEFAULT_DISCOVER_S)
    p.add_argument("--margin", type=float, default=DEFAULT_MARGIN_S)
    p.add_argument("--domain", type=int, default=DEFAULT_DOMAIN)
    p.add_argument("--topic-prefix", default="/jazzy_baseline")
    p.add_argument("--out", default="")
    p.add_argument("--worker", default=str(WORKER), help="replacement worker (Rust hook)")
    p.add_argument("--localhost-only", action="store_true", default=True)
    p.add_argument("--no-localhost-only", action="store_false", dest="localhost_only")
    p.add_argument(
        "--smoke",
        action="store_true",
        help="short same-host oneway matrix for CI / cloud VMs",
    )
    p.add_argument(
        "--allow-missing-ros",
        action="store_true",
        help="write STATUS: blocked and exit 0 when Jazzy is not sourced",
    )
    args = p.parse_args(argv)
    if args.smoke:
        args.sizes = args.sizes or ",".join(str(s) for s in SMOKE_SIZES)
        args.qos = args.qos or ",".join(SMOKE_QOS)
        args.mode = "oneway"
        args.topology = "same-host"
        args.duration = SMOKE_DURATION_S
        args.warmup = SMOKE_WARMUP_S
        args.repeats = SMOKE_REPEATS
        if args.hz is None:
            args.hz = SMOKE_HZ
        args.allow_missing_ros = True
    if not args.out:
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%MZ")
        label = "smoke" if args.smoke else stamp
        args.out = str(REPO_ROOT / "docs" / "artifacts" / "jazzy_baseline" / label)
    return args


def _child_env(rmw: str, domain: int, localhost_only: bool) -> dict[str, str]:
    env = os.environ.copy()
    env["RMW_IMPLEMENTATION"] = rmw
    env["ROS_DOMAIN_ID"] = str(domain)
    # Stock Jazzy: do not inherit the Humble Chain A XML seed.
    env.pop("FASTRTPS_DEFAULT_PROFILES_FILE", None)
    env.pop("CYCLONEDDS_URI", None)
    if localhost_only:
        env["ROS_LOCALHOST_ONLY"] = "1"
    else:
        env.pop("ROS_LOCALHOST_ONLY", None)
    return env


def _wait_ready(path: Path, timeout_s: float) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if path.is_file():
            return True
        time.sleep(0.02)
    return False


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"status": "blocked", "blocked_reason": f"missing {path.name}"}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"status": "blocked", "blocked_reason": f"bad json {path.name}: {exc}"}
    if not isinstance(data, dict):
        return {"status": "blocked", "blocked_reason": f"non-object {path.name}"}
    return data


def _merge_case(
    *,
    spec: dict[str, Any],
    pub: dict[str, Any],
    sub: dict[str, Any],
    rmw_version: str,
    host_class: str,
) -> dict[str, Any]:
    status = "ok"
    reason = ""
    if pub.get("status") != "ok":
        status = "blocked"
        reason = str(pub.get("blocked_reason") or "publisher failed")
    elif sub.get("status") != "ok":
        status = "blocked"
        reason = str(sub.get("blocked_reason") or "subscriber failed")
    sent = int(pub.get("sent") or 0)
    # oneway: subscriber holds one-way samples; rtt: client (pub) holds RTT.
    latency_src = pub if spec.get("mode") == "rtt" else sub
    received = int(latency_src.get("received") or sub.get("received") or 0)
    loss = float("nan")
    if sent > 0:
        loss = max(0.0, 1.0 - received / sent)
    row = {
        "status": status,
        "not_final_baseline": True,
        "host_class": host_class,
        "ros_distro": os.environ.get("ROS_DISTRO") or "",
        "rmw": spec["rmw"],
        "rmw_version": rmw_version,
        "qos": spec["qos"],
        "mode": spec["mode"],
        "topology": spec["topology"],
        "size_bytes": spec["size"],
        "hz_offered": spec["hz"],
        "duration_s": spec["duration"],
        "warmup_s": spec["warmup"],
        "repeat": spec["repeat"],
        "sent": sent,
        "received": received,
        "loss_ratio": loss,
        "throughput_msg_s": latency_src.get("throughput_msg_s", float("nan")),
        "throughput_mbyte_s": latency_src.get("throughput_mbyte_s", float("nan")),
        "p50_us": latency_src.get("p50_us", float("nan")),
        "p90_us": latency_src.get("p90_us", float("nan")),
        "p99_us": latency_src.get("p99_us", float("nan")),
        "max_us": latency_src.get("max_us", float("nan")),
        "min_us": latency_src.get("min_us", float("nan")),
        "mean_us": latency_src.get("mean_us", float("nan")),
        "pub_cpu_percent": pub.get("cpu_percent", float("nan")),
        "sub_cpu_percent": sub.get("cpu_percent", float("nan")),
        "pub_rss_kb_avg": pub.get("rss_kb_avg", float("nan")),
        "pub_rss_kb_peak": pub.get("rss_kb_peak", float("nan")),
        "sub_rss_kb_avg": sub.get("rss_kb_avg", float("nan")),
        "sub_rss_kb_peak": sub.get("rss_kb_peak", float("nan")),
        "pub_pid": pub.get("pid", ""),
        "sub_pid": sub.get("pid", ""),
        "blocked_reason": reason,
    }
    return row


def _blocked_row(spec: dict[str, Any], reason: str, host_class: str, rmw_version: str) -> dict[str, Any]:
    return {
        "status": "blocked",
        "not_final_baseline": True,
        "host_class": host_class,
        "ros_distro": os.environ.get("ROS_DISTRO") or "",
        "rmw": spec.get("rmw", ""),
        "rmw_version": rmw_version,
        "qos": spec.get("qos", ""),
        "mode": spec.get("mode", ""),
        "topology": spec.get("topology", ""),
        "size_bytes": spec.get("size", ""),
        "hz_offered": spec.get("hz", ""),
        "duration_s": spec.get("duration", ""),
        "warmup_s": spec.get("warmup", ""),
        "repeat": spec.get("repeat", 1),
        "sent": 0,
        "received": 0,
        "loss_ratio": float("nan"),
        "throughput_msg_s": float("nan"),
        "throughput_mbyte_s": float("nan"),
        "p50_us": float("nan"),
        "p90_us": float("nan"),
        "p99_us": float("nan"),
        "max_us": float("nan"),
        "min_us": float("nan"),
        "mean_us": float("nan"),
        "pub_cpu_percent": float("nan"),
        "sub_cpu_percent": float("nan"),
        "pub_rss_kb_avg": float("nan"),
        "pub_rss_kb_peak": float("nan"),
        "sub_rss_kb_avg": float("nan"),
        "sub_rss_kb_peak": float("nan"),
        "pub_pid": "",
        "sub_pid": "",
        "blocked_reason": reason,
    }


def _worker_cmd(
    args: argparse.Namespace,
    *,
    role: str,
    spec: dict[str, Any],
    result_json: Path,
    sync_dir: Path,
) -> list[str]:
    worker = args.worker
    if Path(worker).is_file() and os.access(worker, os.X_OK) and not worker.endswith(".py"):
        prog = [worker]
    else:
        prog = [sys.executable, worker]
    return prog + [
        "--role",
        role,
        "--mode",
        spec["mode"],
        "--qos",
        spec["qos"],
        "--size",
        str(spec["size"]),
        "--hz",
        str(spec["hz"]),
        "--duration",
        str(spec["duration"]),
        "--warmup",
        str(spec["warmup"]),
        "--discover",
        str(args.discover),
        "--margin",
        str(args.margin),
        "--topic-prefix",
        spec["topic_prefix"],
        "--rmw",
        spec["rmw"],
        "--result-json",
        str(result_json),
        "--sync-dir",
        str(sync_dir),
    ]


def _run_pair(
    args: argparse.Namespace,
    spec: dict[str, Any],
    case_dir: Path,
    env: dict[str, str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    case_dir.mkdir(parents=True, exist_ok=True)
    sync_dir = case_dir / "sync"
    if sync_dir.exists():
        shutil.rmtree(sync_dir)
    sync_dir.mkdir()
    if spec["mode"] == "rtt":
        a_role, b_role = "echo", "client"
        a_ready, b_ready = "echo.ready", "client.ready"
    else:
        a_role, b_role = "sub", "pub"
        a_ready, b_ready = "sub.ready", "pub.ready"
    a_json = case_dir / f"{a_role}.json"
    b_json = case_dir / f"{b_role}.json"
    a_cmd = _worker_cmd(args, role=a_role, spec=spec, result_json=a_json, sync_dir=sync_dir)
    b_cmd = _worker_cmd(args, role=b_role, spec=spec, result_json=b_json, sync_dir=sync_dir)
    proc_a = subprocess.Popen(a_cmd, env=env, cwd=str(REPO_ROOT))
    if not _wait_ready(sync_dir / a_ready, args.discover):
        proc_a.terminate()
        try:
            proc_a.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc_a.kill()
        return (
            {"status": "blocked", "blocked_reason": f"{a_role} never became ready"},
            {"status": "blocked", "blocked_reason": f"{a_role} never became ready"},
        )
    proc_b = subprocess.Popen(b_cmd, env=env, cwd=str(REPO_ROOT))
    go_at = time.monotonic() + 1.0
    (sync_dir / "go").write_text(json.dumps({"go_at_mono": go_at}) + "\n", encoding="utf-8")
    timeout = args.warmup + args.duration + args.discover + args.margin + 20.0
    try:
        proc_b.wait(timeout=timeout)
        proc_a.wait(timeout=args.margin + 10.0)
    except subprocess.TimeoutExpired:
        proc_b.kill()
        proc_a.kill()
    # Publisher/client first, subscriber/echo second (merge expects that order).
    return _load_json(b_json), _load_json(a_json)


def build_specs(args: argparse.Namespace) -> list[dict[str, Any]]:
    rmws = [str(x) for x in _csv_list(args.rmw, DEFAULT_RMWS)]
    sizes = _csv_ints(args.sizes, DEFAULT_SIZES)
    qoss = [str(x) for x in _csv_list(args.qos, DEFAULT_QOS)]
    modes = [m.strip() for m in str(args.mode).split(",") if m.strip()] or list(DEFAULT_MODES)
    specs: list[dict[str, Any]] = []
    for rmw in rmws:
        for qos in qoss:
            for size in sizes:
                if size < HEADER_SIZE:
                    raise ValueError(f"size {size} < header {HEADER_SIZE}")
                for mode in modes:
                    for repeat in range(1, max(args.repeats, 1) + 1):
                        specs.append(
                            {
                                "rmw": rmw,
                                "qos": qos,
                                "size": size,
                                "mode": mode,
                                "repeat": repeat,
                                "hz": hz_for_size(size, args.hz),
                                "duration": args.duration,
                                "warmup": args.warmup,
                                "topology": args.topology,
                                "topic_prefix": f"{args.topic_prefix}/{rmw}_{qos}_{size}_{mode}_r{repeat}",
                            }
                        )
    return specs


def _write_blocked_run(
    out_dir: Path,
    args: argparse.Namespace,
    reason: str,
    specs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    env = collect(REPO_ROOT, extra={"status": "blocked", "blocked_reason": reason})
    host_class = str(env.get("host_class") or "unknown")
    cases = []
    for spec in specs or []:
        cases.append(_blocked_row(spec, reason, host_class, ""))
    payload = {
        "status": "blocked",
        "not_final_baseline": True,
        "blocked_reason": reason,
        "topology": args.topology,
        "domain": args.domain,
        "smoke": bool(args.smoke),
        "environment": env,
        "cases": cases,
        "host_class": host_class,
    }
    write_reports(out_dir, payload)
    return payload


def run_matrix(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = Path(args.out)
    specs = build_specs(args)
    if args.topology == "cross-host":
        reason = (
            "cross-host requires two machines. Start the subscriber/echo with "
            "--role sub|echo on host B, then --role pub|client on host A. "
            "A single VM records STATUS: blocked (no invented percentiles)."
        )
        return _write_blocked_run(out_dir, args, reason, specs)
    if args.topology == "same-process":
        reason = (
            "same-process is reserved; the required scenario is same-host "
            "two-process. Re-run with --topology same-host."
        )
        return _write_blocked_run(out_dir, args, reason, specs)
    if not ros_sourced():
        reason = (
            "ROS 2 Jazzy is not sourced (no ROS_DISTRO/AMENT_PREFIX_PATH). "
            "Use ./scripts/jazzy_baseline/docker_run.sh or "
            "`source /opt/ros/jazzy/setup.bash`."
        )
        return _write_blocked_run(out_dir, args, reason, specs)

    env_facts = collect(REPO_ROOT, extra={"status": "ok"})
    host_class = str(env_facts.get("host_class") or "unknown")
    cases: list[dict[str, Any]] = []
    any_ok = False
    for spec in specs:
        rmw = spec["rmw"]
        rmw_ver = str((env_facts.get("packages") or {}).get(rmw) or "")
        if not rmw_available(rmw):
            cases.append(
                _blocked_row(
                    spec,
                    f"RMW {rmw} shared library not found on AMENT_PREFIX_PATH",
                    host_class,
                    rmw_ver,
                )
            )
            continue
        case_dir = (
            out_dir
            / "cases"
            / rmw
            / spec["qos"]
            / spec["mode"]
            / str(spec["size"])
            / f"r{spec['repeat']}"
        )
        child_env = _child_env(rmw, args.domain, args.localhost_only and args.topology != "cross-host")
        print(
            f"[jazzy-baseline] {rmw} {spec['qos']} {spec['mode']} "
            f"{spec['size']}B @{spec['hz']}Hz repeat {spec['repeat']}",
            flush=True,
        )
        pub, sub = _run_pair(args, spec, case_dir, child_env)
        row = _merge_case(
            spec=spec,
            pub=pub,
            sub=sub,
            rmw_version=rmw_ver,
            host_class=host_class,
        )
        if row["status"] == "ok":
            any_ok = True
        cases.append(row)

    status = "ok" if any_ok and all(c["status"] == "ok" for c in cases) else (
        "partial" if any_ok else "blocked"
    )
    env_facts["status"] = status
    payload = {
        "status": status,
        "not_final_baseline": True,
        "topology": args.topology,
        "domain": args.domain,
        "smoke": bool(args.smoke),
        "environment": env_facts,
        "cases": cases,
        "host_class": host_class,
    }
    write_reports(out_dir, payload)
    return payload


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = run_matrix(args)
    print(f"[jazzy-baseline] STATUS={payload['status']} out={args.out}", flush=True)
    if payload["status"] == "blocked" and not args.allow_missing_ros and not args.smoke:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
