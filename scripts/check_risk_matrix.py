#!/usr/bin/env python3
"""Assert Feishu wiki3 §9.4 risk-matrix docs + Hold markers exist.

Vanilla box (no ROS): exit 0 when required files + markers are present.
Missing required file or expected marker: FAIL (exit 1).
Does not invent risk scores or percentiles. Style follows
scripts/prove_rmw.py / scripts/print_bench_gates.py.
"""

from __future__ import annotations

from pathlib import Path
import sys

from _freeze_paths import FASTDDS_XML_REL as XML_REL, SCOREBOARD_REL


MATRIX_REL = Path("docs/architecture/feishu-risk-matrix.md")
ADR_REL = Path("docs/architecture/feishu-middleware-adr.md")
R0_REL = Path("docs/architecture/ros2-dds-r0-interface-freeze.md")
MAP_REL = Path("docs/architecture/ros2-source-map.md")
METHOD_REL = Path("docs/architecture/latency-attribution.md")
GATES_REL = Path("docs/architecture/ci-cd-gates.md")

# Layer / Hold phrases the matrix must keep. Not scores.
_MATRIX_MARKERS = (
    "§9.4",
    "env/XML",
    "RMW",
    "DDS knobs",
    "Executor",
    "core forks",
    "Hold",
    "fastdds.xml",
    "SCOREBOARD",
    "Agnocast",
    "zenoh",
    "Cega",
    "Humble",
    "Rolling",
    "blocked",
    # Hold contract is 《3》–《6》; requiring each token so a lone
    # "《3》" or "《3》–《6》" range cannot hide a missing item.
    "《3》",
    "《4》",
    "《5》",
    "《6》",
)


def _repo_root() -> Path:
    cwd = Path.cwd()
    if (cwd / MATRIX_REL).is_file() or (cwd / ADR_REL).is_file():
        return cwd.resolve()
    here = Path(__file__).resolve().parent
    candidate = here.parent
    if (candidate / MATRIX_REL).is_file() or (candidate / ADR_REL).is_file():
        return candidate
    sys.exit(f"cannot find repo root from cwd={cwd} or {candidate}")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def render(root: Path | None = None) -> tuple[str, int]:
    root = (root or _repo_root()).resolve()
    lines = [
        "# check_risk_matrix (wiki3 §9.4)",
        "",
    ]
    failures: list[str] = []

    required = (
        (MATRIX_REL, _MATRIX_MARKERS),
        (ADR_REL, ("§9.4",)),
        (R0_REL, ("Hold",)),
        (MAP_REL, ("vendor",)),
        (METHOD_REL, ("wiki",)),
        (GATES_REL, ("structure",)),
        (SCOREBOARD_REL, ("STATUS",)),
        (XML_REL, ("domainId>42",)),
    )
    for rel, markers in required:
        path = root / rel
        key = rel.as_posix()
        if not path.is_file():
            failures.append(f"missing file `{key}`")
            lines.append(f"- **FAIL missing:** `{key}`")
            continue
        text = _read(path)
        missing_markers = [m for m in markers if m not in text]
        if missing_markers:
            joined = ", ".join(missing_markers)
            failures.append(f"`{key}` missing marker(s): {joined}")
            lines.append(f"- **FAIL markers:** `{key}` (need {joined})")
            continue
        extra = ""
        if rel == SCOREBOARD_REL:
            extra = " (current-best pointer; numbers not printed)"
        elif rel == XML_REL:
            extra = " (read-only contract seed; content not edited)"
        elif rel == MATRIX_REL:
            extra = " (layer checklist; no risk scores)"
        lines.append(f"- **ok file:** `{key}`{extra}")

    matrix_path = root / MATRIX_REL
    if matrix_path.is_file():
        text = _read(matrix_path)
        has_order = all(
            token in text
            for token in ("env/XML", "RMW", "DDS knobs", "Executor", "core forks")
        )
        if has_order:
            lines.append("- **§9.4: env/XML first**")
        else:
            failures.append("§9.4 layer order markers incomplete")
            lines.append("- **FAIL order:** env/XML → RMW → DDS knobs → Executor → core forks")

    lines.append("")
    lines.extend(
        [
            "Filesystem + Hold markers only. This is **not** a risk score,",
            "not a percentile, and not Feishu field proof.",
            "Do not invent risk percentages. SCOREBOARD is the current-best",
            "**pointer**; this script does not copy its numbers.",
            "fastdds.xml is read-only; Agnocast / zenoh / Cega / custom RMW",
            "stay Hold. Rolling ≠ Humble. Cross-host stays blocked.",
            "",
        ]
    )

    if failures:
        lines.append("FAIL:")
        for item in failures:
            lines.append(f"- {item}")
        lines.append("")
        lines.append(
            "Required risk-matrix doc or Hold marker is gone. Restore the "
            "file (docs-only) or the §9.4 / Hold marker. Exit 1."
        )
        lines.append("")
        return "\n".join(lines), 1

    lines.append(
        "Risk matrix healthy: required docs + §9.4 layer/Hold markers exist. "
        "Exit 0."
    )
    lines.append("")
    return "\n".join(lines), 0


def main() -> int:
    text, code = render()
    sys.stdout.write(text)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
