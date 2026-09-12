#!/usr/bin/env python3
"""Assert Feishu wiki3 §13(3) dual-chain baseline pointer docs stay honest.

Vanilla box (no ROS): exit 0 when the baseline doc + dual-chain contract
scripts + ADR §13(3) pointer markers are present.
Missing file or expected marker: FAIL (exit 1).
On success print a line containing exactly:
  dual-chain baseline: pointer only (no XML rewrite)
and a line containing exactly:
  same-topology XML tuning is paused
On failure do not print those success markers.

Does not invent percentiles. Does not prove fastdds.xml / SCOREBOARD
contents are unchanged — those files are existence-only here; the
`boundary` job owns the freeze.
Style follows scripts/check_unitree_cyclone_swap.py / check_risk_matrix.py.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys


BASELINE_REL = Path("docs/architecture/feishu-dual-chain-baseline.md")
ADR_REL = Path("docs/architecture/feishu-middleware-adr.md")
CHAIN_A_REL = Path("config/env/chain_a.sh")
CHAIN_B_REL = Path("config/env/chain_b.sh")
XML_REL = Path("config/fastdds.xml")
SCOREBOARD_REL = Path("docs/artifacts/bench/SCOREBOARD.md")
R0_REL = Path("docs/architecture/ros2-dds-r0-interface-freeze.md")
MAP_REL = Path("docs/architecture/ros2-source-map.md")
SWAP_REL = Path("docs/architecture/unitree-sdk2-dds-swap.md")

SUCCESS_MARKER = "dual-chain baseline: pointer only (no XML rewrite)"
PAUSED_MARKER = "same-topology XML tuning is paused"
MAP_VERDICT = "map≠reproduce"
NO_REWRITE = "no XML rewrite"

# Contiguous phrases so a lone "pointer" / "blocked" / "Hold" cannot
# keep this gate green. Not scores, not percentiles.
_BASELINE_MARKERS = (
    "§13",
    "rmw_fastrtps_cpp",
    "ROS_DOMAIN_ID=42",
    "chain_a.sh",
    "fastdds.xml",
    "只读",
    "rmw_cyclonedds_cpp",
    "域 0",
    "chain_b.sh",
    "CYCLONEDDS_URI",
    "SCOREBOARD",
    "pointer only",
    PAUSED_MARKER,
    NO_REWRITE,
    "STATUS: blocked",
    "cross-host",
    "three-chain",
    MAP_VERDICT,
    "drop-in FAIL",
    "0.10.2",
    "11.0.1",
    "派生自",
    "Not Feishu field proof",
    "《3》",
    "《4》",
    "《5》",
    "《6》",
    "Hold",
)

# ADR §13(3) must keep the no-rewrite contract and point at this cut.
_ADR_MARKERS = (
    "FastDDS + Cyclone",
    "不重写 XML",
    "SCOREBOARD",
    "feishu-dual-chain-baseline.md",
)

_CHAIN_A_MARKERS = (
    "rmw_fastrtps_cpp",
    "ROS_DOMAIN_ID=42",
    "FASTRTPS_DEFAULT_PROFILES_FILE",
)

_CHAIN_B_MARKERS = (
    "rmw_cyclonedds_cpp",
    "ROS_DOMAIN_ID=0",
    "CYCLONEDDS_URI",
)

_PERCENTILE_RE = re.compile(r"\bp(?:50|95|99)\b", re.IGNORECASE)
_EXPORT_CYCLONE_URI_RE = re.compile(
    r"(?m)^\s*export\s+CYCLONEDDS_URI\s*="
)


def _repo_root() -> Path:
    cwd = Path.cwd()
    if (cwd / BASELINE_REL).is_file() or (cwd / ADR_REL).is_file():
        return cwd.resolve()
    here = Path(__file__).resolve().parent
    candidate = here.parent
    if (candidate / BASELINE_REL).is_file() or (candidate / ADR_REL).is_file():
        return candidate
    sys.exit(f"cannot find repo root from cwd={cwd} or {candidate}")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def render(root: Path | None = None) -> tuple[str, int]:
    root = (root or _repo_root()).resolve()
    lines = [
        "# check_dual_chain_baseline (wiki3 §13(3) FastDDS + Cyclone)",
        "",
    ]
    failures: list[str] = []

    # XML / SCOREBOARD: existence only. Content freeze is the `boundary` job.
    required = (
        (BASELINE_REL, _BASELINE_MARKERS, "dual-chain contracts + Hold + pointer-only"),
        (ADR_REL, _ADR_MARKERS, "§13(3) row pointer; no XML rewrite"),
        (CHAIN_A_REL, _CHAIN_A_MARKERS, "chain A contract strings"),
        (CHAIN_B_REL, _CHAIN_B_MARKERS, "chain B contract strings; no URI export"),
        (R0_REL, ("Hold",), "dual-chain R0 freeze exists"),
        (MAP_REL, ("vendor",), "three-chain map exists (map≠reproduce)"),
        (SWAP_REL, ("drop-in FAIL",), "Unitree 0.10.2 vs vendor 11.0.1"),
        (XML_REL, (), "existence only; content freeze is boundary"),
        (SCOREBOARD_REL, (), "existence only; numbers not read; freeze is boundary"),
    )
    texts: dict[Path, str] = {}
    for rel, markers, hint in required:
        path = root / rel
        key = rel.as_posix()
        if not path.is_file():
            failures.append(f"missing file `{key}`")
            lines.append(f"- **FAIL missing:** `{key}`")
            continue
        text = _read(path)
        texts[rel] = text
        missing_markers = [m for m in markers if m not in text]
        if missing_markers:
            joined = ", ".join(missing_markers)
            failures.append(f"`{key}` missing marker(s): {joined}")
            lines.append(f"- **FAIL markers:** `{key}` (need {joined})")
            continue
        extra = f" ({hint})" if hint else ""
        lines.append(f"- **ok file:** `{key}`{extra}")

    baseline_text = texts.get(BASELINE_REL)
    if baseline_text is not None:
        if PAUSED_MARKER in baseline_text:
            lines.append(f"- **ok paused phrase:** `{PAUSED_MARKER}`")
        else:
            failures.append(f"baseline doc missing contiguous `{PAUSED_MARKER}`")
            lines.append(f"- **FAIL paused:** need `{PAUSED_MARKER}`")
        if MAP_VERDICT in baseline_text:
            lines.append(f"- **ok three-chain phrase:** `{MAP_VERDICT}`")
        else:
            failures.append(f"baseline doc missing contiguous `{MAP_VERDICT}`")
            lines.append(f"- **FAIL map:** need `{MAP_VERDICT}`")
        if NO_REWRITE in baseline_text:
            lines.append(f"- **ok no-rewrite phrase:** `{NO_REWRITE}`")
        else:
            failures.append(f"baseline doc missing contiguous `{NO_REWRITE}`")
            lines.append(f"- **FAIL rewrite:** need `{NO_REWRITE}`")
        if "pointer only" in baseline_text:
            lines.append("- **ok SCOREBOARD phrase:** `pointer only`")
        else:
            failures.append("baseline doc missing SCOREBOARD `pointer only`")
            lines.append("- **FAIL pointer:** need `pointer only`")
        invented = _PERCENTILE_RE.findall(baseline_text)
        if invented:
            failures.append(
                "baseline doc invents percentile token(s): "
                + ", ".join(sorted(set(invented)))
            )
            lines.append("- **FAIL percentiles:** do not invent p50/p95/p99")
        else:
            lines.append("- **ok no invented percentiles**")

    chain_b_text = texts.get(CHAIN_B_REL)
    if chain_b_text is not None:
        if _EXPORT_CYCLONE_URI_RE.search(chain_b_text):
            failures.append("chain_b.sh exports CYCLONEDDS_URI (default must be unset)")
            lines.append("- **FAIL chain B:** CYCLONEDDS_URI must stay unset by default")
        else:
            lines.append("- **ok chain B:** CYCLONEDDS_URI not exported")

    lines.append("")
    lines.extend(
        [
            "Filesystem + contract / Hold markers only. This is **not** a",
            "latency measurement, not a percentile reprint, and not Feishu",
            "field proof. SCOREBOARD is the current-best **pointer**; this",
            "script does not copy its numbers. fastdds.xml / SCOREBOARD are",
            "existence-only in this script; the boundary job owns the",
            "content freeze. Cross-host stays blocked. three-chain stays",
            f"{MAP_VERDICT}. Unitree 0.10.2 vs vendor 11.0.1 stays drop-in",
            "FAIL. 《3》–《6》 stay Hold. No XML rewrite this cut.",
            "",
        ]
    )

    if failures:
        lines.append("FAIL:")
        for item in failures:
            lines.append(f"- {item}")
        lines.append("")
        lines.append(
            "Required dual-chain baseline pointer, contract marker, "
            "no-XML-rewrite phrase, SCOREBOARD pointer-only, cross-host "
            "blocked, or 《3》–《6》 Hold marker is gone. Restore the "
            "docs (no XML) or the marker. Exit 1."
        )
        lines.append("")
        return "\n".join(lines), 1

    lines.append(f"- **{SUCCESS_MARKER}**")
    lines.append(f"- **{PAUSED_MARKER}**")
    lines.append("")
    lines.append(
        "Dual-chain baseline healthy: chain A/B contracts exist, this cut "
        "does not rewrite XML, SCOREBOARD stays pointer-only, cross-host "
        "is blocked, and 《3》–《6》 stay Hold. Exit 0."
    )
    lines.append("")
    return "\n".join(lines), 0


def main() -> int:
    text, code = render()
    sys.stdout.write(text)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
