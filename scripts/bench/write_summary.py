#!/usr/bin/env python3
"""Render summary.md from pingpong raw.json (+ optional pytest notes)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _fmt(v: object) -> str:
    if v is None:
        return "—"
    try:
        x = float(v)
    except (TypeError, ValueError):
        return str(v)
    if x != x:  # NaN
        return "—"
    if x >= 1000:
        return f"{x:.1f}"
    if x >= 10:
        return f"{x:.2f}"
    return f"{x:.3f}"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raw", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--pytest-note", default="")
    args = p.parse_args()

    raw_path = Path(args.raw)
    if not raw_path.is_file():
        Path(args.out).write_text(
            f"# {args.title}\n\nSTATUS: blocked — missing `{raw_path.name}`\n",
            encoding="utf-8",
        )
        return 1

    data = json.loads(raw_path.read_text(encoding="utf-8"))
    chain = data.get("chain", "?")
    topo = data.get("topology", "?")
    status = data.get("status", "unknown")
    lines = [
        f"# {args.title}",
        "",
        f"- **STATUS:** `{status}`",
        f"- **Chain:** `{chain}`",
        f"- **Topology:** `{topo}`",
        f"- **Metric:** {data.get('metric', 'rtt')} （单位：{data.get('units', 'microseconds')}）",
        f"- **Domain / RMW:** domain_id=`{data.get('domain_id', '')}` "
        f"RMW=`{data.get('rmw') or '(n/a)'}` ROS_DOMAIN_ID=`{data.get('ros_domain_id') or '(n/a)'}`",
        f"- **CYCLONEDDS_URI / iceoryx:** `{data.get('cyclonedds_uri') or '(unset)'}` / `{data.get('iceoryx', '')}`",
        "",
        "数字是 **ping-pong RTT**（本仓 `scripts/bench/pingpong.py` 里计时），"
        "不是中间件根因，也不是和另一条链可比的对照表。",
        "",
    ]
    if data.get("errors"):
        lines.append("## Errors")
        lines.append("")
        for err in data["errors"]:
            lines.append(f"- `{err}`")
        lines.append("")

    lines += [
        "## p50 / p95 / p99（微秒，RTT）",
        "",
        "| case | msg size | samples | timeouts | p50 (µs) | p95 (µs) | p99 (µs) | min | max |",
        "|------|----------|---------|----------|----------|----------|----------|-----|-----|",
    ]
    for case in data.get("cases", []):
        if "error" in case:
            lines.append(
                f"| `{case.get('name')}` | {case.get('msg_size_bytes', '')} B | "
                f"— | — | — | — | — | error | `{case['error']}` |"
            )
            continue
        lines.append(
            "| `{name}` | {sz} B | {n} | {to} | {p50} | {p95} | {p99} | {mn} | {mx} |".format(
                name=case.get("name", ""),
                sz=case.get("msg_size_bytes", ""),
                n=case.get("recorded_samples", 0),
                to=case.get("timeouts", 0),
                p50=_fmt(case.get("p50_us")),
                p95=_fmt(case.get("p95_us")),
                p99=_fmt(case.get("p99_us")),
                mn=_fmt(case.get("min_us")),
                mx=_fmt(case.get("max_us")),
            )
        )
    lines.append("")
    lines.append("QoS 名称对齐 `testdata.py` 预设：`high_throughput` = BestEffort/KeepLast(1)/Volatile；")
    lines.append("`reliable` = Reliable(max_blocking_time=0)/KeepLast(5000)/Volatile。")
    lines.append("这不是冻结表导航 QoS，也没有改 `ddspubsub` / `rospubsub` 默认值。")
    lines.append("")
    if args.pytest_note:
        lines += ["## Upstream pytest", "", args.pytest_note.strip(), ""]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
