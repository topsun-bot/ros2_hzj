#!/usr/bin/env python3
"""Assert wiki3 §13(2) three-chain reproduce docs stay honestly blocked.

Vanilla box (no ROS): exit 0 when the status doc keeps map≠reproduce,
STATUS: blocked, and the three chain names — and does not claim a
fabricated PASS/PROVEN reproduce.
Missing file or expected marker, or a fabricate claim: FAIL (exit 1).
On success print a line containing exactly:
    three-chain repro: blocked (map only)
On failure do not print that success marker.

Does not invent latencies, percentiles, or claim the reproduce ran.
Does not prove fastdds.xml / SCOREBOARD contents are unchanged —
those files are existence-only here; the `boundary` job owns the freeze.
Style follows scripts/check_runtime_provenance.py / check_unitree_cyclone_swap.py.
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
from _repo import repo_root, read_utf8


REPRO_REL = Path("docs/architecture/feishu-three-chain-repro.md")
MAP_REL = Path("docs/architecture/ros2-source-map.md")
WAITSET_REL = Path("docs/architecture/feishu-executor-waitset.md")
ADR_REL = Path("docs/architecture/feishu-middleware-adr.md")

SUCCESS_MARKER = "three-chain repro: blocked (map only)"
MAP_NE_REPRODUCE = "map ≠ reproduce"
STATUS_BLOCKED = "STATUS: blocked"

# Exact substrings the status doc must keep. Contiguous phrases so
# `map = reproduce` or `STATUS: PASS` cannot keep this gate green.
_REPRO_MARKERS = (
    MAP_NE_REPRODUCE,
    STATUS_BLOCKED,
    "publish",
    "History",
    "wait→callback",
    "WaitSet",
    "callback",
    "not-run-here",
    "Not Feishu field proof",
    "ros2-source-map.md",
    "feishu-executor-waitset.md",
    "Humble",
    "fastdds.xml",
    "SCOREBOARD",
    "Agnocast",
    "zenoh",
)

# Claims that the reproduce itself ran / passed. A prohibition on the
# same line ("do not write STATUS: PASS") is allowed; a positive
# STATUS: PASS / map = reproduce is not.
_PROHIBITION_RE = re.compile(
    r"(不要|禁止|不得|不是|do not|not write|not claim|不得把|不要把)",
    re.IGNORECASE,
)
_STATUS_FABRICATE_RE = re.compile(
    r"(?i)STATUS:\s*\*?\s*(PASS|PROVEN|OK|SUCCESS)\b"
)
_FABRICATE_RES = (
    re.compile(
        r"(?i)(three-chain\s+repro|三条链复现)\s*[:：]\s*(PASS|PROVEN|OK)\b"
    ),
    re.compile(r"(?i)\breproduce\s*[:：]\s*(PASS|PROVEN)\b"),
    re.compile(r"(?i)\bmap\s*=\s*reproduce\b"),
)


def _line_at(text: str, index: int) -> str:
    start = text.rfind("\n", 0, index) + 1
    end = text.find("\n", index)
    if end < 0:
        end = len(text)
    return text[start:end]


def _fabricate_hits(text: str) -> list[str]:
    hits: list[str] = []
    for match in _STATUS_FABRICATE_RE.finditer(text):
        if _PROHIBITION_RE.search(_line_at(text, match.start())):
            continue
        hits.append(match.group(0).strip())
    for pattern in _FABRICATE_RES:
        match = pattern.search(text)
        if match:
            if _PROHIBITION_RE.search(_line_at(text, match.start())):
                continue
            hits.append(match.group(0).strip())
    return hits


def _has_three_chains(text: str) -> tuple[bool, str]:
    has_publish = "publish" in text
    has_history = "History" in text
    has_wait_cb = "wait→callback" in text or "wait->callback" in text
    has_waitset_cb = "WaitSet" in text and "callback" in text
    if has_publish and has_history and (has_wait_cb or has_waitset_cb):
        return True, "publish / History / wait→callback (or WaitSet/callback)"
    missing = []
    if not has_publish:
        missing.append("publish")
    if not has_history:
        missing.append("History")
    if not (has_wait_cb or has_waitset_cb):
        missing.append("wait→callback or WaitSet/callback")
    return False, "missing " + ", ".join(missing)


def render(root: Path | None = None) -> tuple[str, int]:
    root = (root or repo_root(REPRO_REL, ADR_REL)).resolve()
    lines = [
        "# check_three_chain_repro (wiki3 §13(2) map ≠ reproduce)",
        "",
    ]
    failures: list[str] = []

    # XML / SCOREBOARD: existence only. Content freeze is the `boundary` job.
    required = (
        (REPRO_REL, _REPRO_MARKERS, "map ≠ reproduce + STATUS: blocked"),
        (MAP_REL, ("publish", "History"), "map file still present"),
        (WAITSET_REL, ("WaitSet", "callback"), "wait→callback map still present"),
        (ADR_REL, ("§13",), "ADR still cites §13"),
        (XML_REL, (), XML_EXISTENCE_NOTE),
        (SCOREBOARD_REL, (), SCOREBOARD_EXISTENCE_NOTE),
    )
    texts: dict[Path, str] = {}
    for rel, markers, hint in required:
        path = root / rel
        key = rel.as_posix()
        if not path.is_file():
            failures.append(f"missing file `{key}`")
            lines.append(f"- **FAIL missing:** `{key}`")
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

    repro_text = texts.get(REPRO_REL)
    if repro_text is not None:
        if MAP_NE_REPRODUCE in repro_text:
            lines.append(f"- **ok phrase:** `{MAP_NE_REPRODUCE}`")
        else:
            failures.append(f"repro doc missing contiguous `{MAP_NE_REPRODUCE}`")
            lines.append(f"- **FAIL phrase:** need `{MAP_NE_REPRODUCE}`")

        if STATUS_BLOCKED in repro_text:
            lines.append(f"- **ok status:** `{STATUS_BLOCKED}`")
        else:
            failures.append(f"repro doc missing contiguous `{STATUS_BLOCKED}`")
            lines.append(f"- **FAIL status:** need `{STATUS_BLOCKED}`")

        ok_chains, chain_detail = _has_three_chains(repro_text)
        if ok_chains:
            lines.append(f"- **ok chains:** {chain_detail}")
        else:
            failures.append(f"repro doc {chain_detail}")
            lines.append(f"- **FAIL chains:** {chain_detail}")

        fabricated = _fabricate_hits(repro_text)
        if fabricated:
            joined = ", ".join(fabricated)
            failures.append(f"repro doc fabricates reproduce: {joined}")
            lines.append(f"- **FAIL fabricate:** {joined}")
        else:
            lines.append("- **ok honesty:** no PASS/PROVEN reproduce claim")

    lines.append("")
    lines.extend(
        [
            "Filesystem + honesty markers only. This is **not** a loaded",
            "`.so` proof, not a percentile, and not Feishu field proof.",
            "A healthy source map is not a reproduce. This host has no",
            "ROS Humble runtime; keep STATUS: blocked. fastdds.xml /",
            "SCOREBOARD are existence-only in this script; the boundary",
            "job owns the content freeze. Agnocast / zenoh stay Hold.",
            "",
        ]
    )

    if failures:
        lines.append("FAIL:")
        for item in failures:
            lines.append(f"- {item}")
        lines.append("")
        lines.append(
            "Required three-chain status doc, map≠reproduce phrase, "
            "STATUS: blocked, chain names, or sibling map file is gone "
            "(or the doc claims PASS/PROVEN). Restore the docs (no XML) "
            "or the honest blocked marker. Exit 1."
        )
        lines.append("")
        return "\n".join(lines), 1

    lines.append(f"- **{SUCCESS_MARKER}**")
    lines.append("")
    lines.append(
        "Three-chain reproduce record healthy: map ≠ reproduce and "
        "STATUS: blocked (map only). Exit 0."
    )
    lines.append("")
    return "\n".join(lines), 0


def main() -> int:
    text, code = render()
    sys.stdout.write(text)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
