#!/usr/bin/env python3
"""Assert ros2-source-map.md still points at real in-tree files (wiki3 §13.2).

Vanilla box (no ROS): exit 0 when the map is healthy.
Parses only docs/architecture/ros2-source-map.md — not the rest of docs/.
No extra dependencies. Style follows scripts/prove_rmw.py.

Stale line numbers: WARN + exit 0 if the symbol still exists.
Missing file or missing allowlisted symbol: FAIL (exit 1).
"""

from __future__ import annotations

from pathlib import Path

from _md_paths import check_cited_paths, parse_map, repo_root
from _repo import emit_render


MAP_REL = Path("docs/architecture/ros2-source-map.md")

# Well-known symbols the map is about. Checked only if that file is cited.
SYMBOL_ALLOWLIST: dict[str, tuple[str, ...]] = {
    "vendor/Fast-DDS/src/cpp/rtps/history/WriterHistory.cpp": ("add_change",),
    "vendor/Fast-DDS/src/cpp/rtps/reader/StatefulReader.cpp": (
        "process_data_msg",
        "change_received",
    ),
    "vendor/Fast-DDS/src/cpp/rtps/history/ReaderHistory.cpp": (
        "received_change",
        "add_change",
    ),
    "vendor/Fast-DDS/src/cpp/fastdds/publisher/DataWriterHistory.cpp": (
        "add_pub_change",
    ),
    "vendor/rmw/rmw/include/rmw/rmw.h": (
        "rmw_publish",
        "rmw_wait",
        "rmw_take",
        "rmw_get_implementation_identifier",
    ),
    "vendor/rmw_implementation/rmw_implementation/src/functions.cpp": (
        "load_library",
    ),
    "vendor/rmw_fastrtps/rmw_fastrtps_cpp/src/identifier.cpp": (
        "rmw_fastrtps_cpp",
    ),
    "vendor/rmw_fastrtps/rmw_fastrtps_shared_cpp/src/rmw_publish.cpp": (
        "__rmw_publish",
    ),
    "vendor/rmw_fastrtps/rmw_fastrtps_shared_cpp/src/rmw_wait.cpp": (
        "__rmw_wait",
        "get_first_untaken_info",
    ),
    "vendor/rmw_fastrtps/rmw_fastrtps_shared_cpp/src/rmw_take.cpp": (
        "__rmw_take",
    ),
    "vendor/Fast-DDS/src/cpp/fastdds/core/condition/WaitSet.cpp": (
        "WaitSet::wait",
    ),
    "vendor/rmw_cyclonedds/rmw_cyclonedds_cpp/src/rmw_node.cpp": (
        "eclipse_cyclonedds_identifier",
        "rmw_wait",
        "dds_waitset_attach",
    ),
    "vendor/CycloneDDS/src/core/ddsc/src/dds_waitset.c": (
        "dds_waitset_wait",
        "dds_waitset_attach",
    ),
    "vendor/CycloneDDS/src/core/ddsc/src/dds_read.c": ("dds_take",),
    "vendor/CycloneDDS/src/core/ddsi/src/ddsi_whc.c": ("ddsi_whc_insert",),
}

def render(root: Path | None = None) -> tuple[str, int]:
    root = (root or repo_root(MAP_REL)).resolve()
    map_path = root / MAP_REL
    lines = [
        "# check_source_map (wiki3 §13.2)",
        "",
        f"- **map:** `{MAP_REL}`",
        "",
    ]
    if not map_path.is_file():
        lines.append(f"FAIL: map missing: `{MAP_REL}`")
        lines.append("")
        return "\n".join(lines), 1

    cited, notes = parse_map(root, map_path)
    if not cited:
        lines.append("FAIL: no in-repo paths extracted from the source map")
        lines.append("")
        return "\n".join(lines), 1

    failures: list[str] = []
    warnings: list[str] = []
    warnings.extend(notes)

    path_lines, ok_paths, symbol_ok = check_cited_paths(
        root, cited, SYMBOL_ALLOWLIST, failures, warnings
    )
    lines.extend(path_lines)

    lines.append("")
    lines.append(f"- **cited paths:** {len(cited)}")
    lines.append(f"- **paths on disk:** {ok_paths}")
    lines.append(f"- **allowlisted symbols ok:** {symbol_ok}")
    lines.append(f"- **warnings:** {len(warnings)}")
    lines.append("")

    if warnings:
        lines.append("Warnings (exit 0 unless a FAIL remains):")
        for item in warnings:
            lines.append(f"- {item}")
        lines.append("")

    if failures:
        lines.append("FAIL:")
        for item in failures:
            lines.append(f"- {item}")
        lines.append("")
        lines.append(
            "File or allowlisted symbol is gone. Fix the map path "
            "(docs-only) or restore the citation. Exit 1."
        )
        lines.append("")
        return "\n".join(lines), 1

    lines.append(
        "Source map healthy: cited in-repo paths exist and allowlisted "
        "symbols still appear. Stale line numbers warn only. Exit 0."
    )
    lines.append("")
    return "\n".join(lines), 0


def main() -> int:
    return emit_render(render())


if __name__ == "__main__":
    raise SystemExit(main())
