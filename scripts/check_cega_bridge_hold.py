#!/usr/bin/env python3
"""Assert Feishu wiki3 §13(4) Cega / Bridge Hold docs stay honest.

Vanilla box (no ROS): exit 0 when the Hold doc + ADR §13(4) markers
and read-only dimos_bridge runtime paths are present.
Missing file or expected marker: FAIL (exit 1).
On success print a line containing exactly: §13(4) Cega / Bridge: Hold
On failure do not print that success marker.

Does not integrate Cega, edit dimos_bridge runtime, or invent
percentiles. Does not prove fastdds.xml / SCOREBOARD contents are
unchanged — those files are existence-only here; the `boundary` job
owns the freeze.
Style follows scripts/check_unitree_cyclone_swap.py /
check_runtime_provenance.py.
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


HOLD_REL = Path("docs/architecture/feishu-cega-bridge-hold.md")
ADR_REL = Path("docs/architecture/feishu-middleware-adr.md")

SUCCESS_MARKER = "§13(4) Cega / Bridge: Hold"

# Exact substrings the Hold doc must keep. "no Cega" / runtime-edit /
# XML freeze phrases are contiguous so a later integrate-Cega rewrite
# cannot keep this gate green by leftover "Hold" or "Cega" tokens.
_HOLD_MARKERS = (
    "STATUS: Hold",
    "Hold",
    "no Cega",
    "不接 Cega",
    "no dimos_bridge runtime edits this cut",
    "no XML/SCOREBOARD",
    "fastdds.xml",
    "SCOREBOARD",
    "《3》",
    "《4》",
    "《5》",
    "《6》",
    "《3》–《6》",
    "Agnocast",
    "zenoh",
    "三条链",
    "DoD",
    "blocked",
    "unmet",
    "drop-in FAIL",
    "派生自",
    "dimos_bridge",
    "ROSTransport",
    "DDSTransport",
    "ZenohTransport",
    "Unitree",
)

# Loose ADR tokens still required, but they cannot keep the gate green
# if the §13(4) row itself is rewritten to PASS.
_ADR_MARKERS = (
    "§13",
    "不接 Cega",
    "dimos_bridge",
)

# Full §13(4) row. Group 1 is the status cell (not just the **Hold** prefix).
_ADR_ROW_RE = re.compile(
    r"(?m)^\s*\|\s*\(4\)\s*\|\s*Cega / Bridge 后置\s*\|\s*(.*?)\s*\|\s*$"
)

# Positive verdicts in that cell. `**Hold** … PASS` / 已接 Cega must fail.
_CELL_POSITIVE_RE = re.compile(
    r"(?i)(?:\b(?:PASS|PROVEN|Active|OK|SUCCESS)\b|"
    r"已接\s*Cega|接入\s*Cega|integrat(?:e|ed|ion)\s+Cega)"
)

# Prohibition on the same line may mention PASS / 接入 without claiming it.
_PROHIBITION_RE = re.compile(
    r"(不要|禁止|不得|不是|不会|do not|not write|not claim|不得把|不要把|"
    r"禁止把|不发明|不接|未接)",
    re.IGNORECASE,
)
_STATUS_FABRICATE_RE = re.compile(
    r"(?i)STATUS:\s*\*?\s*(PASS|PROVEN|OK|SUCCESS|Active)\b"
)
_CEGA_FABRICATE_RES = (
    re.compile(
        r"(?i)Cega\s*/\s*Bridge\s*[:：]\s*(PASS|PROVEN|OK|SUCCESS|Active)\b"
    ),
    re.compile(r"已接\s*Cega"),
    re.compile(r"(?i)integrat(?:e|ed|ion)\s+Cega"),
)

# Runtime Python this phase documents as read-only. Existence only.
_RUNTIME_RELS = (
    Path("dimos_bridge/dimos/core/transport.py"),
    Path("dimos_bridge/dimos/protocol/pubsub/impl/rospubsub.py"),
    Path("dimos_bridge/dimos/protocol/pubsub/impl/ddspubsub.py"),
    Path("dimos_bridge/dimos/protocol/pubsub/impl/rospubsub_conversion.py"),
    Path("dimos_bridge/dimos/protocol/service/ddsservice.py"),
    Path("dimos_bridge/dimos/protocol/dds_topics.py"),
    Path("dimos_bridge/dimos/robot/unitree/go2/blueprints/smart/unitree_go2_ros.py"),
    Path("dimos_bridge/dimos/robot/unitree/g1/effectors/high_level/dds_sdk.py"),
    Path("dimos_bridge/SOURCE.md"),
)


def _repo_root() -> Path:
    cwd = Path.cwd()
    if (cwd / HOLD_REL).is_file() or (cwd / ADR_REL).is_file():
        return cwd.resolve()
    here = Path(__file__).resolve().parent
    candidate = here.parent
    if (candidate / HOLD_REL).is_file() or (candidate / ADR_REL).is_file():
        return candidate
    sys.exit(f"cannot find repo root from cwd={cwd} or {candidate}")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _line_at(text: str, index: int) -> str:
    start = text.rfind("\n", 0, index) + 1
    end = text.find("\n", index)
    if end < 0:
        end = len(text)
    return text[start:end]


def _first_status_line(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("Status:"):
            return line
    return None


def _adr_row_cell(text: str) -> str | None:
    match = _ADR_ROW_RE.search(text)
    if match is None:
        return None
    return match.group(1)


def _adr_row_ok(text: str) -> bool:
    cell = _adr_row_cell(text)
    if cell is None:
        return False
    if not cell.lstrip().startswith("**Hold**"):
        return False
    if _CELL_POSITIVE_RE.search(cell):
        return False
    return True


def _fabricate_hits(text: str) -> list[str]:
    hits: list[str] = []
    for match in _STATUS_FABRICATE_RE.finditer(text):
        if _PROHIBITION_RE.search(_line_at(text, match.start())):
            continue
        hits.append(match.group(0).strip())
    for pattern in _CEGA_FABRICATE_RES:
        for match in pattern.finditer(text):
            if _PROHIBITION_RE.search(_line_at(text, match.start())):
                continue
            hits.append(match.group(0).strip())
    return hits


def _row_self_check(adr_text: str) -> list[str]:
    """In-memory mutations must fail. Do not write the repo."""
    fails: list[str] = []
    pass_row = re.sub(
        r"(?m)^(\s*\|\s*\(4\)\s*\|\s*Cega / Bridge 后置\s*\|\s*)\*\*Hold\*\*",
        r"\1**PASS**",
        adr_text,
        count=1,
    )
    if _adr_row_ok(pass_row):
        fails.append("self-check: (4) **PASS** rewrite still matched")
    hold_plus = re.sub(
        r"(?m)^(\s*\|\s*\(4\)\s*\|\s*Cega / Bridge 后置\s*\|\s*\*\*Hold\*\*)",
        r"\1 … PASS / 已接 Cega",
        adr_text,
        count=1,
    )
    if _adr_row_ok(hold_plus):
        fails.append("self-check: (4) **Hold** … PASS cell still matched")
    return fails


def render(root: Path | None = None) -> tuple[str, int]:
    root = (root or _repo_root()).resolve()
    lines = [
        "# check_cega_bridge_hold (wiki3 §13(4) Cega / Bridge Hold)",
        "",
    ]
    failures: list[str] = []

    # XML / SCOREBOARD: existence only. Content freeze is the `boundary` job.
    required = (
        (HOLD_REL, _HOLD_MARKERS, "STATUS: Hold + no Cega + no runtime edits"),
        (ADR_REL, _ADR_MARKERS, "opened; §13(4) row checked separately"),
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

    adr_text = texts.get(ADR_REL)
    if adr_text is not None:
        if _adr_row_ok(adr_text):
            lines.append(
                "- **ok ADR §13(4) row:** `| (4) | Cega / Bridge 后置 | **Hold**`"
                " (full cell; no PASS / 已接 Cega)"
            )
        else:
            failures.append(
                "ADR missing `| (4) | Cega / Bridge 后置 | **Hold**` "
                "cell without PASS / 已接 Cega"
            )
            lines.append(
                "- **FAIL ADR row:** need `| (4) | Cega / Bridge 后置 | "
                "**Hold**` and no PASS / 已接 Cega in that cell"
            )
        for item in _row_self_check(adr_text):
            failures.append(item)
            lines.append(f"- **FAIL {item}**")
        for hit in _fabricate_hits(adr_text):
            failures.append(f"ADR positive claim: {hit}")
            lines.append(f"- **FAIL fabricate ADR:** `{hit}`")

    hold_text = texts.get(HOLD_REL)
    if hold_text is not None:
        first_status = _first_status_line(hold_text)
        if first_status and first_status.startswith("Status: **Hold**"):
            if _STATUS_FABRICATE_RE.search(first_status):
                failures.append(
                    "hold doc first Status line claims PASS/PROVEN/Active"
                )
                lines.append(
                    "- **FAIL status:** first `Status:` must stay Hold, "
                    "not PASS"
                )
            else:
                lines.append(
                    "- **ok status header:** first `Status:` is `**Hold**`"
                )
        else:
            failures.append(
                "hold doc first `Status:` line is not `Status: **Hold**`"
            )
            lines.append(
                "- **FAIL status:** first `Status:` must be `Status: **Hold**`"
            )
        if "STATUS: Hold" in hold_text:
            lines.append("- **ok status phrase:** `STATUS: Hold`")
        else:
            failures.append("hold doc missing contiguous `STATUS: Hold`")
            lines.append("- **FAIL status:** need `STATUS: Hold`")
        for hit in _fabricate_hits(hold_text):
            failures.append(f"hold doc positive claim: {hit}")
            lines.append(f"- **FAIL fabricate hold:** `{hit}`")
        if "no Cega" in hold_text and "不接 Cega" in hold_text:
            lines.append("- **ok no-Cega phrases:** `no Cega` / `不接 Cega`")
        else:
            failures.append("hold doc missing `no Cega` / `不接 Cega`")
            lines.append("- **FAIL no Cega:** need `no Cega` and `不接 Cega`")
        if "no dimos_bridge runtime edits this cut" in hold_text:
            lines.append(
                "- **ok runtime freeze:** `no dimos_bridge runtime edits this cut`"
            )
        else:
            failures.append(
                "hold doc missing `no dimos_bridge runtime edits this cut`"
            )
            lines.append(
                "- **FAIL runtime edits:** need "
                "`no dimos_bridge runtime edits this cut`"
            )
        if "no XML/SCOREBOARD" in hold_text:
            lines.append("- **ok freeze phrase:** `no XML/SCOREBOARD`")
        else:
            failures.append("hold doc missing `no XML/SCOREBOARD`")
            lines.append("- **FAIL XML/SCOREBOARD:** need `no XML/SCOREBOARD`")
        missing_phase = [m for m in ("《3》", "《4》", "《5》", "《6》") if m not in hold_text]
        if missing_phase:
            joined = ", ".join(missing_phase)
            failures.append(f"hold doc missing phase marker(s): {joined}")
            lines.append(f"- **FAIL 《3》–《6》:** need {joined}")
        else:
            lines.append("- **ok phase Hold:** 《3》–《6》")

    for rel in _RUNTIME_RELS:
        path = root / rel
        key = rel.as_posix()
        if not path.is_file():
            failures.append(f"missing read-only runtime `{key}`")
            lines.append(f"- **FAIL missing runtime:** `{key}`")
            continue
        lines.append(f"- **ok runtime path:** `{key}` (existence only; not edited here)")

    lines.append("")
    lines.extend(
        [
            "Filesystem + Hold markers only. This is **not** a Cega",
            "integration, not a percentile, and not Feishu field proof.",
            "dimos_bridge runtime paths are existence-only; this script",
            "does not hash them and does not edit them.",
            "fastdds.xml / SCOREBOARD are existence-only in this script;",
            "the boundary job owns the content freeze. Agnocast / zenoh",
            "stay Hold. 《3》–《6》 stay Hold. Three-chain / DoD stay",
            "unmet / blocked. Unitree drop-in stays FAIL.",
            "",
        ]
    )

    if failures:
        lines.append("FAIL:")
        for item in failures:
            lines.append(f"- {item}")
        lines.append("")
        lines.append(
            "Required Hold doc, no Cega / no dimos_bridge runtime-edit "
            "marker, no XML/SCOREBOARD, 《3》–《6》 Hold, ADR §13(4), "
            "or read-only runtime path is gone. Restore the docs (no XML) "
            "or the marker. Exit 1."
        )
        lines.append("")
        return "\n".join(lines), 1

    lines.append(f"- **{SUCCESS_MARKER}**")
    lines.append("")
    lines.append(
        "Cega / Bridge Hold healthy: STATUS Hold, no Cega, no "
        "dimos_bridge runtime edits this cut, no XML/SCOREBOARD, "
        "《3》–《6》 Hold. Exit 0."
    )
    lines.append("")
    return "\n".join(lines), 0


def main() -> int:
    text, code = render()
    sys.stdout.write(text)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
