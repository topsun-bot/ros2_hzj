#!/usr/bin/env python3
"""rclpy pub / sub / echo / client worker.

Same CLI is the Rust hook: a replacement binary must accept these flags and
write the same result JSON. See README.md.
"""

from __future__ import annotations

import argparse
import array
from dataclasses import dataclass, field
import json
import math
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
from wire import ProbeHeader, magic_ok, pack, unpack  # noqa: E402


@dataclass
class MeasurementSamples:
    """按发送时间筛选半开测量窗口；测试使用合成报文，不代表 ROS 测量。"""

    start_ns: int
    end_ns: int
    size: int
    samples_ns: list[int] = field(default_factory=list)
    seen: set[int] = field(default_factory=set)
    duplicate_count: int = 0
    invalid_count: int = 0
    outside_window_count: int = 0

    def header(self, blob: Any) -> ProbeHeader | None:
        if len(blob) != self.size:
            self.invalid_count += 1
            return None
        try:
            header = unpack(blob)
        except (ValueError, TypeError):
            self.invalid_count += 1
            return None
        if not magic_ok(header):
            self.invalid_count += 1
            return None
        if not self.start_ns <= header.t0_ns < self.end_ns:
            self.outside_window_count += 1
            return None
        if header.seq in self.seen:
            self.duplicate_count += 1
            return None
        return header

    def observe(self, blob: Any, received_ns: int, pending: dict[int, int] | None = None) -> None:
        header = self.header(blob)
        if header is None:
            return
        if received_ns < header.t0_ns:
            self.invalid_count += 1
            return
        if pending is not None:
            if pending.get(header.seq) != header.t0_ns:
                self.invalid_count += 1
                return
            pending.pop(header.seq)
        self.seen.add(header.seq)
        self.samples_ns.append(received_ns - header.t0_ns)

    def result(self, duration_s: float) -> dict[str, Any]:
        received = len(self.samples_ns)
        result: dict[str, Any] = {
            "status": "ok" if received else "blocked",
            "received": received,
            "duplicate_count": self.duplicate_count,
            "invalid_count": self.invalid_count,
            "outside_window_count": self.outside_window_count,
            "samples_ns": self.samples_ns,
            "throughput_msg_s": received / duration_s,
            "throughput_mbyte_s": received * self.size / duration_s / 1e6,
            "window_s": duration_s,
            **percentiles_us(self.samples_ns),
        }
        if not received:
            result["blocked_reason"] = "no valid measured samples"
        return result


class MeasurementResources:
    """只在测量阶段采样资源；输出实际采样边界，暴露调度延迟。"""

    def __init__(self, start_ns: int, end_ns: int) -> None:
        self.start_ns, self.end_ns = start_ns, end_ns
        self.sampler = ProcSampler(os.getpid())
        self.started = False
        self.stopped = False
        self.next_sample_ns = start_ns

    def update(self, now_ns: int) -> None:
        if not self.started and self.start_ns <= now_ns < self.end_ns:
            self.sampler.start()
            self.started = True
        if self.started and not self.stopped:
            if now_ns >= self.end_ns:
                self.sampler.stop()
                self.stopped = True
            elif now_ns >= self.next_sample_ns:
                self.sampler.sample()
                self.next_sample_ns = now_ns + 100_000_000

    def finish(self) -> dict[str, Any]:
        if self.started and not self.stopped:
            self.sampler.stop()
            self.stopped = True
        result = self.sampler.as_dict()
        result.update({
            "measure_start_ns": self.start_ns,
            "measure_end_ns": self.end_ns,
            "resource_window_observed": self.started,
        })
        return result


def measurement_bounds(go_at: float, warmup: float, duration: float) -> tuple[int, int]:
    start_ns = round(go_at * 1e9) + round(warmup * 1e9)
    return start_ns, start_ns + round(duration * 1e9)


def _spin_timeout(now_ns: int, until_ns: int, start_ns: int, end_ns: int) -> float:
    boundaries = [until_ns]
    if now_ns < end_ns:
        boundaries.append(end_ns)
    if now_ns < start_ns:
        boundaries.append(start_ns)
    return max(0.0, min(0.01, (min(boundaries) - now_ns) / 1e9))


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
                    go_at_mono = float(data["go_at_mono"])
                    if not math.isfinite(go_at_mono) or go_at_mono <= 0:
                        raise ValueError("invalid go_at_mono")
                except (OSError, ValueError, KeyError, TypeError):
                    time.sleep(0.02)
                    continue
                break
            time.sleep(0.02)
        else:
            raise RuntimeError("timed out waiting for a valid synchronized start")
    if go_at_mono is None:
        return time.monotonic()
    if not math.isfinite(go_at_mono) or go_at_mono <= time.monotonic():
        raise RuntimeError("synchronized start is invalid or already expired")
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
    def json_safe(value: Any) -> Any:
        if isinstance(value, float) and not math.isfinite(value):
            return None
        if isinstance(value, dict):
            return {key: json_safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [json_safe(item) for item in value]
        return value

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_safe(payload), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _base_result(args: argparse.Namespace, role: str) -> dict[str, Any]:
    try:
        from rclpy.utilities import get_rmw_implementation_identifier

        actual_rmw = get_rmw_implementation_identifier()
    except (ImportError, RuntimeError):
        actual_rmw = ""
    return {
        "role": role,
        "rmw": actual_rmw,
        "requested_rmw": os.environ.get("RMW_IMPLEMENTATION") or args.rmw or "",
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

    _write_ready(args.sync_dir, args.role)
    go_at = _wait_go(args.sync_dir, args.go_at_mono)
    start_ns, end_ns = measurement_bounds(go_at, args.warmup, args.duration)
    resources = MeasurementResources(start_ns, end_ns)
    period_ns = round(1e9 / args.hz)
    next_ns = round(go_at * 1e9)
    seq = 0
    sent = 0
    late = 0
    while True:
        now = time.monotonic_ns()
        resources.update(now)
        if now >= end_ns:
            break
        if now < next_ns:
            rclpy.spin_once(node, timeout_sec=_spin_timeout(now, next_ns, start_ns, end_ns))
            continue
        stamp = time.monotonic_ns()
        if stamp >= end_ns:
            break
        pub.publish(_make_msg(pack(seq, stamp, args.size)))
        if start_ns <= stamp < end_ns:
            sent += 1
        seq += 1
        next_ns += period_ns
        if next_ns < stamp - period_ns:
            next_ns = stamp
            late += 1
        rclpy.spin_once(node, timeout_sec=0.0)
    resource_result = resources.finish()
    node.destroy_node()
    rclpy.shutdown()
    result = _base_result(args, args.role)
    result.update({"status": "ok" if sent else "blocked", "sent": sent, "late_slots": late, "matched": True})
    if not sent:
        result["blocked_reason"] = "no measured messages sent"
    result.update(resource_result)
    return result


def _msg_type() -> Any:
    from std_msgs.msg import UInt8MultiArray

    return UInt8MultiArray


def _run_sub(args: argparse.Namespace) -> dict[str, Any]:
    import rclpy
    from rclpy.node import Node

    rclpy.init()
    node = Node(f"jazzy_baseline_sub_{os.getpid()}")
    samples: MeasurementSamples | None = None

    def on_msg(msg: Any) -> None:
        now = time.monotonic_ns()
        if samples is not None:
            samples.observe(msg.data, now)

    topic = f"{args.topic_prefix}/{TOPIC_DATA}"
    node.create_subscription(_msg_type(), topic, on_msg, _qos_profile(args.qos))
    _write_ready(args.sync_dir, args.role)
    go_at = _wait_go(args.sync_dir, args.go_at_mono)
    start_ns, end_ns = measurement_bounds(go_at, args.warmup, args.duration)
    samples = MeasurementSamples(start_ns, end_ns, args.size)
    resources = MeasurementResources(start_ns, end_ns)
    stop_ns = end_ns + round(args.margin * 1e9)
    while True:
        now = time.monotonic_ns()
        resources.update(now)
        if now >= stop_ns:
            break
        rclpy.spin_once(node, timeout_sec=_spin_timeout(now, stop_ns, start_ns, end_ns))
    resource_result = resources.finish()
    node.destroy_node()
    rclpy.shutdown()
    result = _base_result(args, args.role)
    result.update(samples.result(args.duration))
    result.update(resource_result)
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
    invalid_count = 0

    def on_msg(msg: Any) -> None:
        nonlocal echoed, invalid_count
        if len(msg.data) != args.size:
            invalid_count += 1
            return
        if not magic_ok(unpack(msg.data)):
            invalid_count += 1
            return
        out.publish(msg)
        echoed += 1

    node.create_subscription(
        _msg_type(), f"{args.topic_prefix}/{TOPIC_DATA}", on_msg, _qos_profile(args.qos)
    )
    _write_ready(args.sync_dir, args.role)
    go_at = _wait_go(args.sync_dir, args.go_at_mono)
    start_ns, end_ns = measurement_bounds(go_at, args.warmup, args.duration)
    resources = MeasurementResources(start_ns, end_ns)
    stop_ns = end_ns + round(args.margin * 1e9)
    while True:
        now = time.monotonic_ns()
        resources.update(now)
        if now >= stop_ns:
            break
        rclpy.spin_once(node, timeout_sec=_spin_timeout(now, stop_ns, start_ns, end_ns))
    resource_result = resources.finish()
    node.destroy_node()
    rclpy.shutdown()
    result = _base_result(args, args.role)
    result.update({"status": "ok" if echoed else "blocked", "echoed": echoed, "invalid_count": invalid_count})
    if not echoed:
        result["blocked_reason"] = "no valid messages echoed"
    result.update(resource_result)
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
    samples: MeasurementSamples | None = None

    def on_pong(msg: Any) -> None:
        now = time.monotonic_ns()
        if samples is not None:
            samples.observe(msg.data, now, pending)

    echo_sub = node.create_subscription(
        _msg_type(), f"{args.topic_prefix}/{TOPIC_ECHO}", on_pong, _qos_profile(args.qos)
    )

    deadline = time.monotonic() + args.discover
    matched = False
    while time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.05)
        if pub.get_subscription_count() >= 1 and echo_sub.get_publisher_count() >= 1:
            matched = True
            break
    if not matched:
        result = _base_result(args, args.role)
        result.update({"status": "blocked", "blocked_reason": "no matching echo", "sent": 0})
        node.destroy_node()
        rclpy.shutdown()
        return result

    _write_ready(args.sync_dir, args.role)
    go_at = _wait_go(args.sync_dir, args.go_at_mono)
    start_ns, end_ns = measurement_bounds(go_at, args.warmup, args.duration)
    resources = MeasurementResources(start_ns, end_ns)
    samples = MeasurementSamples(start_ns, end_ns, args.size)
    period_ns = round(1e9 / args.hz)
    next_ns = round(go_at * 1e9)
    seq = 0
    sent = 0
    while True:
        now = time.monotonic_ns()
        resources.update(now)
        if now >= end_ns:
            break
        if now < next_ns:
            rclpy.spin_once(node, timeout_sec=_spin_timeout(now, next_ns, start_ns, end_ns))
            continue
        stamp = time.monotonic_ns()
        if stamp >= end_ns:
            break
        if start_ns <= stamp < end_ns:
            pending[seq] = stamp
            sent += 1
        pub.publish(_make_msg(pack(seq, stamp, args.size)))
        seq += 1
        next_ns += period_ns
        if next_ns < stamp - period_ns:
            next_ns = stamp
        rclpy.spin_once(node, timeout_sec=0.0)
    resource_result = resources.finish()
    drain_ns = end_ns + round(args.margin * 1e9)
    while time.monotonic_ns() < drain_ns:
        now = time.monotonic_ns()
        rclpy.spin_once(node, timeout_sec=_spin_timeout(now, drain_ns, start_ns, end_ns))
    node.destroy_node()
    rclpy.shutdown()
    result = _base_result(args, args.role)
    result.update(samples.result(args.duration))
    result.update(
        {
            "sent": sent,
            "unanswered": len(pending),
            "matched": True,
        }
    )
    result.update(resource_result)
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
    if not HEADER_SIZE <= args.size <= 4_194_304:
        p.error(f"--size must be between {HEADER_SIZE} and 4194304")
    for name, maximum, zero_allowed in (
        ("hz", 1_000_000.0, False),
        ("duration", 3600.0, False),
        ("warmup", 600.0, True),
        ("discover", 300.0, False),
        ("margin", 300.0, False),
    ):
        value = getattr(args, name)
        if not math.isfinite(value) or value > maximum or value < 0 or (not zero_allowed and value == 0):
            p.error(f"--{name} must be finite, {'>= 0' if zero_allowed else '> 0'} and <= {maximum:g}")
    if args.hz * (args.warmup + args.duration) > 1_000_000:
        p.error("offered messages must not exceed 1000000 per worker run")
    if args.go_at_mono is not None and (not math.isfinite(args.go_at_mono) or args.go_at_mono <= 0):
        p.error("--go-at-mono must be finite and > 0")
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
