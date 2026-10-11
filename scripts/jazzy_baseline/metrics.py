"""Percentiles and /proc CPU + RSS sampling. No ROS import."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import statistics
import time
from typing import Any


def percentiles_us(samples_ns: list[int]) -> dict[str, float]:
    """Linear-interpolation percentiles in microseconds.

    Same interpolation as ``scripts/bench/pingpong.py`` so a later Rust
    worker can match the existing dual-chain math. Adds p90 (this harness
    reports p50/p90/p99/max; Humble ping-pong reports p95).
    """
    empty = {
        "p50_us": float("nan"),
        "p90_us": float("nan"),
        "p99_us": float("nan"),
        "min_us": float("nan"),
        "max_us": float("nan"),
        "mean_us": float("nan"),
        "stdev_us": float("nan"),
    }
    if not samples_ns:
        return empty
    xs = sorted(int(x) for x in samples_ns)

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
        "p90_us": pct(90),
        "p99_us": pct(99),
        "min_us": xs[0] / 1000.0,
        "max_us": xs[-1] / 1000.0,
        "mean_us": (sum(xs) / len(xs)) / 1000.0,
        "stdev_us": (statistics.pstdev(xs) / 1000.0) if len(xs) > 1 else 0.0,
    }


def clk_tck() -> float:
    try:
        return float(os.sysconf("SC_CLK_TCK"))
    except (OSError, ValueError, AttributeError):
        return 100.0


def read_cpu_jiffies(pid: int) -> int | None:
    path = Path(f"/proc/{pid}/stat")
    try:
        text = path.read_text(encoding="ascii", errors="replace")
    except (OSError, FileNotFoundError):
        return None
    # comm（字段 2）可包含空格和括号，以最后一个右括号确定边界。
    end_comm = text.rfind(")")
    if end_comm < 0:
        return None
    parts = text[end_comm + 1 :].split()
    # 剩余字段从 state（字段 3）开始，utime / stime 是索引 11 / 12。
    if len(parts) < 13:
        return None
    try:
        return int(parts[11]) + int(parts[12])
    except ValueError:
        return None


def read_rss_kb(pid: int) -> int | None:
    path = Path(f"/proc/{pid}/status")
    try:
        text = path.read_text(encoding="ascii", errors="replace")
    except (OSError, FileNotFoundError):
        return None
    for line in text.splitlines():
        if line.startswith("VmRSS:"):
            tok = line.split()
            if len(tok) >= 2:
                try:
                    return int(tok[1])
                except ValueError:
                    return None
    return None


@dataclass
class ProcSampler:
    """Start/end CPU jiffies + periodic RSS samples for one PID."""

    pid: int
    rss_kb: list[int] = field(default_factory=list)
    _t0: float = 0.0
    _j0: int | None = None
    _t1: float = 0.0
    _j1: int | None = None

    def start(self) -> None:
        self._t0 = time.monotonic()
        self._j0 = read_cpu_jiffies(self.pid)
        rss = read_rss_kb(self.pid)
        if rss is not None:
            self.rss_kb.append(rss)

    def sample(self) -> None:
        rss = read_rss_kb(self.pid)
        if rss is not None:
            self.rss_kb.append(rss)

    def stop(self) -> None:
        self._t1 = time.monotonic()
        self._j1 = read_cpu_jiffies(self.pid)
        self.sample()

    def as_dict(self) -> dict[str, Any]:
        elapsed = max(self._t1 - self._t0, 1e-9)
        cpu_pct = float("nan")
        if self._j0 is not None and self._j1 is not None:
            cpu_pct = ((self._j1 - self._j0) / clk_tck()) / elapsed * 100.0
        avg = float("nan")
        peak = float("nan")
        if self.rss_kb:
            avg = sum(self.rss_kb) / len(self.rss_kb)
            peak = float(max(self.rss_kb))
        return {
            "pid": self.pid,
            "cpu_percent": cpu_pct,
            "rss_kb_avg": avg,
            "rss_kb_peak": peak,
            "sample_count": len(self.rss_kb),
            "elapsed_s": elapsed,
            "resource_sample_start_mono_s": self._t0,
            "resource_sample_end_mono_s": self._t1,
        }
