#!/usr/bin/env python3
"""Assert Executor/WaitSet/callback map still points at real files (wiki3 §13).

Vanilla box (no ROS): exit 0 when the map is healthy.
Parses only docs/architecture/feishu-executor-waitset.md — not the rest of docs/.
No extra dependencies. Style follows scripts/check_source_map.py / prove_rmw.py.

Stale line numbers: WARN + exit 0 if the symbol still exists.
Missing file, missing allowlisted symbol, missing marker/URL,
or a vendored rcl/rclcpp/rclpy tree: FAIL (exit 1).

Does not invent latencies, percentiles, or risk scores.
"""

from __future__ import annotations

from pathlib import Path

from _md_paths import check_cited_paths, parse_map, read_utf8, repo_root
from _repo import append_bullets, append_failures_block, emit_render


MAP_REL = Path("docs/architecture/feishu-executor-waitset.md")

REQUIRED_DOCS = (
    MAP_REL,
    Path("docs/architecture/ros2-source-map.md"),
    Path("docs/architecture/feishu-middleware-adr.md"),
    Path("docs/architecture/latency-attribution.md"),
    Path("docs/architecture/feishu-risk-matrix.md"),
    Path("scripts/prove_rmw.py"),
    Path("scripts/check_source_map.py"),
)

# Identity claims — not latency. Exact substrings the map must keep.
DOC_MARKERS = (
    "WaitSet",
    "rmw_wait",
    "rmw_take",
    "Humble",
    "rclcpp",
    "rclpy",
    "不在 vendor",
    "Not Feishu field proof",
    "派生自",
    "rmw_fastrtps_cpp",
    "域 **42**",
    "域 **0**",
    "dds_waitset",
    "on_data_available",
    "SingleThreadedExecutor",
    "§9.4",
)

FEISHU_URLS = (
    "https://topsunhzj.feishu.cn/wiki/N0Xaw1vsdiXRD4km9Jvc8kHynBf",
    "https://topsunhzj.feishu.cn/wiki/XKDbw7blLieO4ykCRgLcUCJKnXe",
    "https://topsunhzj.feishu.cn/docx/SrokdQU4DovvdAxutNDcXByMn5e",
)

# Humble client libraries must stay out of vendor/.
ABSENT_VENDOR_TREES = (
    Path("vendor/rcl"),
    Path("vendor/rclcpp"),
    Path("vendor/rclpy"),
)

# Well-known wait/take/callback symbols. Checked only if that file is cited.
SYMBOL_ALLOWLIST: dict[str, tuple[str, ...]] = {
    "vendor/rmw/rmw/include/rmw/rmw.h": ("rmw_wait", "rmw_take"),
    "vendor/rmw_fastrtps/rmw_fastrtps_cpp/src/rmw_wait.cpp": ("rmw_wait",),
    "vendor/rmw_fastrtps/rmw_fastrtps_shared_cpp/src/rmw_wait.cpp": (
        "__rmw_wait",
        "get_first_untaken_info",
    ),
    "vendor/rmw_fastrtps/rmw_fastrtps_shared_cpp/src/rmw_take.cpp": ("__rmw_take",),
    "vendor/Fast-DDS/src/cpp/fastdds/core/condition/WaitSet.cpp": ("WaitSet::wait",),
    "vendor/Fast-DDS/src/cpp/fastdds/core/condition/WaitSetImpl.cpp": (
        "WaitSetImpl::wait",
    ),
    "vendor/rmw_cyclonedds/rmw_cyclonedds_cpp/src/rmw_node.cpp": (
        "rmw_wait",
        "dds_waitset_attach",
        "rmw_take",
    ),
    "vendor/CycloneDDS/src/core/ddsc/src/dds_waitset.c": (
        "dds_waitset_attach",
        "dds_waitset_wait",
    ),
    "vendor/CycloneDDS/src/core/ddsc/src/dds_read.c": ("dds_take",),
    "dimos_bridge/dimos/protocol/pubsub/impl/ddspubsub.py": ("on_data_available",),
    "dimos_bridge/dimos/protocol/pubsub/impl/rospubsub.py": (
        "SingleThreadedExecutor",
    ),
}

def render(root: Path | None = None) -> tuple[str, int]:
    root = (root or repo_root(MAP_REL)).resolve()
    map_path = root / MAP_REL
    lines = [
        "# check_executor_map (wiki3 §13 wait→callback)",
        "",
        f"- **map:** `{MAP_REL}`",
        "",
    ]
    failures: list[str] = []
    warnings: list[str] = []

    for rel in REQUIRED_DOCS:
        path = root / rel
        key = rel.as_posix()
        if path.is_file():
            lines.append(f"- **ok file:** `{key}`")
        else:
            failures.append(f"missing file `{key}`")
            lines.append(f"- **FAIL missing:** `{key}`")

    for rel in ABSENT_VENDOR_TREES:
        path = root / rel
        key = rel.as_posix()
        if path.exists():
            failures.append(f"Humble client tree must not be vendored: `{key}`")
            lines.append(f"- **FAIL vendored:** `{key}`")
        else:
            lines.append(f"- **ok absent:** `{key}` (Humble rcl* not in vendor)")

    if not map_path.is_file():
        lines.append("")
        lines.append("FAIL: executor map missing")
        lines.append("")
        return "\n".join(lines), 1

    text = read_utf8(map_path)
    missing_markers = [m for m in DOC_MARKERS if m not in text]
    if missing_markers:
        joined = ", ".join(missing_markers)
        failures.append(f"map missing marker(s): {joined}")
        lines.append(f"- **FAIL markers:** `{MAP_REL}` (need {joined})")
    else:
        lines.append(f"- **ok markers:** {len(DOC_MARKERS)} identity strings")

    missing_urls = [u for u in FEISHU_URLS if u not in text]
    if missing_urls:
        failures.append("map missing Feishu URL(s)")
        for url in missing_urls:
            lines.append(f"- **FAIL Feishu URL:** `{url}`")
    else:
        lines.append(f"- **ok Feishu URLs:** {len(FEISHU_URLS)}")

    cited, notes = parse_map(
        root,
        map_path,
        absent_keys={p.as_posix() for p in ABSENT_VENDOR_TREES},
        reject_bare_words=True,
    )
    warnings.extend(notes)
    if not cited:
        failures.append("no in-repo paths extracted from the executor map")
        lines.append("- **FAIL:** no in-repo paths extracted")

    path_lines, ok_paths, symbol_ok = check_cited_paths(
        root, cited, SYMBOL_ALLOWLIST, failures, warnings
    )
    lines.extend(path_lines)

    # Allowlisted files that the map must cite (not just exist on disk).
    cited_keys = {p.as_posix() for p in cited}
    for key in SYMBOL_ALLOWLIST:
        if key not in cited_keys:
            failures.append(f"map does not cite `{key}`")
            lines.append(f"- **FAIL uncited:** `{key}`")

    lines.append("")
    lines.append(f"- **cited paths:** {len(cited)}")
    lines.append(f"- **paths on disk:** {ok_paths}")
    lines.append(f"- **allowlisted symbols ok:** {symbol_ok}")
    lines.append(f"- **warnings:** {len(warnings)}")
    lines.append("- **WaitSet -> callback: mapped**")
    lines.append("")

    if warnings:
        lines.append("Warnings (exit 0 unless a FAIL remains):")
        append_bullets(lines, warnings)
        lines.append("")

    lines.extend(
        [
            "Filesystem + identity markers only. This is **not** a latency",
            "measurement, not a percentile, and not Feishu field proof.",
            "Humble rclcpp/rclpy stay out of vendor/. Exit 0 when the map is healthy.",
            "",
        ]
    )

    if failures:
        append_failures_block(lines, failures)
        lines.append(
            "File, marker, Feishu URL, or allowlisted symbol is gone — or a "
            "Humble rcl* tree appeared under vendor/. Fix the map (docs-only) "
            "or restore the citation. Exit 1."
        )
        lines.append("")
        return "\n".join(lines), 1

    lines.append(
        "Executor map healthy: cited in-repo paths exist, allowlisted "
        "WaitSet/wait/take symbols still appear, Humble rcl* is not vendored. "
        "Stale line numbers warn only. Exit 0."
    )
    lines.append("")
    return "\n".join(lines), 0


def main() -> int:
    return emit_render(render())


if __name__ == "__main__":
    raise SystemExit(main())
