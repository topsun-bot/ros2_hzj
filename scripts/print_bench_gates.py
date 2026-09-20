#!/usr/bin/env python3
"""Print whether bench attribution pointers still exist (wiki3 §12 / §13.3).

Vanilla box (no ROS): exit 0 when required files + STATUS markers are present.
Missing required file or expected marker: FAIL (exit 1).
Does not read or invent latency numbers. Style follows scripts/prove_rmw.py.
"""

from __future__ import annotations

from pathlib import Path
import re

from _freeze_paths import SCOREBOARD_REL
from _repo import append_bullets, emit_render, repo_root, read_utf8


BENCH_README_REL = Path("docs/artifacts/bench/README.md")
SCRIPTS_README_REL = Path("scripts/bench/README.md")
METHOD_REL = Path("docs/architecture/latency-attribution.md")
CROSS_HOST_REL = Path("docs/artifacts/bench/2026-09-11-cross-host")

_STATUS_BLOCKED_RE = re.compile(r"STATUS:\s*\*?\s*blocked", re.IGNORECASE)


def _has_blocked(text: str) -> bool:
    return _STATUS_BLOCKED_RE.search(text) is not None


def _cross_host_hits(root: Path) -> list[str]:
    """Return repo-relative paths whose text says STATUS: blocked."""
    hits: list[str] = []
    candidates = [
        SCOREBOARD_REL,
        BENCH_README_REL,
        CROSS_HOST_REL / "README.md",
        CROSS_HOST_REL / "summary.md",
        CROSS_HOST_REL / "BLOCKED.txt",
    ]
    for rel in candidates:
        path = root / rel
        if not path.is_file():
            continue
        if _has_blocked(read_utf8(path)):
            hits.append(rel.as_posix())
    return hits


def render(root: Path | None = None) -> tuple[str, int]:
    root = (root or repo_root(SCOREBOARD_REL, METHOD_REL)).resolve()
    lines = [
        "# print_bench_gates (wiki3 §12 / §13.3)",
        "",
    ]
    failures: list[str] = []

    required = (
        (SCOREBOARD_REL, ("STATUS",)),
        (BENCH_README_REL, ("STATUS", "SCOREBOARD")),
        (SCRIPTS_README_REL, ("cross-host",)),
        (METHOD_REL, ("wiki",)),
    )
    for rel, markers in required:
        path = root / rel
        key = rel.as_posix()
        if not path.is_file():
            failures.append(f"missing file `{key}`")
            lines.append(f"- **FAIL missing:** `{key}`")
            continue
        text = read_utf8(path)
        missing_markers = [m for m in markers if m not in text]
        if missing_markers:
            joined = ", ".join(missing_markers)
            failures.append(f"`{key}` missing marker(s): {joined}")
            lines.append(f"- **FAIL markers:** `{key}` (need {joined})")
            continue
        extra = ""
        if rel == SCOREBOARD_REL:
            extra = " (current-best pointer; numbers not printed)"
        lines.append(f"- **ok file:** `{key}`{extra}")

    cross_dir = root / CROSS_HOST_REL
    if cross_dir.is_dir():
        lines.append(f"- **ok dir:** `{CROSS_HOST_REL.as_posix()}/`")
    else:
        # Placeholder dir is expected while UDP stays blocked; missing = fail.
        failures.append(f"missing dir `{CROSS_HOST_REL.as_posix()}/`")
        lines.append(f"- **FAIL missing:** `{CROSS_HOST_REL.as_posix()}/`")

    hits = _cross_host_hits(root)
    if hits:
        lines.append(f"- **cross-host: blocked** ({', '.join(hits)})")
    else:
        failures.append("no STATUS: blocked marker for cross-host")
        lines.append("- **FAIL cross-host:** STATUS blocked marker not found")

    lines.append("")
    lines.extend(
        [
            "Filesystem + STATUS markers only. This is **not** a latency",
            "measurement, not a percentile reprint, and not Feishu field proof.",
            "Do not sum segment P99s. Same-host tables are not cross-host proof.",
            "SCOREBOARD is the current-best **pointer**; this script does not",
            "copy its numbers.",
            "",
        ]
    )

    if failures:
        lines.append("FAIL:")
        append_bullets(lines, failures)
        lines.append("")
        lines.append(
            "Required bench pointer or STATUS marker is gone. Restore the file "
            "(docs-only) or the blocked marker. Exit 1."
        )
        lines.append("")
        return "\n".join(lines), 1

    lines.append(
        "Bench gates healthy: SCOREBOARD / README pointers exist and "
        "cross-host STATUS is blocked. Exit 0."
    )
    lines.append("")
    return "\n".join(lines), 0


def main() -> int:
    return emit_render(render())


if __name__ == "__main__":
    raise SystemExit(main())
