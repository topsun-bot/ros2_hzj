#!/usr/bin/env python3
"""Assert Feishu wiki3 §13(3) dual-chain baseline pointer docs stay honest.

Vanilla box (no ROS): exit 0 when the baseline doc + dual-chain contract
scripts + ADR §13(3) pointer markers are present.
Missing file or expected marker: FAIL (exit 1).
On success print a line containing exactly:
  dual-chain baseline: pointer only (no XML rewrite)
and a line containing exactly:
  same-topology XML tuning is paused
On failure do not print those success markers (including in ok/FAIL
diagnostics).

Does not invent booked percentile tokens (p50 / p90 / p95 / p99 or
"Nth percentile"), including labels next to Chinese text. Policy
words such as 分位数 are allowed.
Does not prove fastdds.xml / SCOREBOARD contents are unchanged —
those files are existence-only here; the `boundary` job owns the freeze.
chain_b.sh must `unset CYCLONEDDS_URI` (same as load.py CHAIN_B_UNSET)
and must not `export CYCLONEDDS_URI=`.
Style follows scripts/check_unitree_cyclone_swap.py / check_risk_matrix.py.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys

from _freeze_paths import (
    FASTDDS_XML_REL as XML_REL,
    SCOREBOARD_EXISTENCE_NOTE,
    SCOREBOARD_REL,
    XML_EXISTENCE_NOTE,
)


BASELINE_REL = Path("docs/architecture/feishu-dual-chain-baseline.md")
ADR_REL = Path("docs/architecture/feishu-middleware-adr.md")
CHAIN_A_REL = Path("config/env/chain_a.sh")
CHAIN_B_REL = Path("config/env/chain_b.sh")
R0_REL = Path("docs/architecture/ros2-dds-r0-interface-freeze.md")
MAP_REL = Path("docs/architecture/ros2-source-map.md")
SWAP_REL = Path("docs/architecture/unitree-sdk2-dds-swap.md")

SUCCESS_MARKER = "dual-chain baseline: pointer only (no XML rewrite)"
PAUSED_MARKER = "same-topology XML tuning is paused"
MAP_VERDICT = "map≠reproduce"
NO_REWRITE = "no XML rewrite"

# Contiguous phrases so a lone "pointer" / "blocked" / "Hold" cannot
# keep this gate green. Paused success phrase is checked separately so
# a FAIL report does not echo it. Not scores, not percentiles.
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

_EXPORT_CHAIN_A = (
    re.compile(r"(?m)^\s*export\s+RMW_IMPLEMENTATION=rmw_fastrtps_cpp\s*$"),
    re.compile(r"(?m)^\s*export\s+ROS_DOMAIN_ID=42\s*$"),
    re.compile(
        r"(?m)^\s*export\s+FASTRTPS_DEFAULT_PROFILES_FILE=.*config/fastdds\.xml"
    ),
)
_EXPORT_CHAIN_B = (
    re.compile(r"(?m)^\s*export\s+RMW_IMPLEMENTATION=rmw_cyclonedds_cpp\s*$"),
    re.compile(r"(?m)^\s*export\s+ROS_DOMAIN_ID=0\s*$"),
)

# Booked tokens only. ASCII lookarounds so 链A的p99=… still matches;
# Python \b treats CJK as word chars. Policy words (分位数) are OK.
_PERCENTILE_RE = re.compile(
    r"(?i)(?:(?<![A-Za-z0-9_])p(?:50|90|95|99(?:\.\d+)?)(?![A-Za-z0-9_.])|"
    r"(?:50|90|95|99)(?:st|nd|rd|th)\s+percentile)"
)
_EXPORT_CYCLONE_URI_RE = re.compile(
    r"(?m)^\s*export\s+CYCLONEDDS_URI\s*="
)
_UNSET_CYCLONE_URI_RE = re.compile(r"(?m)^\s*unset\s+CYCLONEDDS_URI\s*$")


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


def _missing_exports(text: str, patterns: tuple[re.Pattern[str], ...]) -> list[str]:
    missing: list[str] = []
    for pattern in patterns:
        if pattern.search(text) is None:
            missing.append(pattern.pattern)
    return missing


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
        (CHAIN_A_REL, (), "opened; export assignments checked separately"),
        (CHAIN_B_REL, (), "opened; export assignments + no URI export"),
        (R0_REL, ("Hold",), "dual-chain R0 freeze exists"),
        (MAP_REL, ("vendor", "不是复现"), "three-chain map exists (not a reproduce)"),
        (SWAP_REL, ("drop-in FAIL", "0.10.2", "11.0.1"), "Unitree 0.10.2 vs vendor 11.0.1"),
        (XML_REL, (), XML_EXISTENCE_NOTE),
        (SCOREBOARD_REL, (), SCOREBOARD_EXISTENCE_NOTE),
    )
    existence_only = {XML_REL, SCOREBOARD_REL}
    texts: dict[Path, str] = {}
    for rel, markers, hint in required:
        path = root / rel
        key = rel.as_posix()
        if not path.is_file():
            failures.append(f"missing file `{key}`")
            lines.append(f"- **FAIL missing:** `{key}`")
            continue
        if rel in existence_only:
            extra = f" ({hint})" if hint else ""
            lines.append(f"- **ok file:** `{key}`{extra}")
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
            lines.append("- **ok paused phrase:** present in baseline doc")
        else:
            failures.append("baseline doc missing contiguous same-topology paused phrase")
            lines.append("- **FAIL paused:** need same-topology paused phrase")
        if MAP_VERDICT in baseline_text:
            lines.append("- **ok three-chain phrase:** present")
        else:
            failures.append("baseline doc missing contiguous three-chain map verdict")
            lines.append("- **FAIL map:** need three-chain map verdict")
        if NO_REWRITE in baseline_text:
            lines.append("- **ok no-rewrite phrase:** present")
        else:
            failures.append("baseline doc missing contiguous no-XML-rewrite phrase")
            lines.append("- **FAIL rewrite:** need no-XML-rewrite phrase")
        if "pointer only" in baseline_text:
            lines.append("- **ok SCOREBOARD phrase:** pointer-only present")
        else:
            failures.append("baseline doc missing SCOREBOARD pointer-only phrase")
            lines.append("- **FAIL pointer:** need pointer-only phrase")
        invented = _PERCENTILE_RE.findall(baseline_text)
        if invented:
            failures.append(
                "baseline doc invents booked percentile token(s): "
                + ", ".join(sorted(set(invented)))
            )
            lines.append("- **FAIL percentiles:** do not invent booked pNN tokens")
        else:
            lines.append("- **ok no invented booked percentile tokens**")

    chain_a_text = texts.get(CHAIN_A_REL)
    if chain_a_text is not None:
        missing_a = _missing_exports(chain_a_text, _EXPORT_CHAIN_A)
        if missing_a:
            failures.append("chain_a.sh missing anchored export assignment(s)")
            lines.append("- **FAIL chain A:** need anchored export assignments")
        else:
            lines.append("- **ok chain A:** anchored export assignments")

    chain_b_text = texts.get(CHAIN_B_REL)
    if chain_b_text is not None:
        missing_b = _missing_exports(chain_b_text, _EXPORT_CHAIN_B)
        if missing_b:
            failures.append("chain_b.sh missing anchored export assignment(s)")
            lines.append("- **FAIL chain B:** need anchored export assignments")
        else:
            lines.append("- **ok chain B:** anchored export assignments")
        if _EXPORT_CYCLONE_URI_RE.search(chain_b_text):
            failures.append("chain_b.sh exports CYCLONEDDS_URI (helper must not set it)")
            lines.append("- **FAIL chain B:** helper must not export CYCLONEDDS_URI")
        elif _UNSET_CYCLONE_URI_RE.search(chain_b_text) is None:
            failures.append("chain_b.sh missing anchored unset CYCLONEDDS_URI")
            lines.append("- **FAIL chain B:** need anchored unset CYCLONEDDS_URI")
        else:
            lines.append(
                "- **ok chain B:** helper unsets CYCLONEDDS_URI "
                "(aligns with load.py CHAIN_B_UNSET)"
            )

    lines.append("")
    lines.extend(
        [
            "Filesystem + contract / Hold markers only. This is **not** a",
            "latency measurement, not a booked-percentile reprint, and not",
            "Feishu field proof. SCOREBOARD is the current-best pointer;",
            "this script does not copy its numbers. fastdds.xml /",
            "SCOREBOARD are existence-only in this script; the boundary",
            "job owns the content freeze. Cross-host stays blocked.",
            "three-chain stays map-only. Unitree 0.10.2 vs vendor 11.0.1",
            "stays drop-in FAIL. 《3》–《6》 stay Hold. This cut does not",
            "rewrite XML. chain_b.sh unsets CYCLONEDDS_URI.",
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
