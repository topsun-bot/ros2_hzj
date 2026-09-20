#!/usr/bin/env python3
"""Assert Feishu sink-layer (RMW/DDS/Executor) docs stay honest.

Vanilla box (no ROS): exit 0 when the sink doc + layer/Hold markers
are present. Missing file or expected marker: FAIL (exit 1).
On success print a line containing exactly:
    sink layers: mapped (Hold vs allowed)
On failure do not print that success marker.

Does not invent SHAs, percentiles, or claim Feishu was fetched live.
Does not prove fastdds.xml / SCOREBOARD contents are unchanged —
those files are existence-only here; the `boundary` job owns the freeze.
Style follows scripts/check_unitree_cyclone_swap.py / check_risk_matrix.py.
"""

from __future__ import annotations

from pathlib import Path
import re

from _freeze_paths import (
    FASTDDS_XML_REL as XML_REL,
    SCOREBOARD_EXISTENCE_NOTE,
    SCOREBOARD_REL,
    XML_EXISTENCE_NOTE,
)
from _repo import append_bullets, append_failures_block, emit_render, repo_root, read_utf8, report_missing_file


SINK_REL = Path("docs/architecture/feishu-sink-layers.md")
ADR_REL = Path("docs/architecture/feishu-middleware-adr.md")
MAP_REL = Path("docs/architecture/ros2-source-map.md")
EXEC_REL = Path("docs/architecture/feishu-executor-waitset.md")
SWAP_REL = Path("docs/architecture/unitree-sdk2-dds-swap.md")

SUCCESS_MARKER = "sink layers: mapped (Hold vs allowed)"

# Contiguous policy clauses — a lone "fastdds.xml" / "Agnocast" / "Hold"
# is not enough (a rewrite that *allows* XML could keep those names).
_POLICY_CLAUSES = (
    "不改 config/fastdds.xml / SCOREBOARD",
    "不启用 Agnocast / zenoh",
    "《3》–《6》仍 Hold",
    "AUTO ≠ 已开零拷",
    "没有 vendor/iceoryx",
)

# Table-row labels. Substring "rcl" would also match `rclpy` in the app row.
_LAYER_ROW_RE = re.compile(
    r"(?m)^\|\s*\*\*(app|rcl|rmw|DDS|executor|memory)\*\*\s*\|"
)
_LAYER_NAMES = ("app", "rcl", "rmw", "DDS", "executor", "memory")

# Exact substrings the sink doc must keep. Layers + Hold + no XML/SCOREBOARD
# rewrite + no Agnocast/zenoh. Pointers are contiguous so a lone "map"
# or "FAIL" cannot keep this gate green.
_SINK_MARKERS = (
    *_POLICY_CLAUSES,
    "Hold vs allowed",
    "eCAL",
    "DPDK",
    "Isaac",
    "Cega",
    "自定义 RMW",
    "派生自",
    "Not Feishu field proof",
    "map ≠ reproduce",
    "drop-in FAIL",
    "0.10.2",
    "11.0.1",
    "Humble",
    "Rolling",
    "blocked",
    "psmx_iox",
)

# Humble client libs + Iceoryx tree must stay out of vendor/.
# Cyclone's psmx_iox adapter source is not this list.
ABSENT_VENDOR_TREES = (
    Path("vendor/rcl"),
    Path("vendor/rclcpp"),
    Path("vendor/rclpy"),
    Path("vendor/iceoryx"),
)

_ADR_MARKERS = (
    "RMW",
    "DDS",
    "Executor",
    "内存",
)

_MAP_MARKERS = (
    "不是复现",
    "publish",
)

_EXEC_MARKERS = (
    "WaitSet",
    "callback",
)

_SWAP_MARKERS = (
    "0.10.2",
    "11.0.1",
    "drop-in FAIL",
)


def render(root: Path | None = None) -> tuple[str, int]:
    root = (root or repo_root(SINK_REL, ADR_REL)).resolve()
    lines = [
        "# check_sink_layers (Feishu RMW/DDS/Executor sink)",
        "",
    ]
    failures: list[str] = []

    # XML / SCOREBOARD: existence only. Content freeze is the `boundary` job.
    required = (
        (SINK_REL, _SINK_MARKERS, "layers + Hold vs allowed + no XML/SCOREBOARD rewrite"),
        (ADR_REL, _ADR_MARKERS, "differentiation sink still named"),
        (MAP_REL, _MAP_MARKERS, "three-chain map ≠ reproduce pointer target"),
        (EXEC_REL, _EXEC_MARKERS, "WaitSet / callback identity map"),
        (SWAP_REL, _SWAP_MARKERS, "Unitree 0.10.2 vs vendor 11.0.1 drop-in FAIL"),
        (XML_REL, (), XML_EXISTENCE_NOTE),
        (SCOREBOARD_REL, (), SCOREBOARD_EXISTENCE_NOTE),
    )
    texts: dict[Path, str] = {}
    for rel, markers, hint in required:
        path = root / rel
        key = rel.as_posix()
        if not path.is_file():
            report_missing_file(failures, lines, key)
            continue
        text = read_utf8(path)
        texts[rel] = text
        missing_markers = [m for m in markers if m not in text]
        if missing_markers:
            joined = ", ".join(missing_markers)
            failures.append(f"`{key}` missing marker(s): {joined}")
            lines.append(f"- **FAIL markers:** `{key}` (need {joined})")
            continue
        extra = f" ({hint})" if hint else ""
        lines.append(f"- **ok file:** `{key}`{extra}")

    for rel in ABSENT_VENDOR_TREES:
        path = root / rel
        key = rel.as_posix()
        if path.exists():
            failures.append(f"Hold tree must not be vendored: `{key}`")
            lines.append(f"- **FAIL vendored:** `{key}`")
        else:
            lines.append(f"- **ok absent:** `{key}`")

    sink_text = texts.get(SINK_REL)
    if sink_text is not None:
        found_layers = set(_LAYER_ROW_RE.findall(sink_text))
        missing_layers = [name for name in _LAYER_NAMES if name not in found_layers]
        if missing_layers:
            failures.append(
                "sink doc missing table-row label(s): "
                + ", ".join(f"| **{name}** |" for name in missing_layers)
            )
            lines.append(
                "- **FAIL layers:** need table rows "
                + ", ".join(f"| **{name}** |" for name in missing_layers)
            )
        else:
            lines.append(
                "- **ok layers:** table rows | **app** | **rcl** | **rmw** | "
                "**DDS** | **executor** | **memory** |"
            )
        missing_policy = [c for c in _POLICY_CLAUSES if c not in sink_text]
        if missing_policy:
            joined = ", ".join(f"`{c}`" for c in missing_policy)
            failures.append(f"sink doc missing policy clause(s): {joined}")
            lines.append(f"- **FAIL policy:** need {joined}")
        else:
            lines.append(
                "- **ok policy:** 不改 XML/SCOREBOARD; 不启用 Agnocast/zenoh; "
                "《3》–《6》仍 Hold; AUTO ≠ 已开零拷; 没有 vendor/iceoryx"
            )
        if "Hold vs allowed" in sink_text:
            lines.append("- **ok Hold vs allowed:** contiguous phrase present")
        else:
            failures.append("sink doc missing contiguous `Hold vs allowed`")
            lines.append("- **FAIL Hold vs allowed:** need contiguous phrase")
        if "map ≠ reproduce" in sink_text:
            lines.append("- **ok three-chain pointer:** `map ≠ reproduce`")
        else:
            failures.append("sink doc missing contiguous `map ≠ reproduce`")
            lines.append("- **FAIL three-chain:** need `map ≠ reproduce`")
        if "drop-in FAIL" in sink_text:
            lines.append("- **ok Unitree pointer:** `drop-in FAIL`")
        else:
            failures.append("sink doc missing contiguous `drop-in FAIL`")
            lines.append("- **FAIL Unitree pointer:** need `drop-in FAIL`")

    lines.append("")
    lines.extend(
        [
            "Filesystem + Hold markers only. This is **not** a loaded",
            "`.so` proof, not a percentile, and not Feishu field proof.",
            "Live Feishu was not fetched; the sink doc must stay derived",
            "from the in-repo ADR + source map + executor map.",
            "fastdds.xml / SCOREBOARD are existence-only in this script;",
            "the boundary job owns the content freeze. Agnocast / zenoh",
            "stay Hold. Three-chain stays map ≠ reproduce. Unitree 0.10.2",
            "vs vendor 11.0.1 stays drop-in FAIL. Do not rewrite XML.",
            "",
        ]
    )

    if failures:
        append_failures_block(lines, failures)
        lines.append(
            "Required sink-layer doc, layer/Hold marker, no-XML/SCOREBOARD "
            "marker, or Agnocast/zenoh Hold is gone. Restore the docs "
            "(no XML) or the marker. Exit 1."
        )
        lines.append("")
        return "\n".join(lines), 1

    lines.append(f"- **{SUCCESS_MARKER}**")
    lines.append("")
    lines.append(
        "Sink-layer record healthy: app / rcl / rmw / DDS / executor / "
        "memory stay marked Hold vs allowed; Agnocast / zenoh stay Hold. "
        "fastdds.xml / SCOREBOARD are existence-only here — the boundary "
        "job owns the content freeze. Exit 0."
    )
    lines.append("")
    return "\n".join(lines), 0


def main() -> int:
    return emit_render(render())


if __name__ == "__main__":
    raise SystemExit(main())
