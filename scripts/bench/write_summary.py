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
        f"- **Payload sizes (bytes):** `{data.get('payload_sizes_bytes') or 'see cases'}`",
        f"- **Inter-message gap:** `{data.get('inter_message_gap_ms', 0)}` ms"
        + (
            f" (target `{data.get('target_publish_hz')}` Hz)"
            if data.get("target_publish_hz")
            else " (closed-loop only)"
        ),
        f"- **Scale:** `{data.get('scale_label') or '(n/a)'}`",
        f"- **Primary metric:** jitter (RTT p95/p99 + inter-message interval variance). "
        "Do **not** claim success from p50/mean alone.",
        f"- **Chain A ros_msg:** `{data.get('ros_msg') or '(n/a)'}`",
        "",
        "数字是 **ping-pong RTT 与 inter-message interval**（本仓 `scripts/bench/pingpong.py` 里计时），"
        "不是中间件根因，也不是和另一条链可比的对照表。"
        " **不是** 飞书现场 / 实机 / 跨机根因证明。",
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
        "| case | payload (B) | gap (ms) | samples | timeouts | p50 (µs) | p95 (µs) | p99 (µs) | min | max |",
        "|------|-------------|----------|---------|----------|----------|----------|----------|-----|-----|",
    ]
    for case in data.get("cases", []):
        if "error" in case:
            lines.append(
                f"| `{case.get('name')}` | {case.get('payload_len_bytes', case.get('msg_size_bytes', ''))} B | "
                f"{case.get('inter_message_gap_ms', '')} | "
                f"— | — | — | — | — | error | `{case['error']}` |"
            )
            continue
        lines.append(
            "| `{name}` | {sz} B | {gap} | {n} | {to} | {p50} | {p95} | {p99} | {mn} | {mx} |".format(
                name=case.get("name", ""),
                sz=case.get("payload_len_bytes", case.get("msg_size_bytes", "")),
                gap=case.get("inter_message_gap_ms", data.get("inter_message_gap_ms", "")),
                n=case.get("recorded_samples", 0),
                to=case.get("timeouts", 0),
                p50=_fmt(case.get("p50_us")),
                p95=_fmt(case.get("p95_us")),
                p99=_fmt(case.get("p99_us")),
                mn=_fmt(case.get("min_us")),
                mx=_fmt(case.get("max_us")),
            )
        )
    lines += [
        "",
        "## Jitter（主指标：RTT 尾 + inter-message interval）",
        "",
        "Do **not** read p50/mean as success. "
        "`pub_interval` = consecutive post-warmup publish times (includes timed-out publishes). "
        "`arrival_interval` = consecutive successful pong times. "
        "`jitter_abs` = |interval − target gap|. "
        "`rfc3550` = running mean of |Δinterval|.",
        "",
        "| case | payload (B) | RTT p95−p50 | RTT p99−p50 | RTT stdev | "
        "pub I p50 | pub I stdev | pub |I−tgt| p95 | pub |I−tgt| p99 | pub rfc3550 | "
        "arr I stdev | arr |I−tgt| p95 | arr |I−tgt| p99 |",
        "|------|-------------|-------------|-------------|-----------|"
        "-----------|-------------|---------------|---------------|-------------|"
        "-------------|---------------|---------------|",
    ]
    for case in data.get("cases", []):
        if "error" in case:
            lines.append(
                f"| `{case.get('name')}` | {case.get('payload_len_bytes', case.get('msg_size_bytes', ''))} B | "
                f"— | — | — | — | — | — | — | — | — | — | — |"
            )
            continue
        lines.append(
            "| `{name}` | {sz} B | {j95} | {j99} | {st} | "
            "{pp50} | {pst} | {pj95} | {pj99} | {prfc} | "
            "{ast} | {aj95} | {aj99} |".format(
                name=case.get("name", ""),
                sz=case.get("payload_len_bytes", case.get("msg_size_bytes", "")),
                j95=_fmt(case.get("rtt_jitter_p95_minus_p50_us")),
                j99=_fmt(case.get("rtt_jitter_p99_minus_p50_us")),
                st=_fmt(case.get("rtt_stdev_us") or case.get("stdev_us")),
                pp50=_fmt(case.get("pub_interval_p50_us")),
                pst=_fmt(case.get("pub_interval_stdev_us")),
                pj95=_fmt(case.get("pub_interval_jitter_abs_p95_us")),
                pj99=_fmt(case.get("pub_interval_jitter_abs_p99_us")),
                prfc=_fmt(case.get("pub_interval_jitter_rfc3550_us")),
                ast=_fmt(case.get("arrival_interval_stdev_us")),
                aj95=_fmt(case.get("arrival_interval_jitter_abs_p95_us")),
                aj99=_fmt(case.get("arrival_interval_jitter_abs_p99_us")),
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
