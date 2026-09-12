#!/usr/bin/env python3
"""Assert Feishu wiki3 §13(6) CI + gray process-gate docs stay honest.

Vanilla box (no ROS): exit 0 when the process-gate doc + ADR §13(6)
markers are present. Missing file or expected marker: FAIL (exit 1).
On success print a line containing exactly:
    §13(6) CI + gray: process gate
On failure do not print that success marker.

Does not expand CI to Mac HIL / Promptfoo / CVE / 90% LLM, compile
vendor, or invent percentiles. Does not prove fastdds.xml /
SCOREBOARD contents are unchanged — those files are existence-only
here; the `boundary` job owns the freeze.
Style follows scripts/check_cega_bridge_hold.py / check_dual_chain_baseline.py.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys


GATE_REL = Path("docs/architecture/feishu-ci-gray.md")
ADR_REL = Path("docs/architecture/feishu-middleware-adr.md")
GATES_REL = Path("docs/architecture/ci-cd-gates.md")
XML_REL = Path("config/fastdds.xml")
SCOREBOARD_REL = Path("docs/artifacts/bench/SCOREBOARD.md")

SUCCESS_MARKER = "§13(6) CI + gray: process gate"

# Contiguous policy clauses — leftover "Hold" / "CI" tokens must not
# keep this gate green after a rewrite that claims auto-merge or Mac HIL.
_POLICY_CLAUSES = (
    "STATUS: process gate",
    "§13(6)",
    "CI + 灰度",
    "CI + gray",
    "structure",
    "contracts",
    "boundary",
    "humans merge",
    "no auto-merge",
    "agents stop before merge/production",
    "no vendor compile",
    "no XML/SCOREBOARD this cut",
    "《3》–《6》",
    "cross-host blocked",
    "#41",
    "#42",
    "may still be open",
    "do not claim they merged",
    "required checks green",
    "派生自",
    "Not Feishu field proof",
)

_GATE_MARKERS = (
    *_POLICY_CLAUSES,
    "《3》",
    "《4》",
    "《5》",
    "《6》",
    "Mac HIL",
    "Promptfoo",
    "CVE",
    "90% LLM",
    "ci-cd-gates.md",
    "allow-hold-bypass",
    "Agnocast",
    "zenoh",
    "Hold",
    "blocked",
)

_ADR_MARKERS = (
    "§13",
    "CI + 灰度",
    "feishu-ci-gray.md",
)

_GATES_MARKERS = (
    "structure",
    "contracts",
    "boundary",
    "人类批准 merge",
    "不自动合入",
)

# Full §13(6) row. Group 1 is the status cell.
_ADR_ROW_RE = re.compile(
    r"(?m)^\s*\|\s*\(6\)\s*\|\s*CI \+ 灰度\s*\|\s*(.*?)\s*\|\s*$"
)

_CELL_REQUIRED = (
    "process gate",
    "feishu-ci-gray.md",
    "structure",
    "contracts",
    "boundary",
    "不编译 vendor",
)

# Positive verdicts in that cell. Merged-#41/#42 / enabled auto-merge fail.
# "no auto-merge" is the required policy and must not trip this.
_CELL_POSITIVE_RE = re.compile(
    r"(?i)(?:\b(?:PASS|PROVEN|Active|OK|SUCCESS)\b|"
    r"#4[12]\s+(?:is\s+)?merged|"
    r"已合入\s*#?\s*4[12]|"
    r"(?<!no )auto-merge)"
)

_PROHIBITION_RE = re.compile(
    r"(不要|禁止|不得|不是|不会|do not|not write|not claim|"
    r"不得把|不要把|禁止把|不发明|不宣称|may still be open|"
    r"NOT\s+Mac HIL|不是灰度)",
    re.IGNORECASE,
)
_STATUS_FABRICATE_RE = re.compile(
    r"(?i)STATUS:\s*\*?\s*(PASS|PROVEN|OK|SUCCESS|Active|merged)\b"
)
_MERGED_FABRICATE_RES = (
    re.compile(r"(?i)#4[12]\s+(?:is\s+)?merged"),
    re.compile(r"已合入\s*#?\s*4[12]"),
    re.compile(r"(?i)auto-merge\s+(?:enabled|on|yes)"),
    re.compile(r"(?i)gray\s*=\s*(?:Mac HIL|Promptfoo|CVE|90%\s*LLM)"),
)


def _repo_root() -> Path:
    cwd = Path.cwd()
    if (cwd / GATE_REL).is_file() or (cwd / ADR_REL).is_file():
        return cwd.resolve()
    here = Path(__file__).resolve().parent
    candidate = here.parent
    if (candidate / GATE_REL).is_file() or (candidate / ADR_REL).is_file():
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
    if not all(token in cell for token in _CELL_REQUIRED):
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
    for pattern in _MERGED_FABRICATE_RES:
        for match in pattern.finditer(text):
            if _PROHIBITION_RE.search(_line_at(text, match.start())):
                continue
            hits.append(match.group(0).strip())
    return hits


def _row_self_check(adr_text: str) -> list[str]:
    """In-memory mutations must fail. Do not write the repo."""
    fails: list[str] = []
    pass_row = re.sub(
        r"(?m)^(\s*\|\s*\(6\)\s*\|\s*CI \+ 灰度\s*\|\s*)",
        r"\1**PASS** ",
        adr_text,
        count=1,
    )
    if _adr_row_ok(pass_row):
        fails.append("self-check: (6) **PASS** rewrite still matched")
    dropped = re.sub(
        r"(?m)^(\s*\|\s*\(6\)\s*\|\s*CI \+ 灰度\s*\|\s*).*$",
        r"\1三个 job only |",
        adr_text,
        count=1,
    )
    if _adr_row_ok(dropped):
        fails.append("self-check: (6) dropped process-gate cell still matched")
    return fails


def render(root: Path | None = None) -> tuple[str, int]:
    root = (root or _repo_root()).resolve()
    lines = [
        "# check_ci_gray (wiki3 §13(6) CI + gray process gate)",
        "",
    ]
    failures: list[str] = []

    # XML / SCOREBOARD: existence only. Content freeze is the `boundary` job.
    required = (
        (GATE_REL, _GATE_MARKERS, "process gate + CI + gray + three jobs"),
        (ADR_REL, _ADR_MARKERS, "opened; §13(6) row checked separately"),
        (GATES_REL, _GATES_MARKERS, "ci-cd-gates pointer: jobs + humans merge"),
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

    adr_text = texts.get(ADR_REL)
    if adr_text is not None:
        if _adr_row_ok(adr_text):
            lines.append(
                "- **ok ADR §13(6) row:** `| (6) | CI + 灰度 | process gate"
                " + structure/contracts/boundary + feishu-ci-gray.md"
                " + 不编译 vendor`"
            )
        else:
            failures.append(
                "ADR missing `| (6) | CI + 灰度 |` cell with process gate / "
                "three job names / feishu-ci-gray.md / 不编译 vendor "
                "and no PASS / #41/#42 merged"
            )
            lines.append(
                "- **FAIL ADR row:** need `| (6) | CI + 灰度 | process gate` "
                "plus structure / contracts / boundary / "
                "feishu-ci-gray.md / 不编译 vendor"
            )
        for item in _row_self_check(adr_text):
            failures.append(item)
            lines.append(f"- **FAIL {item}**")
        for hit in _fabricate_hits(adr_text):
            failures.append(f"ADR positive claim: {hit}")
            lines.append(f"- **FAIL fabricate ADR:** `{hit}`")

    gate_text = texts.get(GATE_REL)
    if gate_text is not None:
        first_status = _first_status_line(gate_text)
        if first_status and "process gate" in first_status:
            if _STATUS_FABRICATE_RE.search(first_status):
                failures.append(
                    "gate doc first Status line claims PASS/PROVEN/Active"
                )
                lines.append(
                    "- **FAIL status:** first `Status:` must stay process gate, "
                    "not PASS"
                )
            else:
                lines.append(
                    "- **ok status header:** first `Status:` is `**process gate**`"
                )
        else:
            failures.append(
                "gate doc first `Status:` line does not name process gate"
            )
            lines.append(
                "- **FAIL status:** first `Status:` must name process gate"
            )
        if "STATUS: process gate" in gate_text:
            lines.append("- **ok status phrase:** `STATUS: process gate`")
        else:
            failures.append("gate doc missing contiguous `STATUS: process gate`")
            lines.append("- **FAIL status:** need `STATUS: process gate`")
        for hit in _fabricate_hits(gate_text):
            failures.append(f"gate doc positive claim: {hit}")
            lines.append(f"- **FAIL fabricate gate:** `{hit}`")
        missing_policy = [c for c in _POLICY_CLAUSES if c not in gate_text]
        if missing_policy:
            joined = ", ".join(f"`{c}`" for c in missing_policy)
            failures.append(f"gate doc missing policy clause(s): {joined}")
            lines.append(f"- **FAIL policy:** need {joined}")
        else:
            lines.append(
                "- **ok policy:** CI + gray; three jobs; humans merge; "
                "no auto-merge; no vendor compile; "
                "no XML/SCOREBOARD this cut; 《3》–《6》; "
                "cross-host blocked; #41/#42 may still be open"
            )
        missing_phase = [m for m in ("《3》", "《4》", "《5》", "《6》") if m not in gate_text]
        if missing_phase:
            joined = ", ".join(missing_phase)
            failures.append(f"gate doc missing phase marker(s): {joined}")
            lines.append(f"- **FAIL 《3》–《6》:** need {joined}")
        else:
            lines.append("- **ok phase Hold:** 《3》–《6》")
        if "cross-host blocked" in gate_text:
            lines.append("- **ok cross-host:** `cross-host blocked`")
        else:
            failures.append("gate doc missing contiguous `cross-host blocked`")
            lines.append("- **FAIL cross-host:** need `cross-host blocked`")
        if "no XML/SCOREBOARD this cut" in gate_text:
            lines.append("- **ok freeze phrase:** `no XML/SCOREBOARD this cut`")
        else:
            failures.append("gate doc missing `no XML/SCOREBOARD this cut`")
            lines.append(
                "- **FAIL XML/SCOREBOARD:** need `no XML/SCOREBOARD this cut`"
            )
        if "no vendor compile" in gate_text:
            lines.append("- **ok vendor:** `no vendor compile`")
        else:
            failures.append("gate doc missing `no vendor compile`")
            lines.append("- **FAIL vendor:** need `no vendor compile`")
        if (
            "humans merge" in gate_text
            and "no auto-merge" in gate_text
            and "agents stop before merge/production" in gate_text
        ):
            lines.append(
                "- **ok merge policy:** humans merge; no auto-merge; "
                "agents stop before merge/production"
            )
        else:
            failures.append(
                "gate doc missing humans merge / no auto-merge / "
                "agents stop before merge/production"
            )
            lines.append(
                "- **FAIL merge:** need `humans merge` + `no auto-merge` + "
                "`agents stop before merge/production`"
            )
        if (
            "required checks green" in gate_text
            and "humans merge" in gate_text
            and "no auto-merge" in gate_text
        ):
            lines.append(
                "- **ok gray def:** required checks green + humans merge "
                "+ no auto-merge"
            )
        else:
            failures.append(
                "gate doc missing gray = required checks green + "
                "humans merge + no auto-merge"
            )
            lines.append(
                "- **FAIL gray:** need `required checks green` + "
                "`humans merge` + `no auto-merge`"
            )
        hold_not_gray = ("Mac HIL", "Promptfoo", "CVE", "90% LLM")
        if all(token in gate_text for token in hold_not_gray):
            lines.append(
                "- **ok not-gray Hold:** Mac HIL / Promptfoo / CVE / 90% LLM"
            )
        else:
            missing = [t for t in hold_not_gray if t not in gate_text]
            joined = ", ".join(missing)
            failures.append(f"gate doc missing not-gray Hold token(s): {joined}")
            lines.append(f"- **FAIL not-gray:** need {joined}")
        if (
            "#41" in gate_text
            and "#42" in gate_text
            and "may still be open" in gate_text
            and "do not claim they merged" in gate_text
        ):
            lines.append(
                "- **ok #41/#42 honesty:** may still be open; "
                "do not claim they merged"
            )
        else:
            failures.append(
                "gate doc missing #41/#42 may still be open / "
                "do not claim they merged"
            )
            lines.append(
                "- **FAIL #41/#42:** need `#41` + `#42` + "
                "`may still be open` + `do not claim they merged`"
            )
        jobs = ("structure", "contracts", "boundary")
        if all(name in gate_text for name in jobs):
            lines.append(
                "- **ok job names:** `structure` / `contracts` / `boundary`"
            )
        else:
            missing = [n for n in jobs if n not in gate_text]
            joined = ", ".join(missing)
            failures.append(f"gate doc missing required job name(s): {joined}")
            lines.append(f"- **FAIL jobs:** need {joined}")

    lines.append("")
    lines.extend(
        [
            "Filesystem + process-gate markers only. This is **not** a",
            "Mac HIL / Promptfoo / CVE / 90% LLM expansion, not a",
            "percentile, and not Feishu field proof. #41 and #42 may",
            "still be open — this script does not require those PRs to",
            "exist or be merged. fastdds.xml / SCOREBOARD are",
            "existence-only in this script; the boundary job owns the",
            "content freeze. Agnocast / zenoh stay Hold. 《3》–《6》",
            "stay Hold. Cross-host stays blocked. Do not compile vendor.",
            "Do not rewrite XML. Humans merge; no auto-merge.",
            "",
        ]
    )

    if failures:
        lines.append("FAIL:")
        for item in failures:
            lines.append(f"- {item}")
        lines.append("")
        lines.append(
            "Required CI + gray process-gate doc, three job names, "
            "humans merge / no auto-merge, no vendor compile, "
            "no XML/SCOREBOARD this cut, 《3》–《6》 Hold, "
            "cross-host blocked, ADR §13(6), or ci-cd-gates pointer "
            "is gone. Restore the docs (no XML) or the marker. Exit 1."
        )
        lines.append("")
        return "\n".join(lines), 1

    lines.append(f"- **{SUCCESS_MARKER}**")
    lines.append("")
    lines.append(
        "CI + gray process gate healthy: STATUS process gate, "
        "structure / contracts / boundary, humans merge, no auto-merge, "
        "no vendor compile, no XML/SCOREBOARD this cut, 《3》–《6》 Hold, "
        "cross-host blocked. Exit 0."
    )
    lines.append("")
    return "\n".join(lines), 0


def main() -> int:
    text, code = render()
    sys.stdout.write(text)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
