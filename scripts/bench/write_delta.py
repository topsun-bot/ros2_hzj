#!/usr/bin/env python3
"""Like-to-like delta.md between two ping-pong raw.json files (same chain+topology)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _pct(v: object) -> float | None:
    try:
        x = float(v)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if x != x:
        return None
    return x


def _fmt(v: float | None) -> str:
    if v is None:
        return "—"
    if abs(v) >= 1000:
        return f"{v:.1f}"
    if abs(v) >= 10:
        return f"{v:.2f}"
    return f"{v:.3f}"


def _key(case: dict) -> tuple:
    return (
        case.get("name"),
        int(case.get("payload_len_bytes") or case.get("msg_size_bytes") or -1),
        case.get("qos"),
    )


def load_cases(path: Path) -> tuple[dict, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    cases = {}
    for case in data.get("cases", []):
        if "error" in case:
            continue
        cases[_key(case)] = case
    return data, cases


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base", required=True, help="baseline raw.json")
    p.add_argument("--after", required=True, help="after-change raw.json")
    p.add_argument("--out", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--notes", default="")
    args = p.parse_args()

    base_raw, base_cases = load_cases(Path(args.base))
    after_raw, after_cases = load_cases(Path(args.after))
    if base_raw.get("chain") != after_raw.get("chain"):
        raise SystemExit("refusing to delta different chains")
    if base_raw.get("topology") != after_raw.get("topology"):
        raise SystemExit("refusing to delta different topologies")

    keys = [k for k in base_cases if k in after_cases]
    lines = [
        f"# {args.title}",
        "",
        f"- **Chain:** `{base_raw.get('chain')}` (only this chain)",
        f"- **Topology:** `{base_raw.get('topology')}`",
        f"- **Metric:** ping-pong RTT microseconds. Δ = after − baseline. Negative = faster.",
        f"- **Payload sizes:** `{base_raw.get('payload_sizes_bytes')}`",
        f"- **Inter-message gap:** `{base_raw.get('inter_message_gap_ms')}` ms",
        "",
        "Like-to-like only (same chain, topology, sizes, gap, runner). "
        "Do **not** mix Chain A and Chain B. "
        "Not real-robot / Feishu-field / cross-host proof.",
        "",
    ]
    if args.notes:
        lines += [args.notes.strip(), ""]
    lines += [
        "| case | payload (B) | p50 base → after | Δ p50 | p50 % | p95 base → after | Δ p95 | p95 % | p99 base → after | Δ p99 | p99 % |",
        "|------|-------------|------------------|-------|-------|------------------|-------|-------|------------------|-------|-------|",
    ]
    for key in keys:
        b, a = base_cases[key], after_cases[key]
        row = [f"`{key[0]}`", str(key[1])]
        for stat in ("p50_us", "p95_us", "p99_us"):
            bv, av = _pct(b.get(stat)), _pct(a.get(stat))
            if bv is None or av is None:
                row += ["—", "—", "—"]
                continue
            delta = av - bv
            pct = (delta / bv * 100.0) if bv else float("nan")
            row += [
                f"{_fmt(bv)} → {_fmt(av)}",
                _fmt(delta),
                f"{pct:+.2f}%" if pct == pct else "—",
            ]
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
