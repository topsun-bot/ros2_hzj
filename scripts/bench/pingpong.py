#!/usr/bin/env python3
"""Thin ping-pong RTT wrapper. Does not change ddspubsub / rospubsub.

Measures round-trip times in *this script only* (request topic → echo →
reply topic). Production DimOS / vendor code is import-only.

Chain B uses ``dimos.protocol.pubsub.impl.ddspubsub.DDS`` (Cyclone, domain 0)
when that import works. Chain A uses rclpy + std_msgs/ByteMultiArray when ROS
is present.

Topology is an explicit CLI flag. Never mix Chain A and Chain B in one file.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import statistics
import struct
import subprocess
import sys
import threading
import time
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]


def percentiles_us(samples_ns: list[int]) -> dict[str, float]:
    if not samples_ns:
        return {"p50_us": float("nan"), "p95_us": float("nan"), "p99_us": float("nan")}
    xs = sorted(samples_ns)
    def pct(p: float) -> float:
        if len(xs) == 1:
            return xs[0] / 1000.0
        k = (len(xs) - 1) * (p / 100.0)
        lo = int(k)
        hi = min(lo + 1, len(xs) - 1)
        frac = k - lo
        return (xs[lo] * (1.0 - frac) + xs[hi] * frac) / 1000.0

    return {
        "p50_us": pct(50),
        "p95_us": pct(95),
        "p99_us": pct(99),
        "min_us": xs[0] / 1000.0,
        "max_us": xs[-1] / 1000.0,
        "mean_us": (sum(xs) / len(xs)) / 1000.0,
        "stdev_us": (statistics.pstdev(xs) / 1000.0) if len(xs) > 1 else 0.0,
    }


def _rebuild_dds_config() -> None:
    """Pydantic 2.13 needs Qos imported before DDSConfig is instantiated.

    DimOS ``DDSConfig.qos`` is a forward ref (Qos imported under TYPE_CHECKING).
    This is a bench-host shim only — it does not edit ddsservice.py.
    """
    from cyclonedds.qos import Qos as _Qos
    import dimos.protocol.service.ddsservice as ddsvc

    ddsvc.Qos = _Qos  # runtime name for the TYPE_CHECKING forward ref
    ddsvc.DDSConfig.model_rebuild()


def _qos_cyclone(kind: str) -> Any:
    from cyclonedds.qos import Policy, Qos

    if kind == "high_throughput":
        return Qos(
            Policy.Reliability.BestEffort,
            Policy.History.KeepLast(depth=1),
            Policy.Durability.Volatile,
        )
    if kind == "reliable":
        return Qos(
            Policy.Reliability.Reliable(max_blocking_time=0),
            Policy.History.KeepLast(depth=5000),
            Policy.Durability.Volatile,
        )
    raise ValueError(kind)


def _ensure_dimos_path(dimos_root: str | None) -> None:
    if not dimos_root:
        return
    root = str(Path(dimos_root).resolve())
    if root not in sys.path:
        sys.path.insert(0, root)


def _make_probe_type() -> type:
    # IdlStruct types cannot be defined in __main__ (uint32 fails to resolve).
    if str(SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPT_DIR))
    from probe_types import BenchProbe

    return BenchProbe


def _payload_pattern(msg_size: int) -> list[int]:
    """Reuse across samples so 100KiB–1MiB cases do not rebuild every ping."""
    if msg_size <= 0:
        return []
    pat = list(range(256))
    reps, rem = divmod(msg_size, 256)
    return pat * reps + pat[:rem]


def _wait_interval(last_pub_ns: int | None, interval_ms: float) -> None:
    """Sleep so successive publishes honor a minimum inter-message gap."""
    if last_pub_ns is None or interval_ms <= 0:
        return
    elapsed_ms = (time.perf_counter_ns() - last_pub_ns) / 1e6
    remain = interval_ms - elapsed_ms
    if remain > 0:
        time.sleep(remain / 1000.0)


def _interval_series_stats(
    timestamps_ns: list[int],
    *,
    target_interval_ms: float,
    prefix: str,
) -> dict[str, Any]:
    """Percentiles and jitter of consecutive inter-timestamp gaps.

    Primary IMU metrics live here: interval stdev and |I − target| p95/p99.
    RFC 3550 interarrival jitter is the running mean of |Δinterval|.
    """
    empty = {
        f"{prefix}_count": 0,
        f"{prefix}_p50_us": float("nan"),
        f"{prefix}_p95_us": float("nan"),
        f"{prefix}_p99_us": float("nan"),
        f"{prefix}_min_us": float("nan"),
        f"{prefix}_max_us": float("nan"),
        f"{prefix}_mean_us": float("nan"),
        f"{prefix}_stdev_us": float("nan"),
        f"{prefix}_jitter_abs_p50_us": float("nan"),
        f"{prefix}_jitter_abs_p95_us": float("nan"),
        f"{prefix}_jitter_abs_p99_us": float("nan"),
        f"{prefix}_jitter_rfc3550_us": float("nan"),
        f"{prefix}_target_us": (
            target_interval_ms * 1000.0 if target_interval_ms > 0 else None
        ),
    }
    if len(timestamps_ns) < 2:
        return empty
    gaps_ns = [b - a for a, b in zip(timestamps_ns, timestamps_ns[1:])]
    stats = percentiles_us(gaps_ns)
    target_ns = target_interval_ms * 1e6 if target_interval_ms > 0 else None
    if target_ns is not None:
        abs_dev_ns = [abs(g - target_ns) for g in gaps_ns]
        dev = percentiles_us([int(x) for x in abs_dev_ns])
    else:
        # No target: jitter vs the series median.
        mid = stats["p50_us"] * 1000.0
        abs_dev_ns = [abs(g - mid) for g in gaps_ns]
        dev = percentiles_us([int(x) for x in abs_dev_ns])
    rfc_us = 0.0
    if len(gaps_ns) >= 2:
        j = 0.0
        for i in range(1, len(gaps_ns)):
            d = abs(gaps_ns[i] - gaps_ns[i - 1])
            j = j + (d - j) / 16.0
        rfc_us = j / 1000.0
    return {
        f"{prefix}_count": len(gaps_ns),
        f"{prefix}_p50_us": stats["p50_us"],
        f"{prefix}_p95_us": stats["p95_us"],
        f"{prefix}_p99_us": stats["p99_us"],
        f"{prefix}_min_us": stats["min_us"],
        f"{prefix}_max_us": stats["max_us"],
        f"{prefix}_mean_us": stats["mean_us"],
        f"{prefix}_stdev_us": stats["stdev_us"],
        f"{prefix}_jitter_abs_p50_us": dev["p50_us"],
        f"{prefix}_jitter_abs_p95_us": dev["p95_us"],
        f"{prefix}_jitter_abs_p99_us": dev["p99_us"],
        f"{prefix}_jitter_rfc3550_us": rfc_us,
        f"{prefix}_target_us": (
            target_interval_ms * 1000.0 if target_interval_ms > 0 else None
        ),
    }


def _jitter_fields(
    *,
    rtt_ns: list[int],
    pub_ns: list[int],
    arrival_ns: list[int],
    interval_ms: float,
) -> dict[str, Any]:
    """RTT tail jitter plus inter-publish / inter-arrival interval stats.

    Success is judged on p95/p99 RTT and interval jitter, not p50/mean.
    """
    rtt = percentiles_us(rtt_ns)
    p50 = rtt.get("p50_us")
    p95 = rtt.get("p95_us")
    p99 = rtt.get("p99_us")
    out: dict[str, Any] = {
        "primary_metric": "jitter",
        "rtt_jitter_p95_minus_p50_us": (
            (p95 - p50) if p50 == p50 and p95 == p95 else float("nan")
        ),
        "rtt_jitter_p99_minus_p50_us": (
            (p99 - p50) if p50 == p50 and p99 == p99 else float("nan")
        ),
        "rtt_stdev_us": rtt.get("stdev_us"),
        **_interval_series_stats(
            pub_ns, target_interval_ms=interval_ms, prefix="pub_interval"
        ),
        **_interval_series_stats(
            arrival_ns, target_interval_ms=interval_ms, prefix="arrival_interval"
        ),
    }
    return out


def _case_pacing(interval_ms: float) -> dict[str, Any]:
    if interval_ms > 0:
        hz = 1000.0 / interval_ms
        scale = (os.environ.get("BENCH_SCALE_LABEL") or "").strip()
        scale_bit = f", {scale}" if scale else ""
        return {
            "inter_message_gap_ms": interval_ms,
            "target_publish_hz": hz,
            "scale_label": scale or None,
            "pacing": (
                f"minimum inter-publish gap {interval_ms:g} ms "
                f"(target {hz:.4g} Hz{scale_bit}); "
                "if RTT exceeds the gap, the next ping waits for pong first "
                "(closed-loop; effective rate is 1/RTT)"
            ),
        }
    return {
        "inter_message_gap_ms": 0.0,
        "target_publish_hz": None,
        "pacing": "closed-loop ping-pong (next publish after pong; no extra gap)",
    }


def run_chain_b_same_process(
    *,
    qos_kind: str,
    msg_size: int,
    warmup: int,
    samples: int,
    timeout_s: float,
    topic_prefix: str,
    domain_id: int,
    interval_ms: float = 0.0,
) -> dict[str, Any]:
    from dimos.protocol.pubsub.impl.ddspubsub import DDS, Topic

    _rebuild_dds_config()
    Probe = _make_probe_type()
    qos = _qos_cyclone(qos_kind)
    ping_topic = Topic(name=f"{topic_prefix}/ping", data_type=Probe)
    pong_topic = Topic(name=f"{topic_prefix}/pong", data_type=Probe)

    bus = DDS(qos=qos, domain_id=domain_id)
    bus.start()

    lock = threading.Lock()
    got: dict[int, int] = {}
    ev = threading.Event()
    expect_seq = -1

    def on_ping(message: Any, _topic: Any) -> None:
        bus.publish(pong_topic, message)

    def on_pong(message: Any, _topic: Any) -> None:
        now = time.perf_counter_ns()
        with lock:
            if int(message.seq) == expect_seq:
                got[int(message.seq)] = now
                ev.set()

    bus.subscribe(ping_topic, on_ping)
    bus.subscribe(pong_topic, on_pong)
    time.sleep(0.15)

    payload = _payload_pattern(msg_size)
    rtt_ns: list[int] = []
    pub_ns: list[int] = []
    arrival_ns: list[int] = []
    timeouts = 0
    total = warmup + samples
    last_pub_ns: int | None = None
    for i in range(total):
        _wait_interval(last_pub_ns, interval_ms)
        ev.clear()
        with lock:
            expect_seq = i
            got.pop(i, None)
        t0 = time.perf_counter_ns()
        last_pub_ns = t0
        bus.publish(ping_topic, Probe(seq=i, t0_ns=t0, payload=payload))
        if not ev.wait(timeout=timeout_s):
            timeouts += 1
            if i >= warmup:
                pub_ns.append(t0)
            continue
        with lock:
            t1 = got.get(i)
        if t1 is None:
            timeouts += 1
            if i >= warmup:
                pub_ns.append(t0)
            continue
        if i >= warmup:
            rtt_ns.append(t1 - t0)
            pub_ns.append(t0)
            arrival_ns.append(t1)

    bus.stop()
    stats = percentiles_us(rtt_ns)
    return {
        "name": f"dds_{qos_kind}",
        "impl": "dimos.protocol.pubsub.impl.ddspubsub.DDS",
        "qos": qos_kind,
        "msg_size_bytes": msg_size,
        "payload_len_bytes": msg_size,
        "payload_field": "BenchProbe.payload (sequence[uint8]); plus seq uint32 + t0_ns uint64",
        "warmup": warmup,
        "requested_samples": samples,
        "recorded_samples": len(rtt_ns),
        "timeouts": timeouts,
        "timeout_s": timeout_s,
        "metric": "rtt",
        "units": "microseconds",
        **_case_pacing(interval_ms),
        **stats,
        **_jitter_fields(
            rtt_ns=rtt_ns,
            pub_ns=pub_ns,
            arrival_ns=arrival_ns,
            interval_ms=interval_ms,
        ),
        "rtt_us": [n / 1000.0 for n in rtt_ns],
    }


def run_chain_b_same_host(
    *,
    qos_kind: str,
    msg_size: int,
    warmup: int,
    samples: int,
    timeout_s: float,
    topic_prefix: str,
    domain_id: int,
    dimos_root: str,
    interval_ms: float = 0.0,
) -> dict[str, Any]:
    """Two OS processes; still one host. Responder is this file with --role responder."""
    env = os.environ.copy()
    resp = subprocess.Popen(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--chain",
            "B",
            "--role",
            "responder",
            "--topology",
            "same-host",
            "--qos",
            qos_kind,
            "--topic-prefix",
            topic_prefix,
            "--domain-id",
            str(domain_id),
            "--dimos-root",
            dimos_root,
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        time.sleep(1.2)
        if resp.poll() is not None:
            out = resp.stdout.read() if resp.stdout else ""
            raise RuntimeError(f"responder exited early: {out[-2000:]}")
        result = _chain_b_client_only(
            qos_kind=qos_kind,
            msg_size=msg_size,
            warmup=warmup,
            samples=samples,
            timeout_s=timeout_s,
            topic_prefix=topic_prefix,
            domain_id=domain_id,
            interval_ms=interval_ms,
        )
        result["responder_pid"] = resp.pid
        result["transport_label"] = (
            "same-host two processes; no RouDi ⇒ localhost UDP, not SHM"
        )
        return result
    finally:
        resp.terminate()
        try:
            resp.wait(timeout=3)
        except subprocess.TimeoutExpired:
            resp.kill()


def _chain_b_client_only(
    *,
    qos_kind: str,
    msg_size: int,
    warmup: int,
    samples: int,
    timeout_s: float,
    topic_prefix: str,
    domain_id: int,
    interval_ms: float = 0.0,
) -> dict[str, Any]:
    from dimos.protocol.pubsub.impl.ddspubsub import DDS, Topic

    _rebuild_dds_config()
    Probe = _make_probe_type()
    qos = _qos_cyclone(qos_kind)
    ping_topic = Topic(name=f"{topic_prefix}/ping", data_type=Probe)
    pong_topic = Topic(name=f"{topic_prefix}/pong", data_type=Probe)
    bus = DDS(qos=qos, domain_id=domain_id)
    bus.start()

    lock = threading.Lock()
    got: dict[int, int] = {}
    ev = threading.Event()
    expect_seq = -1

    def on_pong(message: Any, _topic: Any) -> None:
        now = time.perf_counter_ns()
        with lock:
            if int(message.seq) == expect_seq:
                got[int(message.seq)] = now
                ev.set()

    bus.subscribe(pong_topic, on_pong)
    time.sleep(0.5)

    payload = _payload_pattern(msg_size)
    rtt_ns: list[int] = []
    pub_ns: list[int] = []
    arrival_ns: list[int] = []
    timeouts = 0
    total = warmup + samples
    last_pub_ns: int | None = None
    for i in range(total):
        _wait_interval(last_pub_ns, interval_ms)
        ev.clear()
        with lock:
            expect_seq = i
            got.pop(i, None)
        t0 = time.perf_counter_ns()
        last_pub_ns = t0
        bus.publish(ping_topic, Probe(seq=i, t0_ns=t0, payload=payload))
        if not ev.wait(timeout=timeout_s):
            timeouts += 1
            if i >= warmup:
                pub_ns.append(t0)
            continue
        with lock:
            t1 = got.get(i)
        if t1 is None:
            timeouts += 1
            if i >= warmup:
                pub_ns.append(t0)
            continue
        if i >= warmup:
            rtt_ns.append(t1 - t0)
            pub_ns.append(t0)
            arrival_ns.append(t1)

    bus.stop()
    stats = percentiles_us(rtt_ns)
    return {
        "name": f"dds_{qos_kind}",
        "impl": "dimos.protocol.pubsub.impl.ddspubsub.DDS",
        "qos": qos_kind,
        "msg_size_bytes": msg_size,
        "payload_len_bytes": msg_size,
        "payload_field": "BenchProbe.payload (sequence[uint8]); plus seq uint32 + t0_ns uint64",
        "warmup": warmup,
        "requested_samples": samples,
        "recorded_samples": len(rtt_ns),
        "timeouts": timeouts,
        "timeout_s": timeout_s,
        "metric": "rtt",
        "units": "microseconds",
        **_case_pacing(interval_ms),
        **stats,
        **_jitter_fields(
            rtt_ns=rtt_ns,
            pub_ns=pub_ns,
            arrival_ns=arrival_ns,
            interval_ms=interval_ms,
        ),
        "rtt_us": [n / 1000.0 for n in rtt_ns],
    }


def responder_chain_b(*, qos_kind: str, topic_prefix: str, domain_id: int) -> None:
    from dimos.protocol.pubsub.impl.ddspubsub import DDS, Topic

    _rebuild_dds_config()
    Probe = _make_probe_type()
    qos = _qos_cyclone(qos_kind)
    ping_topic = Topic(name=f"{topic_prefix}/ping", data_type=Probe)
    pong_topic = Topic(name=f"{topic_prefix}/pong", data_type=Probe)
    bus = DDS(qos=qos, domain_id=domain_id)
    bus.start()

    def on_ping(message: Any, _topic: Any) -> None:
        bus.publish(pong_topic, message)

    bus.subscribe(ping_topic, on_ping)
    print("RESPONDER_READY", flush=True)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        bus.stop()


def _byte_multiarray_data(blob: bytes) -> list[bytes]:
    """Humble ``std_msgs/ByteMultiArray.data`` is ``byte[]`` (each item ``bytes``)."""
    return [bytes([b]) for b in blob]


def _blob_from_byte_multiarray(data: Any) -> bytes:
    if not data:
        return b""
    first = data[0]
    if isinstance(first, (bytes, bytearray)):
        return b"".join(data)
    return bytes(data)


def _chain_a_msg_cls(ros_msg: str) -> Any:
    if ros_msg == "uint8_multiarray":
        from std_msgs.msg import UInt8MultiArray

        return UInt8MultiArray
    from std_msgs.msg import ByteMultiArray

    return ByteMultiArray


def _chain_a_pack(ros_msg: str, blob: bytes) -> Any:
    """Build a ROS 2 multiarray. uint8 path is required at ≥100KiB (lidar-ish).

    Humble ByteMultiArray needs one Python ``bytes`` per octet and OOMs / dominates
    RTT at Feishu / lidar sizes. UInt8MultiArray takes a contiguous ``array('B')``.
    """
    if ros_msg == "uint8_multiarray":
        import array

        from std_msgs.msg import UInt8MultiArray

        msg = UInt8MultiArray()
        msg.data = array.array("B", blob)
        return msg
    from std_msgs.msg import ByteMultiArray

    msg = ByteMultiArray()
    msg.data = _byte_multiarray_data(blob)
    return msg


def _chain_a_unpack(ros_msg: str, msg: Any) -> bytes:
    if ros_msg == "uint8_multiarray":
        return bytes(msg.data)
    return _blob_from_byte_multiarray(msg.data)


def _chain_a_impl_label(ros_msg: str) -> str:
    if ros_msg == "uint8_multiarray":
        return (
            "rclpy UInt8MultiArray ping-pong (contiguous uint8; "
            "lidar/PointCloud2-like; not DimosROS library QoS rewrite)"
        )
    return "rclpy ByteMultiArray ping-pong (not DimosROS library QoS rewrite)"


def _rclpy_ensure_init() -> None:
    import rclpy

    if not rclpy.ok():
        rclpy.init()


def _rclpy_ensure_shutdown() -> None:
    import rclpy

    if rclpy.ok():
        rclpy.shutdown()


def _chain_a_qos(qos_kind: str) -> Any:
    from rclpy.qos import (
        QoSDurabilityPolicy,
        QoSHistoryPolicy,
        QoSProfile,
        QoSReliabilityPolicy,
    )

    if qos_kind == "high_throughput":
        return QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            durability=QoSDurabilityPolicy.VOLATILE,
            depth=1,
        )
    if qos_kind == "reliable":
        return QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            history=QoSHistoryPolicy.KEEP_LAST,
            durability=QoSDurabilityPolicy.VOLATILE,
            depth=5000,
        )
    raise ValueError(qos_kind)


def _chain_a_case(
    *,
    qos_kind: str,
    msg_size: int,
    warmup: int,
    samples: int,
    timeout_s: float,
    rtt_ns: list[int],
    timeouts: int,
    extra: dict[str, Any] | None = None,
    interval_ms: float = 0.0,
    ros_msg: str = "byte_multiarray",
    pub_ns: list[int] | None = None,
    arrival_ns: list[int] | None = None,
) -> dict[str, Any]:
    stats = percentiles_us(rtt_ns)
    payload = {
        "name": f"ros_{qos_kind}",
        "impl": _chain_a_impl_label(ros_msg),
        "ros_msg": ros_msg,
        "qos": qos_kind,
        "msg_size_bytes": msg_size,
        "payload_len_bytes": msg_size,
        "payload_field": (
            "UInt8MultiArray.data (uint8[]) including 12-byte seq+t0 header"
            if ros_msg == "uint8_multiarray"
            else "ByteMultiArray.data (byte[]) including 12-byte seq+t0 header"
        ),
        "warmup": warmup,
        "requested_samples": samples,
        "recorded_samples": len(rtt_ns),
        "timeouts": timeouts,
        "timeout_s": timeout_s,
        "metric": "rtt",
        "units": "microseconds",
        **_case_pacing(interval_ms),
        **stats,
        **_jitter_fields(
            rtt_ns=rtt_ns,
            pub_ns=pub_ns or [],
            arrival_ns=arrival_ns or [],
            interval_ms=interval_ms,
        ),
        "rtt_us": [n / 1000.0 for n in rtt_ns],
    }
    if extra:
        payload.update(extra)
    return payload


def run_chain_a_same_process(
    *,
    qos_kind: str,
    msg_size: int,
    warmup: int,
    samples: int,
    timeout_s: float,
    topic_prefix: str,
    interval_ms: float = 0.0,
    ros_msg: str = "byte_multiarray",
) -> dict[str, Any]:
    import rclpy

    Msg = _chain_a_msg_cls(ros_msg)
    qos = _chain_a_qos(qos_kind)
    _rclpy_ensure_init()
    node = None
    spin_stop = threading.Event()
    th: threading.Thread | None = None
    try:
        node = rclpy.create_node("hzj_bench_pingpong")
        ping_name = f"{topic_prefix}/ping"
        pong_name = f"{topic_prefix}/pong"

        lock = threading.Lock()
        got: dict[int, int] = {}
        ev = threading.Event()
        expect_seq = -1

        pub_pong = node.create_publisher(Msg, pong_name, qos)
        pub_ping = node.create_publisher(Msg, ping_name, qos)

        def on_ping(msg: Any) -> None:
            pub_pong.publish(msg)

        def on_pong(msg: Any) -> None:
            now = time.perf_counter_ns()
            blob = _chain_a_unpack(ros_msg, msg)
            if len(blob) < 12:
                return
            seq, _t0 = struct.unpack_from("<IQ", blob, 0)
            with lock:
                if seq == expect_seq:
                    got[seq] = now
                    ev.set()

        node.create_subscription(Msg, ping_name, on_ping, qos)
        node.create_subscription(Msg, pong_name, on_pong, qos)

        def spin() -> None:
            while not spin_stop.is_set() and rclpy.ok():
                rclpy.spin_once(node, timeout_sec=0.01)

        th = threading.Thread(target=spin, daemon=True)
        th.start()
        time.sleep(0.3)

        pad = bytes(i % 256 for i in range(max(0, msg_size - 12)))
        rtt_ns: list[int] = []
        pub_ns: list[int] = []
        arrival_ns: list[int] = []
        timeouts = 0
        total = warmup + samples
        last_pub_ns: int | None = None
        for i in range(total):
            _wait_interval(last_pub_ns, interval_ms)
            ev.clear()
            with lock:
                expect_seq = i
                got.pop(i, None)
            t0 = time.perf_counter_ns()
            last_pub_ns = t0
            header = struct.pack("<IQ", i, t0)
            pub_ping.publish(_chain_a_pack(ros_msg, header + pad))
            if not ev.wait(timeout=timeout_s):
                timeouts += 1
                if i >= warmup:
                    pub_ns.append(t0)
                continue
            with lock:
                t1 = got.get(i)
            if t1 is None:
                timeouts += 1
                if i >= warmup:
                    pub_ns.append(t0)
                continue
            if i >= warmup:
                rtt_ns.append(t1 - t0)
                pub_ns.append(t0)
                arrival_ns.append(t1)

        return _chain_a_case(
            qos_kind=qos_kind,
            msg_size=msg_size,
            warmup=warmup,
            samples=samples,
            timeout_s=timeout_s,
            rtt_ns=rtt_ns,
            timeouts=timeouts,
            interval_ms=interval_ms,
            ros_msg=ros_msg,
            pub_ns=pub_ns,
            arrival_ns=arrival_ns,
        )
    finally:
        spin_stop.set()
        if th is not None:
            th.join(timeout=1.0)
        if node is not None:
            node.destroy_node()
        _rclpy_ensure_shutdown()


def responder_chain_a(
    *, qos_kind: str, topic_prefix: str, ros_msg: str = "byte_multiarray"
) -> None:
    """Echo process for Chain A same-host or cross-host-UDP (role=responder)."""
    import rclpy

    Msg = _chain_a_msg_cls(ros_msg)
    qos = _chain_a_qos(qos_kind)
    _rclpy_ensure_init()
    node = rclpy.create_node(f"hzj_bench_a_responder_{os.getpid()}")
    ping_name = f"{topic_prefix}/ping"
    pong_name = f"{topic_prefix}/pong"
    pub_pong = node.create_publisher(Msg, pong_name, qos)

    def on_ping(msg: Any) -> None:
        pub_pong.publish(msg)

    node.create_subscription(Msg, ping_name, on_ping, qos)
    print("RESPONDER_READY", flush=True)
    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.01)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        _rclpy_ensure_shutdown()


def _chain_a_client_only(
    *,
    qos_kind: str,
    msg_size: int,
    warmup: int,
    samples: int,
    timeout_s: float,
    topic_prefix: str,
    interval_ms: float = 0.0,
    ros_msg: str = "byte_multiarray",
    discover_s: float = 1.2,
) -> dict[str, Any]:
    import rclpy

    Msg = _chain_a_msg_cls(ros_msg)
    qos = _chain_a_qos(qos_kind)
    _rclpy_ensure_init()
    node = None
    spin_stop = threading.Event()
    th: threading.Thread | None = None
    try:
        node = rclpy.create_node(f"hzj_bench_a_client_{os.getpid()}")
        ping_name = f"{topic_prefix}/ping"
        pong_name = f"{topic_prefix}/pong"

        lock = threading.Lock()
        got: dict[int, int] = {}
        ev = threading.Event()
        expect_seq = -1

        pub_ping = node.create_publisher(Msg, ping_name, qos)

        def on_pong(msg: Any) -> None:
            now = time.perf_counter_ns()
            blob = _chain_a_unpack(ros_msg, msg)
            if len(blob) < 12:
                return
            seq, _t0 = struct.unpack_from("<IQ", blob, 0)
            with lock:
                if seq == expect_seq:
                    got[seq] = now
                    ev.set()

        node.create_subscription(Msg, pong_name, on_pong, qos)

        def spin() -> None:
            while not spin_stop.is_set() and rclpy.ok():
                rclpy.spin_once(node, timeout_sec=0.01)

        th = threading.Thread(target=spin, daemon=True)
        th.start()
        # Discovery between two Fast-DDS participants; do not assume SHM.
        # same-host default 1.2 s; cross-host UDP may pass a longer wait.
        time.sleep(max(0.0, discover_s))

        pad = bytes(i % 256 for i in range(max(0, msg_size - 12)))
        rtt_ns: list[int] = []
        pub_ns: list[int] = []
        arrival_ns: list[int] = []
        timeouts = 0
        total = warmup + samples
        last_pub_ns: int | None = None
        for i in range(total):
            _wait_interval(last_pub_ns, interval_ms)
            ev.clear()
            with lock:
                expect_seq = i
                got.pop(i, None)
            t0 = time.perf_counter_ns()
            last_pub_ns = t0
            header = struct.pack("<IQ", i, t0)
            pub_ping.publish(_chain_a_pack(ros_msg, header + pad))
            if not ev.wait(timeout=timeout_s):
                timeouts += 1
                if i >= warmup:
                    pub_ns.append(t0)
                continue
            with lock:
                t1 = got.get(i)
            if t1 is None:
                timeouts += 1
                if i >= warmup:
                    pub_ns.append(t0)
                continue
            if i >= warmup:
                rtt_ns.append(t1 - t0)
                pub_ns.append(t0)
                arrival_ns.append(t1)

        return _chain_a_case(
            qos_kind=qos_kind,
            msg_size=msg_size,
            warmup=warmup,
            samples=samples,
            timeout_s=timeout_s,
            rtt_ns=rtt_ns,
            timeouts=timeouts,
            interval_ms=interval_ms,
            ros_msg=ros_msg,
            pub_ns=pub_ns,
            arrival_ns=arrival_ns,
        )
    finally:
        spin_stop.set()
        if th is not None:
            th.join(timeout=1.0)
        if node is not None:
            node.destroy_node()
        _rclpy_ensure_shutdown()


def run_chain_a_same_host(
    *,
    qos_kind: str,
    msg_size: int,
    warmup: int,
    samples: int,
    timeout_s: float,
    topic_prefix: str,
    interval_ms: float = 0.0,
    ros_msg: str = "byte_multiarray",
) -> dict[str, Any]:
    """Two OS processes; still one host. Responder is this file with --role responder."""
    env = os.environ.copy()
    resp = subprocess.Popen(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--chain",
            "A",
            "--role",
            "responder",
            "--topology",
            "same-host",
            "--qos",
            qos_kind,
            "--topic-prefix",
            topic_prefix,
            "--ros-msg",
            ros_msg,
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        time.sleep(1.2)
        if resp.poll() is not None:
            out = resp.stdout.read() if resp.stdout else ""
            raise RuntimeError(f"responder exited early: {out[-2000:]}")
        result = _chain_a_client_only(
            qos_kind=qos_kind,
            msg_size=msg_size,
            warmup=warmup,
            samples=samples,
            timeout_s=timeout_s,
            topic_prefix=topic_prefix,
            interval_ms=interval_ms,
            ros_msg=ros_msg,
        )
        result["responder_pid"] = resp.pid
        result["transport_label"] = (
            "same-host two processes; Fast-DDS default transports "
            "(fastdds.xml does not force UDP-only or SHM-only; do not invent SHM)"
        )
        return result
    finally:
        resp.terminate()
        try:
            resp.wait(timeout=3)
        except subprocess.TimeoutExpired:
            resp.kill()


def parse_sizes(text: str) -> list[int]:
    return [int(x) for x in text.split(",") if x.strip()]


@dataclass
class RunSpec:
    chain: str
    topology: str
    qos_list: list[str]
    sizes: list[int]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--chain", choices=("A", "B"), required=True)
    p.add_argument(
        "--topology",
        choices=("same-process", "same-host", "cross-host-UDP"),
        default="same-process",
    )
    p.add_argument("--role", choices=("client", "responder"), default="client")
    p.add_argument("--qos", default="high_throughput,reliable")
    p.add_argument("--sizes", default="64,1024,16384,65536")
    p.add_argument("--warmup", type=int, default=50)
    p.add_argument("--samples", type=int, default=400)
    p.add_argument("--timeout", type=float, default=1.0)
    p.add_argument(
        "--interval-ms",
        type=float,
        default=0.0,
        help="minimum inter-publish gap in milliseconds (0 = closed-loop only)",
    )
    p.add_argument(
        "--ros-msg",
        choices=("byte_multiarray", "uint8_multiarray"),
        default="byte_multiarray",
        help="Chain A payload type. Use uint8_multiarray for ≥100KiB (lidar-ish).",
    )
    p.add_argument("--domain-id", type=int, default=0)
    p.add_argument("--topic-prefix", default="")
    p.add_argument("--dimos-root", default=os.environ.get("TOPSUN_DIMOS", ""))
    p.add_argument("--out", default="")
    p.add_argument(
        "--remote-peer",
        default="",
        help=(
            "Other host identity for cross-host-UDP (hostname or address). "
            "Required with --role client --topology cross-host-UDP; omit to record blocked. "
            "Existing run_chain_a.sh / docker_chain_a.sh stay blocked without this flag."
        ),
    )
    p.add_argument(
        "--discover-s",
        type=float,
        default=1.2,
        help="Seconds to wait for DDS discovery before first ping (same-host default 1.2).",
    )
    p.add_argument(
        "--iceoryx",
        choices=("default", "off"),
        default="default",
        help="off: set CYCLONEDDS_URI to scripts/bench/cyclonedds_udp_lo.xml",
    )
    args = p.parse_args()

    # Default client path stays blocked so existing single-host runners do not invent
    # percentiles. Two-machine recipe: --role responder, or --role client --remote-peer.
    if (
        args.topology == "cross-host-UDP"
        and args.role != "responder"
        and not str(args.remote_peer).strip()
    ):
        payload = {
            "status": "blocked",
            "chain": args.chain,
            "topology": args.topology,
            "error": "cross-host-UDP needs a second machine; this runner is single-host",
        }
        if args.out:
            Path(args.out).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(payload, indent=2))
        return 2

    if args.iceoryx == "off":
        uri = SCRIPT_DIR / "cyclonedds_udp_lo.xml"
        os.environ["CYCLONEDDS_URI"] = f"file://{uri}"

    _ensure_dimos_path(args.dimos_root or None)

    qos_list = [x.strip() for x in args.qos.split(",") if x.strip()]
    sizes = parse_sizes(args.sizes)
    prefix = args.topic_prefix or f"hzj_bench_{os.getpid()}"

    if args.role == "responder":
        if args.chain == "B":
            responder_chain_b(
                qos_kind=qos_list[0],
                topic_prefix=prefix,
                domain_id=args.domain_id,
            )
            return 0
        if args.chain == "A":
            responder_chain_a(
                qos_kind=qos_list[0],
                topic_prefix=prefix,
                ros_msg=args.ros_msg,
            )
            return 0
        print(f"responder is not implemented for chain={args.chain}", file=sys.stderr)
        return 2

    cases: list[dict[str, Any]] = []
    errors: list[str] = []
    for qos_kind in qos_list:
        for size in sizes:
            case_prefix = f"{prefix}_{qos_kind}_{size}"
            try:
                if args.chain == "B" and args.topology == "same-process":
                    cases.append(
                        run_chain_b_same_process(
                            qos_kind=qos_kind,
                            msg_size=size,
                            warmup=args.warmup,
                            samples=args.samples,
                            timeout_s=args.timeout,
                            topic_prefix=case_prefix,
                            domain_id=args.domain_id,
                            interval_ms=args.interval_ms,
                        )
                    )
                elif args.chain == "B" and args.topology == "same-host":
                    if not args.dimos_root:
                        raise RuntimeError("same-host Chain B requires --dimos-root")
                    cases.append(
                        run_chain_b_same_host(
                            qos_kind=qos_kind,
                            msg_size=size,
                            warmup=args.warmup,
                            samples=args.samples,
                            timeout_s=args.timeout,
                            topic_prefix=case_prefix,
                            domain_id=args.domain_id,
                            dimos_root=args.dimos_root,
                            interval_ms=args.interval_ms,
                        )
                    )
                elif args.chain == "A" and args.topology == "same-process":
                    cases.append(
                        run_chain_a_same_process(
                            qos_kind=qos_kind,
                            msg_size=size,
                            warmup=args.warmup,
                            samples=args.samples,
                            timeout_s=args.timeout,
                            topic_prefix=case_prefix,
                            interval_ms=args.interval_ms,
                            ros_msg=args.ros_msg,
                        )
                    )
                elif args.chain == "A" and args.topology == "same-host":
                    cases.append(
                        run_chain_a_same_host(
                            qos_kind=qos_kind,
                            msg_size=size,
                            warmup=args.warmup,
                            samples=args.samples,
                            timeout_s=args.timeout,
                            topic_prefix=case_prefix,
                            interval_ms=args.interval_ms,
                            ros_msg=args.ros_msg,
                        )
                    )
                elif args.chain == "A" and args.topology == "cross-host-UDP":
                    # Remote responder is already running on the other host
                    # with the same --topic-prefix (do not append qos/size —
                    # a single echo process cannot rematch per-case prefixes).
                    # Do not spawn a local echo (that would be same-host).
                    case = _chain_a_client_only(
                        qos_kind=qos_kind,
                        msg_size=size,
                        warmup=args.warmup,
                        samples=args.samples,
                        timeout_s=args.timeout,
                        topic_prefix=prefix,
                        interval_ms=args.interval_ms,
                        ros_msg=args.ros_msg,
                        discover_s=args.discover_s,
                    )
                    case["transport_label"] = (
                        "cross-host-UDP two machines; Fast-DDS builtin UDP "
                        f"(remote_peer={args.remote_peer}; fastdds.xml unchanged; "
                        "do not invent SHM)"
                    )
                    cases.append(case)
                elif args.chain == "B" and args.topology == "cross-host-UDP":
                    # Same client-only helper as same-host; peer is remote.
                    # Shared --topic-prefix (not per-case). This gate's runner
                    # is Chain A; documented only, not mixed in A tables.
                    case = _chain_b_client_only(
                        qos_kind=qos_kind,
                        msg_size=size,
                        warmup=args.warmup,
                        samples=args.samples,
                        timeout_s=args.timeout,
                        topic_prefix=prefix,
                        domain_id=args.domain_id,
                        interval_ms=args.interval_ms,
                    )
                    case["transport_label"] = (
                        "cross-host-UDP two machines; Cyclone UDP domain 0 "
                        f"(remote_peer={args.remote_peer})"
                    )
                    cases.append(case)
                else:
                    raise RuntimeError(
                        f"unsupported combination chain={args.chain} topology={args.topology}"
                    )
            except Exception as exc:  # noqa: BLE001 — record and continue other cases
                errors.append(f"{qos_kind}/{size}B: {type(exc).__name__}: {exc}")
                cases.append(
                    {
                        "name": f"{'dds' if args.chain == 'B' else 'ros'}_{qos_kind}",
                        "msg_size_bytes": size,
                        "qos": qos_kind,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )

    ok_cases = [c for c in cases if "error" not in c and c.get("recorded_samples", 0) > 0]
    status = "ok" if ok_cases and not errors else ("partial" if ok_cases else "blocked")
    payload = {
        "status": status,
        "chain": args.chain,
        "topology": args.topology,
        "domain_id": args.domain_id if args.chain == "B" else int(os.environ.get("ROS_DOMAIN_ID") or 0),
        "rmw": os.environ.get("RMW_IMPLEMENTATION", ""),
        "ros_domain_id": os.environ.get("ROS_DOMAIN_ID", ""),
        "cyclonedds_uri": os.environ.get("CYCLONEDDS_URI", ""),
        "iceoryx": args.iceoryx,
        "metric": "round-trip time (ping-pong in scripts/bench/pingpong.py)",
        "units": "microseconds",
        "payload_sizes_bytes": sizes,
        "inter_message_gap_ms": args.interval_ms,
        "target_publish_hz": (
            (1000.0 / args.interval_ms) if args.interval_ms > 0 else None
        ),
        "ros_msg": args.ros_msg if args.chain == "A" else None,
        "remote_peer": (args.remote_peer or "").strip() or None,
        "discover_s": args.discover_s,
        "scale_label": (os.environ.get("BENCH_SCALE_LABEL") or "").strip() or None,
        "note": (
            "Per-message RTT from a thin wrapper. Not a root-cause claim. "
            "Do not compare Chain A and Chain B in one table. "
            "Not real-robot, Feishu-field, or cross-host proof. "
            "Upstream pytest -m tool -k dds reports throughput / drain time, not these percentiles."
        ),
        "errors": errors,
        "cases": cases,
    }
    text = json.dumps(payload, indent=2) + "\n"
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    print(text)
    return 0 if status in {"ok", "partial"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
