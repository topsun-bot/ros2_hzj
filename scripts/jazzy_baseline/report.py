"""CSV / JSON / Markdown writers for one harness run."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from defaults import CSV_COLUMNS
from envinfo import render_md


def _fmt(v: object) -> str:
    if v is None:
        return "—"
    try:
        x = float(v)
    except (TypeError, ValueError):
        return str(v)
    if x != x:
        return "—"
    if abs(x) >= 1000:
        return f"{x:.1f}"
    if abs(x) >= 10:
        return f"{x:.2f}"
    return f"{x:.3f}"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(CSV_COLUMNS), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in CSV_COLUMNS})


def _row_md(row: dict[str, Any]) -> str:
    if row.get("status") != "ok":
        return (
            f"| `{row.get('qos', '')}` | {row.get('size_bytes', '')} | "
            f"`{row.get('mode', '')}` | — | — | — | — | — | — | — | — | "
            f"`{row.get('status', '')}` | `{row.get('blocked_reason', '')}` |"
        )
    return (
        "| `{qos}` | {sz} | `{mode}` | {hz} | {p50} | {p90} | {p99} | {mx} | "
        "{msg} | {mbs} | {loss} | {pcpu} / {scpu} | {prss} / {srss} |".format(
            qos=row.get("qos", ""),
            sz=row.get("size_bytes", ""),
            mode=row.get("mode", ""),
            hz=_fmt(row.get("hz_offered")),
            p50=_fmt(row.get("p50_us")),
            p90=_fmt(row.get("p90_us")),
            p99=_fmt(row.get("p99_us")),
            mx=_fmt(row.get("max_us")),
            msg=_fmt(row.get("throughput_msg_s")),
            mbs=_fmt(row.get("throughput_mbyte_s")),
            loss=_fmt(row.get("loss_ratio")),
            pcpu=_fmt(row.get("pub_cpu_percent")),
            scpu=_fmt(row.get("sub_cpu_percent")),
            prss=_fmt(row.get("pub_rss_kb_peak")),
            srss=_fmt(row.get("sub_rss_kb_peak")),
        )
    )


def render_summary(payload: dict[str, Any]) -> str:
    env = payload.get("environment") or {}
    rows: list[dict[str, Any]] = list(payload.get("cases") or [])
    status = payload.get("status", "unknown")
    lines = [
        "# Jazzy ROS 2 baseline summary",
        "",
        f"- **STATUS:** `{status}`",
        f"- **not_final_baseline:** `{payload.get('not_final_baseline', True)}`",
        f"- **host_class:** `{env.get('host_class', payload.get('host_class', ''))}`",
        f"- **ROS_DISTRO:** `{env.get('ros_distro', '')}`",
        f"- **topology:** `{payload.get('topology', '')}`",
        f"- **domain:** `{payload.get('domain', '')}`",
        f"- **UTC:** `{env.get('utc', '')}`",
        f"- **CPU:** `{env.get('cpu', '')}` × {env.get('nproc', '?')}",
        f"- **kernel:** `{env.get('kernel', '')}`",
        "",
        env.get(
            "disclaimer",
            "Cloud / lab measurement only. Not the final 10× denominator.",
        ),
        "",
        "Latency is one-way (same-host `CLOCK_MONOTONIC` stamp) or ping-pong RTT.",
        "Throughput is received messages after warmup ÷ measure window.",
        "CPU is process util over that window; RSS is `/proc/<pid>/status` VmRSS.",
        "",
        "Fast DDS and Cyclone stay in **separate** tables. This is not a bake-off",
        "and not a Humble dual-chain SCOREBOARD update.",
        "",
    ]
    if payload.get("blocked_reason"):
        lines += ["## Blocked", "", payload["blocked_reason"], ""]

    by_rmw: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_rmw.setdefault(str(row.get("rmw") or "?"), []).append(row)

    header = (
        "| qos | size (B) | mode | Hz | p50 (µs) | p90 (µs) | p99 (µs) | max | "
        "msg/s | MB/s | loss | CPU% pub/sub | RSS peak KiB pub/sub |"
    )
    sep = (
        "|-----|----------|------|----|----------|----------|----------|-----|"
        "------|------|------|---------------|------------------------|"
    )
    for rmw, group in by_rmw.items():
        ver = group[0].get("rmw_version") or env.get("packages", {}).get(rmw, "")
        lines += [
            f"## `{rmw}`",
            "",
            f"dpkg / recorded version: `{ver}`",
            "",
            header,
            sep,
        ]
        for row in group:
            lines.append(_row_md(row))
        lines.append("")

    if not by_rmw:
        lines += ["(no cases)", ""]

    lines += [
        "## Method",
        "",
        "- Warmup seconds are discarded before percentiles and throughput.",
        "- Same-host uses two processes and `ROS_LOCALHOST_ONLY=1` by default.",
        "- Cross-host is optional; a single VM records `STATUS: blocked`.",
        "- Repeat recommended ≥ 3 on the robot / HIL host; isolate CPUs if you can.",
        "",
    ]
    return "\n".join(lines) + "\n"


def write_reports(out_dir: Path, payload: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "results.json", payload)
    write_csv(out_dir / "results.csv", list(payload.get("cases") or []))
    (out_dir / "summary.md").write_text(render_summary(payload), encoding="utf-8")
    env = payload.get("environment") or {}
    (out_dir / "environment.md").write_text(render_md(env), encoding="utf-8")
    write_json(out_dir / "environment.json", env)
