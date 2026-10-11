#!/usr/bin/env python3
"""rclpy pub / sub / echo / client worker.

Same CLI is the Rust hook: a replacement binary must accept these flags and
write the same result JSON. See README.md.
"""

from __future__ import annotations

import argparse
import array
import json
import os
from pathlib import Path
import sys
import time
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from defaults import HEADER_SIZE, TOPIC_DATA, TOPIC_ECHO  # noqa: E402
from metrics import ProcSampler, percentiles_us  # noqa: E402
from wire import magic_ok, pack, unpack  # noqa: E402


def _qos_profile(kind: str) -> Any:
    from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy

    if kind == "best_effort":
        return QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            durability=DurabilityPolicy.VOLATILE,
        )
    if kind == "reliable":
        return QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=16,
            durability=DurabilityPolicy.VOLATILE,
        )
    raise ValueError(f"unknown qos: {kind}")


def _make_msg(blob: bytes) -> Any:
    from std_msgs.msg import UInt8MultiArray

    msg = UInt8MultiArray()
    msg.data = array.array("B", blob)
    return msg


def _wait_go(sync_dir: Path | None, go_at_mono: float | None) -> float:
    if sync_dir is not None:
        go_path = sync_dir / "go"
        deadline = time.monotonic() + 60.0
        while time.monotonic() < deadline:
            if go_path.is_file():
                try:
                    data = json.loads(go_path.read_text(encoding="utf-8"))
                    go_at_mono = float(data.get("go_at_mono", 0.0)) or go_at_mono
                except (OSError, ValueError, json.JSONDecodeError):
                    pass
                break
            time.sleep(0.02)
    if go_at_mono is None:
        return time.monotonic()
    while time.monotonic() < go_at_mono:
        time.sleep(0.005)
    return go_at_mono


def _write_ready(sync_dir: Path | None, role: str) -> None:
    if sync_dir is None:
        return
    sync_dir.mkdir(parents=True, exist_ok=True)
    (sync_dir / f"{role}.ready").write_text("ready\n", encoding="utf-8")
    print("WORKER_READY", role, flush=True)


def _write_result(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _base_result(args: argparse.Namespace, role: str) -> dict[str, Any]:
    return {
        "role": role,
        "rmw": os.environ.get("RMW_IMPLEMENTATION") or args.rmw or "",
        "qos": args.qos,
        "size_bytes": args.size,
        "mode": args.mode,
        "hz": args.hz,
        "duration_s": args.duration,
        "warmup_s": args.warmup,
        "pid": os.getpid(),
    }


def _run_pub(args: argparse.Namespace) -> dict[str, Any]:
    import rclpy
    from rclpy.node import Node

    rclpy.init()
    node = Node(f"jazzy_baseline_pub_{os.getpid()}")
    topic = f"{args.topic_prefix}/{TOPIC_ECHO if args.mode == 'rtt' else TOPIC_DATA}"
    if args.mode == "rtt":
        topic = f"{args.topic_prefix}/{TOPIC_DATA}"
    pub = node.create_publisher(_msg_type(), topic, _qos_profile(args.qos))
    _write_ready(args.sync_dir, args.role)
    _wait_go(args.sync_dir, args.go_at_mono)

    deadline = time.monotonic() + args.discover
    matched = False
    while time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.05)
        if pub.get_subscription_count() >= 1:
            matched = True
            break
    if not matched:
        result = _base_result(args, args.role)
        result.update({"status": "blocked", "blocked_reason": "no matching subscriber", "sent": 0})
        node.destroy_node()
        rclpy.shutdown()
        return result

    sampler = ProcSampler(os.getpid())
    sampler.start()
    t0 = time.monotonic()
    t_warm_end = t0 + args.warmup
    t_end = t_warm_end + args.duration
    period = 1.0 / args.hz
    next_t = t0
    seq = 0
    sent = 0
    late = 0
    blob_pad = pack(0, 0, args.size)  # size check; rebuilt per publish
    del blob_pad
    while time.monotonic() < t_end:
        now = time.monotonic()
        if now < next_t:
            time.sleep(min(next_t - now, 0.001))
            rclpy.spin_once(node, timeout_sec=0.0)
            continue
        stamp = time.monotonic_ns()
        pub.publish(_make_msg(pack(seq, stamp, args.size)))
        if now >= t_warm_end:
            sent += 1
        seq += 1
        next_t += period
        if next_t < now - period:
            next_t = now
            late += 1
        if seq % 32 == 0:
            sampler.sample()
        rclpy.spin_once(node, timeout_sec=0.0)
    sampler.stop()
    node.destroy_node()
    rclpy.shutdown()
    result = _base_result(args, args.role)
    result.update({"status": "ok", "sent": sent, "late_slots": late, "matched": True})
    result.update(sampler.as_dict())
    return result


def _msg_type() -> Any:
    from std_msgs.msg import UInt8MultiArray

    return UInt8MultiArray


def _run_sub(args: argparse.Namespace) -> dict[str, Any]:
    import rclpy
    from rclpy.node import Node

    rclpy.init()
    node = Node(f"jazzy_baseline_sub_{os.getpid()}")
    samples_ns: list[int] = []
    received = 0
    bad_magic = 0
    first_ns: int | None = None
    last_ns: int | None = None
    measure_start = float("inf")

    def on_msg(msg: Any) -> None:
        nonlocal received, bad_magic, first_ns, last_ns
        now = time.monotonic_ns()
        wall = time.monotonic()
        try:
            header = unpack(bytes(msg.data))
        except ValueError:
            return
        if not magic_ok(header):
            bad_magic += 1
            return
        if wall < measure_start:
            return
        samples_ns.append(now - header.t0_ns)
        received += 1
        if first_ns is None:
            first_ns = now
        last_ns = now

    topic = f"{args.topic_prefix}/{TOPIC_DATA}"
    node.create_subscription(_msg_type(), topic, on_msg, _qos_profile(args.qos))
    _write_ready(args.sync_dir, args.role)
    go_at = _wait_go(args.sync_dir, args.go_at_mono)
    measure_start = go_at + args.warmup
    stop_at = measure_start + args.duration + args.margin
    sampler = ProcSampler(os.getpid())
    sampler.start()
    while time.monotonic() < stop_at:
        rclpy.spin_once(node, timeout_sec=0.05)
        if int(time.monotonic() * 10) % 8 == 0:
            sampler.sample()
    sampler.stop()
    node.destroy_node()
    rclpy.shutdown()
    window = args.duration if args.duration > 0 else 1e-9
    if first_ns is not None and last_ns is not None and last_ns > first_ns:
        window = max((last_ns - first_ns) / 1e9, 1e-9)
    stats = percentiles_us(samples_ns)
    result = _base_result(args, args.role)
    result.update(
        {
            "status": "ok",
            "received": received,
            "bad_magic": bad_magic,
            "throughput_msg_s": received / window,
            "throughput_mbyte_s": (received * args.size) / window / 1e6,
            "window_s": window,
            **stats,
        }
    )
    result.update(sampler.as_dict())
    return result


def _run_echo(args: argparse.Namespace) -> dict[str, Any]:
    import rclpy
    from rclpy.node import Node

    rclpy.init()
    node = Node(f"jazzy_baseline_echo_{os.getpid()}")
    out = node.create_publisher(
        _msg_type(), f"{args.topic_prefix}/{TOPIC_ECHO}", _qos_profile(args.qos)
    )
    echoed = 0

    def on_msg(msg: Any) -> None:
        nonlocal echoed
        out.publish(msg)
        echoed += 1

    node.create_subscription(
        _msg_type(), f"{args.topic_prefix}/{TOPIC_DATA}", on_msg, _qos_profile(args.qos)
    )
    _write_ready(args.sync_dir, args.role)
    go_at = _wait_go(args.sync_dir, args.go_at_mono)
    stop_at = go_at + args.warmup + args.duration + args.margin
    sampler = ProcSampler(os.getpid())
    sampler.start()
    while time.monotonic() < stop_at:
        rclpy.spin_once(node, timeout_sec=0.05)
        sampler.sample()
    sampler.stop()
    node.destroy_node()
    rclpy.shutdown()
    result = _base_result(args, args.role)
    result.update({"status": "ok", "echoed": echoed})
    result.update(sampler.as_dict())
    return result


def _run_client(args: argparse.Namespace) -> dict[str, Any]:
    import rclpy
    from rclpy.node import Node

    rclpy.init()
    node = Node(f"jazzy_baseline_client_{os.getpid()}")
    pub = node.create_publisher(
        _msg_type(), f"{args.topic_prefix}/{TOPIC_DATA}", _qos_profile(args.qos)
    )
    pending: dict[int, int] = {}
    rtt_ns: list[int] = []
    received = 0

    def on_pong(msg: Any) -> None:
        nonlocal received
        now = time.monotonic_ns()
        try:
            header = unpack(bytes(msg.data))
        except ValueError:
            return
        t0 = pending.pop(header.seq, None)
        if t0 is None:
            return
        rtt_ns.append(now - t0)
        received += 1

    node.create_subscription(
        _msg_type(), f"{args.topic_prefix}/{TOPIC_ECHO}", on_pong, _qos_profile(args.qos)
    )
    _write_ready(args.sync_dir, args.role)
    _wait_go(args.sync_dir, args.go_at_mono)

    deadline = time.monotonic() + args.discover
    matched = False
    while time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.05)
        if pub.get_subscription_count() >= 1:
            matched = True
            break
    if not matched:
        result = _base_result(args, args.role)
        result.update({"status": "blocked", "blocked_reason": "no matching echo", "sent": 0})
        node.destroy_node()
        rclpy.shutdown()
        return result

    sampler = ProcSampler(os.getpid())
    sampler.start()
    t0 = time.monotonic()
    t_warm_end = t0 + args.warmup
    t_end = t_warm_end + args.duration
    period = 1.0 / args.hz
    next_t = t0
    seq = 0
    sent = 0
    while time.monotonic() < t_end:
        now = time.monotonic()
        if now < next_t:
            rclpy.spin_once(node, timeout_sec=min(next_t - now, 0.01))
            continue
        stamp = time.monotonic_ns()
        if now >= t_warm_end:
            pending[seq] = stamp
            sent += 1
        pub.publish(_make_msg(pack(seq, stamp, args.size)))
        seq += 1
        next_t += period
        if next_t < now - period:
            next_t = now
        rclpy.spin_once(node, timeout_sec=0.0)
    drain = time.monotonic() + args.margin
    while time.monotonic() < drain:
        rclpy.spin_once(node, timeout_sec=0.05)
    sampler.stop()
    node.destroy_node()
    rclpy.shutdown()
    window = args.duration if args.duration > 0 else 1e-9
    stats = percentiles_us(rtt_ns)
    result = _base_result(args, args.role)
    result.update(
        {
            "status": "ok",
            "sent": sent,
            "received": received,
            "throughput_msg_s": received / window,
            "throughput_mbyte_s": (received * args.size) / window / 1e6,
            "window_s": window,
            "matched": True,
            **stats,
        }
    )
    result.update(sampler.as_dict())
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--role", required=True, choices=("pub", "sub", "echo", "client"))
    p.add_argument("--mode", default="oneway", choices=("oneway", "rtt"))
    p.add_argument("--qos", default="reliable", choices=("reliable", "best_effort"))
    p.add_argument("--size", type=int, required=True)
    p.add_argument("--hz", type=float, required=True)
    p.add_argument("--duration", type=float, required=True)
    p.add_argument("--warmup", type=float, default=1.0)
    p.add_argument("--discover", type=float, default=15.0)
    p.add_argument("--margin", type=float, default=3.0)
    p.add_argument("--topic-prefix", default="/jazzy_baseline")
    p.add_argument("--rmw", default="")
    p.add_argument("--result-json", required=True)
    p.add_argument("--sync-dir", default="")
    p.add_argument("--go-at-mono", type=float, default=None)
    args = p.parse_args(argv)
    if args.size < HEADER_SIZE:
        p.error(f"--size must be >= {HEADER_SIZE}")
    if args.hz <= 0 or args.duration <= 0:
        p.error("--hz and --duration must be > 0")
    args.sync_dir = Path(args.sync_dir) if args.sync_dir else None
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    runners = {
        "pub": _run_pub,
        "sub": _run_sub,
        "echo": _run_echo,
        "client": _run_client,
    }
    try:
        result = runners[args.role](args)
    except Exception as exc:  # noqa: BLE001 — worker must always write a result
        result = _base_result(args, args.role)
        result.update({"status": "blocked", "blocked_reason": f"{type(exc).__name__}: {exc}"})
    _write_result(Path(args.result_json), result)
    return 0 if result.get("status") == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
