"""Defaults for the Jazzy FastDDS / Cyclone ROS 2 baseline harness.

This is the 10×-denominator tool for a future Rust RMW. It is **not** the
Humble dual-chain SCOREBOARD and must not rewrite ``config/fastdds.xml``.
"""

from __future__ import annotations

# Dedicated domain so a leftover Chain A (42) / Chain B (0) session cannot
# join this run. Operators may override with --domain / ROS_DOMAIN_ID.
DEFAULT_DOMAIN = 87

DEFAULT_RMWS = ("rmw_fastrtps_cpp", "rmw_cyclonedds_cpp")
DEFAULT_SIZES = (1024, 65536, 1048576, 4194304)
DEFAULT_QOS = ("reliable", "best_effort")
DEFAULT_MODES = ("oneway",)
DEFAULT_TOPOLOGY = "same-host"

# Per-size offered rate when --hz is omitted. 4 MiB at 100 Hz would saturate
# a shared cloud vCPU and is not a useful default.
DEFAULT_HZ_BY_SIZE = {
    1024: 100.0,
    65536: 50.0,
    1048576: 10.0,
    4194304: 2.0,
}
DEFAULT_HZ_FALLBACK = 10.0

DEFAULT_DURATION_S = 10.0
DEFAULT_WARMUP_S = 2.0
DEFAULT_REPEATS = 3
DEFAULT_DISCOVER_S = 15.0
DEFAULT_MARGIN_S = 3.0

SMOKE_SIZES = (1024, 65536)
SMOKE_QOS = ("reliable",)
SMOKE_DURATION_S = 2.0
SMOKE_WARMUP_S = 0.5
SMOKE_REPEATS = 1
SMOKE_HZ = 20.0

# 16-byte little-endian header: magic u32 + seq u32 + t0_ns u64.
HEADER_SIZE = 16
WIRE_MAGIC = 0x4A5A4253  # "JZBS"

TOPIC_DATA = "data"
TOPIC_ECHO = "echo"

CSV_COLUMNS = (
    "status",
    "not_final_baseline",
    "host_class",
    "ros_distro",
    "rmw",
    "rmw_version",
    "qos",
    "mode",
    "topology",
    "size_bytes",
    "hz_offered",
    "duration_s",
    "warmup_s",
    "repeat",
    "sent",
    "received",
    "loss_ratio",
    "throughput_msg_s",
    "throughput_mbyte_s",
    "p50_us",
    "p90_us",
    "p99_us",
    "max_us",
    "min_us",
    "mean_us",
    "pub_cpu_percent",
    "sub_cpu_percent",
    "pub_rss_kb_avg",
    "pub_rss_kb_peak",
    "sub_rss_kb_avg",
    "sub_rss_kb_peak",
    "pub_pid",
    "sub_pid",
    "blocked_reason",
)


def hz_for_size(size_bytes: int, override: float | None) -> float:
    if override is not None:
        if override <= 0:
            raise ValueError("hz must be > 0")
        return float(override)
    return float(DEFAULT_HZ_BY_SIZE.get(int(size_bytes), DEFAULT_HZ_FALLBACK))
