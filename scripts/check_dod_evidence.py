#!/usr/bin/env python3
"""Assert wiki3 §6.3 product DoD evidence docs stay honestly unmet.

Vanilla box (no ROS): exit 0 when the evidence doc keeps DoD: unmet,
STATUS: blocked, the five product items, and does not claim a
fabricated PASS / PROVEN / this-host measured-delta or Humble runtime.
Missing file or expected marker, or a fabricate claim: FAIL (exit 1).
On success print a line containing exactly:
    dod evidence: unmet (blocked)
On failure do not print that success marker.

Does not invent latencies, percentiles, or claim Humble ran here.
Does not prove fastdds.xml / SCOREBOARD contents are unchanged —
those files are existence-only here; the `boundary` job owns the freeze.
Style follows scripts/check_runtime_provenance.py / check_unitree_cyclone_swap.py
and the phrase-based honesty gates (map≠reproduce / pointer-only).
"""

from __future__ import annotations

from pathlib import Path
import re
import sys


DOD_REL = Path("docs/architecture/feishu-dod-evidence.md")
ADR_REL = Path("docs/architecture/feishu-middleware-adr.md")
PROVENANCE_REL = Path("docs/architecture/feishu-runtime-provenance.md")
MAP_REL = Path("docs/architecture/ros2-source-map.md")
METHOD_REL = Path("docs/architecture/latency-attribution.md")
SWAP_REL = Path("docs/architecture/unitree-sdk2-dds-swap.md")
PROVE_RMW_REL = Path("scripts/prove_rmw.py")
XML_REL = Path("config/fastdds.xml")
SCOREBOARD_REL = Path("docs/artifacts/bench/SCOREBOARD.md")

SUCCESS_MARKER = "dod evidence: unmet (blocked)"
DOD_UNMET = "DoD: unmet"
STATUS_BLOCKED = "STATUS: blocked"

# Exact substrings the evidence doc must keep. Contiguous phrases so
# `DoD: met` or `STATUS: PASS` cannot keep this gate green.
_DOD_MARKERS = (
    DOD_UNMET,
    STATUS_BLOCKED,
    "派生自",
    "Not Feishu field proof",
    "prove_rmw.py",
    "env",
    "字符串",
    "modified",
    ".so",
    "ROS not loaded",
    "Humble",
    "real build",
    "baseline-vs-change",
    "rollback",
    "acceptance",
    "feishu-runtime-provenance.md",
    "ros2-source-map.md",
    "latency-attribution.md",
    "SCOREBOARD",
    "pointer only",
    "fastdds.xml",
    "Agnocast",
    "zenoh",
    "《3》",
    "《4》",
    "《5》",
    "《6》",
    "Hold",
)

_ADR_MARKERS = (
    "§6.3",
    "prove_rmw.py",
    "feishu-dod-evidence.md",
)

_FIVE_ITEMS = (
    ("real build/test", ("real build", "build/test")),
    ("modified .so beyond prove_rmw", ("modified", ".so", "prove_rmw")),
    ("this-host baseline-vs-change", ("baseline-vs-change",)),
    ("rollback proof", ("rollback",)),
    ("product acceptance thresholds", ("acceptance",)),
)

# A prohibition on the same line ("do not write STATUS: PASS") is
# allowed; a positive STATUS: PASS / DoD: met / measured-delta is not.
_PROHIBITION_RE = re.compile(
    r"(不要|禁止|不得|不是|do not|not write|not claim|不得把|不要把|"
    r"禁止把|未测|没有|无\b|unmet|blocked)",
    re.IGNORECASE,
)
_STATUS_FABRICATE_RE = re.compile(
    r"(?i)STATUS:\s*\*?\s*(PASS|PROVEN|OK|SUCCESS|met)\b"
)
_DOD_FABRICATE_RE = re.compile(
    r"(?i)DoD:\s*\*?\s*(PASS|PROVEN|OK|SUCCESS|met)\b"
)
_FABRICATE_RES = (
    re.compile(
        r"(?i)(dod evidence|产品\s*DoD)\s*[:：]\s*(PASS|PROVEN|OK|met)\b"
    ),
    re.compile(r"(?i)measured[- ]delta\s*[:：]?\s*(PASS|PROVEN|OK|yes)\b"),
    re.compile(
        r"(?i)(this host|本机|本自动化主机).{0,40}(measured[- ]delta|测过的"
        r"\s*delta|baseline-vs-change.{0,20}(PASS|PROVEN|测出))"
    ),
    re.compile(
        r"(?i)(Humble\s+runtime\s+(existed|was present|ran)\s+here|"
        r"本机(存在过|跑过|有过)\s*Humble)"
    ),
)

# Booked tokens only. Policy words such as 分位数 are allowed.
_PERCENTILE_RE = re.compile(
    r"(?i)(?:(?<![A-Za-z0-9_])p(?:50|90|95|99(?:\.\d+)?)(?![A-Za-z0-9_.])|"
    r"(?:50|90|95|99)(?:st|nd|rd|th)\s+percentile)"
)


def _line_at(text: str, index: int) -> str:
    start = text.rfind("\n", 0, index) + 1
    end = text.find("\n", index)
    if end < 0:
        end = len(text)
    return text[start:end]


def _repo_root() -> Path:
    cwd = Path.cwd()
    if (cwd / DOD_REL).is_file() or (cwd / ADR_REL).is_file():
        return cwd.resolve()
    here = Path(__file__).resolve().parent
    candidate = here.parent
    if (candidate / DOD_REL).is_file() or (candidate / ADR_REL).is_file():
        return candidate
    sys.exit(f"cannot find repo root from cwd={cwd} or {candidate}")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _fabricate_hits(text: str) -> list[str]:
    hits: list[str] = []
    for pattern in (_STATUS_FABRICATE_RE, _DOD_FABRICATE_RE, *_FABRICATE_RES):
        for match in pattern.finditer(text):
            if _PROHIBITION_RE.search(_line_at(text, match.start())):
                continue
            hits.append(match.group(0).strip())
    return hits


def _has_five_items(text: str) -> tuple[bool, str]:
    missing: list[str] = []
    for label, tokens in _FIVE_ITEMS:
        if not all(token in text for token in tokens):
            missing.append(label)
    if missing:
        return False, "missing " + ", ".join(missing)
    return True, "five product DoD items named (all expected unmet)"


def render(root: Path | None = None) -> tuple[str, int]:
    root = (root or _repo_root()).resolve()
    lines = [
        "# check_dod_evidence (wiki3 §6.3 DoD: unmet)",
        "",
    ]
    failures: list[str] = []

    # XML / SCOREBOARD: existence only. Content freeze is the `boundary` job.
    required = (
        (DOD_REL, _DOD_MARKERS, "DoD: unmet + STATUS: blocked + five items"),
        (ADR_REL, _ADR_MARKERS, "§6.3 citation + this cut"),
        (PROVENANCE_REL, ("Underlay", "Vendor snapshot"), "underlay vs vendor pointer"),
        (MAP_REL, ("publish", "History"), "source-map pointer still present"),
        (METHOD_REL, ("wiki", "DoD"), "latency method pointer still present"),
        (SWAP_REL, ("drop-in FAIL",), "Unitree swap pointer still present"),
        (PROVE_RMW_REL, ("wiki3 §6.3", "ROS not loaded"), "env/string identity gate"),
        (XML_REL, (), "existence only; content freeze is boundary"),
        (SCOREBOARD_REL, (), "existence only; numbers not read; freeze is boundary"),
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

    dod_text = texts.get(DOD_REL)
    if dod_text is not None:
        if DOD_UNMET in dod_text:
            lines.append(f"- **ok phrase:** `{DOD_UNMET}`")
        else:
            failures.append(f"DoD doc missing contiguous `{DOD_UNMET}`")
            lines.append("- **FAIL phrase:** need contiguous DoD unmet marker")

        if STATUS_BLOCKED in dod_text:
            lines.append(f"- **ok status:** `{STATUS_BLOCKED}`")
        else:
            failures.append(f"DoD doc missing contiguous `{STATUS_BLOCKED}`")
            lines.append("- **FAIL status:** need contiguous STATUS blocked marker")

        ok_items, item_detail = _has_five_items(dod_text)
        if ok_items:
            lines.append(f"- **ok items:** {item_detail}")
        else:
            failures.append(f"DoD doc {item_detail}")
            lines.append(f"- **FAIL items:** {item_detail}")

        fabricated = _fabricate_hits(dod_text)
        if fabricated:
            joined = ", ".join(fabricated)
            failures.append(f"DoD doc fabricates product evidence: {joined}")
            lines.append("- **FAIL fabricate:** positive PASS/PROVEN/measured-delta/Humble-here")
        else:
            lines.append("- **ok honesty:** no PASS/PROVEN/measured-delta/Humble-here claim")

        invented = _PERCENTILE_RE.findall(dod_text)
        if invented:
            failures.append(
                "DoD doc invents booked percentile token(s): "
                + ", ".join(sorted({str(m) for m in invented}))
            )
            lines.append("- **FAIL percentiles:** do not invent booked pNN tokens")
        else:
            lines.append("- **ok no invented booked percentile tokens**")

    lines.append("")
    lines.extend(
        [
            "Filesystem + honesty markers only. This is **not** a loaded",
            "modified `.so` proof, not a this-host measured-delta, and not",
            "Feishu field proof. prove_rmw.py stays an env/string identity",
            "gate. SCOREBOARD is the current-best pointer; this script does",
            "not copy its numbers. fastdds.xml / SCOREBOARD are",
            "existence-only in this script; the boundary job owns the",
            "content freeze. Cross-host stays blocked. 《3》–《6》 stay Hold.",
            "This cut does not claim Humble runtime existed here.",
            "",
        ]
    )

    if failures:
        lines.append("FAIL:")
        for item in failures:
            lines.append(f"- {item}")
        lines.append("")
        lines.append(
            "Required DoD evidence file, DoD unmet marker, STATUS blocked "
            "marker, five-item list, pointer doc, or Hold marker is gone, "
            "or the page fabricates PASS/PROVEN/measured-delta/Humble-here. "
            "Restore the docs (no XML) or the marker. Exit 1."
        )
        lines.append("")
        return "\n".join(lines), 1

    lines.append(f"- **{SUCCESS_MARKER}**")
    lines.append("")
    lines.append(
        "Product DoD evidence healthy: five items stay unmet, STATUS is "
        "blocked, prove_rmw stays env/string, and this host does not claim "
        "a measured-delta or Humble runtime. Exit 0."
    )
    lines.append("")
    return "\n".join(lines), 0


def main() -> int:
    text, code = render()
    sys.stdout.write(text)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
