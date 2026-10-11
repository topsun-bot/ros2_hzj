"""CSV / JSON / Markdown writers for one harness run."""

from __future__ import annotations

import csv
from collections import Counter
import json
import math
from pathlib import Path
import statistics
from typing import Any

from defaults import CSV_COLUMNS
from envinfo import render_md

GROUP_COLUMNS = (
    "rmw", "rmw_version", "host_class", "ros_distro", "topology", "qos",
    "mode", "size_bytes", "hz_offered", "duration_s", "warmup_s",
)
REPEAT_METRICS = (
    "p50_us", "p99_us", "max_us", "throughput_msg_s", "throughput_mbyte_s",
    "pub_cpu_percent", "sub_cpu_percent", "pub_rss_kb_peak", "sub_rss_kb_peak",
)
STAT_COLUMNS = ("n", "mean", "sample_stdev", "min", "max", "cv")


def _json_safe(value: Any) -> Any:
    """Represent unavailable measurements as JSON null, never NaN/Infinity."""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return value


def _finite(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def summarize_repeats(payload: dict[str, Any]) -> dict[str, Any]:
    """Summarize variability of run-level metrics, without pooling quantiles."""
    expected = payload.get("expected_repeats")
    if not _positive_int(expected):
        expected = None
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in payload.get("cases") or []:
        grouped.setdefault(tuple(row.get(k) for k in GROUP_COLUMNS), []).append(row)
    groups = []
    for key, rows in grouped.items():
        warnings = []
        missing_keys = [k for k, value in zip(GROUP_COLUMNS, key) if value is None or value == ""]
        if missing_keys:
            warnings.append(f"missing grouping fields: {missing_keys}")
        if expected is None:
            warnings.append("expected_repeats missing or invalid")
        ids = Counter(row.get("repeat") for row in rows if _positive_int(row.get("repeat")))
        duplicates = sorted(i for i, n in ids.items() if n > 1)
        if duplicates:
            warnings.append(f"duplicate repeat IDs excluded: {duplicates}")
        invalid_ids = sum(not _positive_int(row.get("repeat")) for row in rows)
        if invalid_ids:
            warnings.append(f"missing or invalid repeat IDs: {invalid_ids}")
        failed = [row for row in rows if row.get("status") != "ok"]
        for row in failed:
            warnings.append(
                f"repeat {row.get('repeat')}: status={row.get('status', 'missing')}; "
                f"{row.get('blocked_reason') or 'no failure detail'}"
            )
        eligible = [
            row for row in rows if row.get("status") == "ok"
            and _positive_int(row.get("repeat")) and ids[row["repeat"]] == 1
        ]
        successful_ids = sorted(row["repeat"] for row in eligible)
        missing = sorted(set(range(1, expected + 1)) - set(successful_ids)) if expected else []
        unexpected = sorted(set(ids) - set(range(1, expected + 1))) if expected else []
        if missing:
            warnings.append(f"missing successful repeats: {missing}")
        if unexpected:
            warnings.append(f"unexpected repeat IDs: {unexpected}")
        valid = [row for row in eligible if all(_finite(row.get(m)) for m in REPEAT_METRICS)]
        if len(valid) < 3:
            warnings.append(f"at least 3 fully measured unique successful repeats required; got {len(valid)}")
        stats = {}
        for metric in REPEAT_METRICS:
            xs = [float(row[metric]) for row in eligible if _finite(row.get(metric))]
            rejected = [row["repeat"] for row in eligible if not _finite(row.get(metric))]
            if rejected:
                warnings.append(f"{metric}: missing/non-finite/non-numeric values in repeats {rejected}")
            mean = statistics.mean(xs) if xs else None
            sd = statistics.stdev(xs) if len(xs) >= 2 else None
            stats[metric] = {
                "n": len(xs), "mean": mean, "sample_stdev": sd,
                "min": min(xs) if xs else None, "max": max(xs) if xs else None,
                "cv": sd / abs(mean) if sd is not None and mean else None,
            }
            if any(v is not None and not _finite(v) for v in stats[metric].values()):
                warnings.append(f"{metric}: non-finite aggregate statistic")
        successful = sum(row.get("status") == "ok" for row in rows)
        complete = expected is not None and not warnings and len(valid) >= max(3, expected)
        groups.append({
            **dict(zip(GROUP_COLUMNS, key)),
            "status": "complete" if complete else ("partial" if successful else "blocked"),
            "expected_repeats": expected,
            "observed_runs": len(rows), "successful_runs": successful,
            "valid_successful_runs": len(valid), "successful_repeat_ids": successful_ids,
            "missing_successful_repeat_ids": missing, "duplicate_repeat_ids": duplicates,
            "warnings": warnings, "metrics": stats,
        })
    return _json_safe({
        "status": (
            "complete" if groups and all(g["status"] == "complete" for g in groups)
            else "partial" if any(g["successful_runs"] for g in groups) else "blocked"
        ),
        "not_final_baseline": True,
        "expected_repeats": expected,
        "method": "Across-run statistics of each run's metric; percentiles are not pooled.",
        "warnings": [] if groups else ["no cases to summarize"],
        "groups": groups,
    })


def write_repeats_csv(path: Path, summary: dict[str, Any]) -> None:
    columns = GROUP_COLUMNS + (
        "status", "expected_repeats", "observed_runs", "successful_runs",
        "valid_successful_runs", "warnings", "metric",
    ) + STAT_COLUMNS
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for group in summary["groups"]:
            for metric, stats in group["metrics"].items():
                writer.writerow({**group, "warnings": "; ".join(group["warnings"]), "metric": metric, **stats})


def _cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def _repeats_md(summary: dict[str, Any]) -> list[str]:
    lines = [
        "## 重复运行的波动", "",
        f"- 汇总状态：`{summary['status']}`；预期重复数：`{summary['expected_repeats']}`。",
        "- 以下统计针对各次运行的指标值；p50/p99 的均值不是合并样本后的总体分位数。",
        "- sample_stdev 为样本标准差（n−1）；CV = sample_stdev / |mean|。",
        "- n < 2 时标准差与 CV 不可用；mean = 0 时 CV 不可用，以 — / JSON null 表示。",
        "- 至少 3 次成功、编号唯一、指标完整，且达到预期重复数，才标记 complete。",
        "- 重复编号的全部记录、失败记录不参与统计；缺失或非有限指标逐项排除并报告。",
        "- complete 仅表示此参数组的重复统计完整，不表示全矩阵、全部拓扑或最终基线验收完成。",
        "",
    ]
    for warning in summary["warnings"]:
        lines += [f"- 警告：{_cell(warning)}", ""]
    for i, group in enumerate(summary["groups"], 1):
        lines += [f"### 参数组 {i}", ""]
        lines += [" / ".join(f"{k}=`{_cell(group[k])}`" for k in GROUP_COLUMNS), ""]
        lines += [
            f"状态 `{group['status']}`；成功 {group['successful_runs']} / 预期 {group['expected_repeats']}；"
            f"指标完整且编号唯一 {group['valid_successful_runs']}；观测记录 {group['observed_runs']}。",
            "",
        ]
        for warning in group["warnings"]:
            lines.append(f"- 警告：{_cell(warning)}")
        lines += ["", "| metric | n | mean | sample_stdev | min | max | CV |", "|---|---|---|---|---|---|---|"]
        for metric, stats in group["metrics"].items():
            lines.append("| " + " | ".join([f"`{metric}`", str(stats["n"])] + [_fmt(stats[k]) for k in STAT_COLUMNS[1:]]) + " |")
        lines.append("")
    return lines


def _fmt(v: object) -> str:
    if v is None:
        return "—"
    try:
        x = float(v)
    except (TypeError, ValueError):
        return str(v)
    if not math.isfinite(x):
        return "—"
    if abs(x) >= 1000:
        return f"{x:.1f}"
    if abs(x) >= 10:
        return f"{x:.2f}"
    return f"{x:.3f}"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_json_safe(payload), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(CSV_COLUMNS), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in CSV_COLUMNS})


def _row_md(row: dict[str, Any]) -> str:
    cells = [row.get("repeat", ""), row.get("qos", ""), row.get("size_bytes", ""), row.get("mode", ""), _fmt(row.get("hz_offered"))]
    if row.get("status") == "ok":
        cells += [_fmt(row.get(k)) for k in ("p50_us", "p90_us", "p99_us", "max_us", "throughput_msg_s", "throughput_mbyte_s", "loss_ratio")]
        cells += [f"{_fmt(row.get('pub_cpu_percent'))} / {_fmt(row.get('sub_cpu_percent'))}"]
        cells += [f"{_fmt(row.get('pub_rss_kb_peak'))} / {_fmt(row.get('sub_rss_kb_peak'))}"]
    else:
        cells += ["—"] * 9
    cells += [row.get("status", ""), row.get("blocked_reason", "")]
    return "| " + " | ".join(_cell(cell) for cell in cells) + " |"


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
        "| repeat | qos | size (B) | mode | Hz | p50 (µs) | p90 (µs) | p99 (µs) | max | "
        "msg/s | MB/s | loss | CPU% pub/sub | RSS peak KiB pub/sub | status | reason |"
    )
    sep = (
        "|-----|-----|----------|------|----|----------|----------|----------|-----|"
        "------|------|------|---------------|------------------------|--------|--------|"
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

    lines += _repeats_md(summarize_repeats(payload))

    lines += [
        "## Method",
        "",
        "- Warmup seconds are discarded before percentiles and throughput.",
        "- Same-host uses two processes; the default configuration sets `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` (see each processes.json for the effective environment).",
        "- 同进程、跨进程、跨机均为任务要求；same-host 结果只覆盖本机跨进程。",
        "- 每组至少重复 3 次并检查波动汇总；smoke 运行不满足完整基线验收。",
        "",
    ]
    return "\n".join(lines) + "\n"


def write_reports(out_dir: Path, payload: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "results.json", payload)
    write_csv(out_dir / "results.csv", list(payload.get("cases") or []))
    repeats = summarize_repeats(payload)
    write_json(out_dir / "repeats.json", repeats)
    write_repeats_csv(out_dir / "repeats.csv", repeats)
    (out_dir / "summary.md").write_text(render_summary(payload), encoding="utf-8")
    env = payload.get("environment") or {}
    (out_dir / "environment.md").write_text(render_md(env), encoding="utf-8")
    write_json(out_dir / "environment.json", env)
