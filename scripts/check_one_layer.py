#!/usr/bin/env python3
"""Assert Feishu wiki3 §13(5) one-layer process-gate docs stay honest.

Vanilla box (no ROS): exit 0 when the process-gate doc + ADR §13(5)
markers are present. Missing file or expected marker: FAIL (exit 1).
On success print a line containing exactly:
    §13(5) one-layer: process gate
On failure do not print that success marker.

Does not land a middleware layer, integrate Cega, or invent
percentiles. Does not prove fastdds.xml / SCOREBOARD contents are
unchanged — those files are existence-only here; the `boundary` job
owns the freeze.
Style follows scripts/check_cega_bridge_hold.py / check_sink_layers.py.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys


GATE_REL = Path("docs/architecture/feishu-one-layer.md")
ADR_REL = Path("docs/architecture/feishu-middleware-adr.md")
SINK_REL = Path("docs/architecture/feishu-sink-layers.md")
MATRIX_REL = Path("docs/architecture/feishu-risk-matrix.md")
XML_REL = Path("config/fastdds.xml")
SCOREBOARD_REL = Path("docs/artifacts/bench/SCOREBOARD.md")

SUCCESS_MARKER = "§13(5) one-layer: process gate"

# Contiguous policy clauses — leftover "Hold" / "一层" tokens must not
# keep this gate green after a rewrite that bundles layers or XML.
_POLICY_CLAUSES = (
    "STATUS: process gate",
    "one-layer",
    "一次一层",
    "separate PR",
    "下一层另开 PR",
    "no XML/SCOREBOARD this cut",
    "Cega+memory+XML",
    "《3》–《6》",
    "cross-host blocked",
    "#41",
    "may still be open",
    "do not claim it merged",
    "env/XML first",
    "executor mid",
    "core fork last",
    "派生自",
)

_GATE_MARKERS = (
    *_POLICY_CLAUSES,
    "《3》",
    "《4》",
    "《5》",
    "《6》",
    "Not Feishu field proof",
    "allow-hold-bypass",
    "feishu-sink-layers.md",
    "feishu-risk-matrix.md",
    "XML/SCOREBOARD frozen unless labeled",
    "Agnocast",
    "zenoh",
    "Hold",
    "blocked",
)

_ADR_MARKERS = (
    "§13",
    "一次一层",
    "feishu-one-layer.md",
)

_SINK_MARKERS = (
    "一次一层",
    "app",
    "rcl",
    "rmw",
    "DDS",
    "executor",
    "memory",
)

_MATRIX_MARKERS = (
    "env/XML",
    "core forks",
    "Executor",
)

# Full §13(5) row. Group 1 is the status cell.
_ADR_ROW_RE = re.compile(
    r"(?m)^\s*\|\s*\(5\)\s*\|\s*一次一层\s*\|\s*(.*?)\s*\|\s*$"
)

_CELL_REQUIRED = (
    "process gate",
    "下一层另开 PR",
    "feishu-one-layer.md",
)

# Positive verdicts in that cell. Bundled-layer / merged-#41 claims fail.
_CELL_POSITIVE_RE = re.compile(
    r"(?i)(?:\b(?:PASS|PROVEN|Active|OK|SUCCESS)\b|"
    r"memory Hold\s+(?:is\s+)?(?:merged|landed|已合入)|"
    r"已合入\s*#?\s*41|"
    r"#41\s+(?:is\s+)?merged)"
)

_PROHIBITION_RE = re.compile(
    r"(不要|禁止|不得|不是|不会|do not|not write|not claim|不得把|不要把|"
    r"禁止把|不发明|不宣称|may still be open)",
    re.IGNORECASE,
)
_STATUS_FABRICATE_RE = re.compile(
    r"(?i)STATUS:\s*\*?\s*(PASS|PROVEN|OK|SUCCESS|Active|merged)\b"
)
_MERGED_FABRICATE_RES = (
    re.compile(r"(?i)#41\s+(?:is\s+)?merged"),
    re.compile(r"(?i)memory Hold\s+(?:is\s+)?(?:merged|landed)"),
    re.compile(r"已合入\s*#?\s*41"),
    re.compile(r"(?i)Cega\s*\+\s*memory\s*\+\s*XML\s+(?:in this|this)\s+PR"),
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
        r"(?m)^(\s*\|\s*\(5\)\s*\|\s*一次一层\s*\|\s*)",
        r"\1**PASS** ",
        adr_text,
        count=1,
    )
    if _adr_row_ok(pass_row):
        fails.append("self-check: (5) **PASS** rewrite still matched")
    dropped = re.sub(
        r"(?m)^(\s*\|\s*\(5\)\s*\|\s*一次一层\s*\|\s*).*$",
        r"\1文档 only |",
        adr_text,
        count=1,
    )
    if _adr_row_ok(dropped):
        fails.append("self-check: (5) dropped process-gate cell still matched")
    return fails


def render(root: Path | None = None) -> tuple[str, int]:
    root = (root or _repo_root()).resolve()
    lines = [
        "# check_one_layer (wiki3 §13(5) one-layer process gate)",
        "",
    ]
    failures: list[str] = []

    # XML / SCOREBOARD: existence only. Content freeze is the `boundary` job.
    required = (
        (GATE_REL, _GATE_MARKERS, "process gate + one-layer + separate PR"),
        (ADR_REL, _ADR_MARKERS, "opened; §13(5) row checked separately"),
        (SINK_REL, _SINK_MARKERS, "sink-layers order pointer target"),
        (MATRIX_REL, _MATRIX_MARKERS, "risk-matrix order pointer target"),
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
                "- **ok ADR §13(5) row:** `| (5) | 一次一层 | process gate"
                " + 下一层另开 PR + feishu-one-layer.md`"
            )
        else:
            failures.append(
                "ADR missing `| (5) | 一次一层 |` cell with process gate / "
                "下一层另开 PR / feishu-one-layer.md and no PASS / #41 merged"
            )
            lines.append(
                "- **FAIL ADR row:** need `| (5) | 一次一层 | process gate` "
                "plus 下一层另开 PR / feishu-one-layer.md"
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
                "- **ok policy:** one-layer; separate PR; "
                "no XML/SCOREBOARD this cut; 《3》–《6》; "
                "cross-host blocked; #41 may still be open"
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
        if "Cega+memory+XML" in gate_text:
            lines.append("- **ok no-bundle:** `Cega+memory+XML`")
        else:
            failures.append("gate doc missing `Cega+memory+XML`")
            lines.append("- **FAIL bundle:** need `Cega+memory+XML`")
        if (
            "#41" in gate_text
            and "may still be open" in gate_text
            and "do not claim it merged" in gate_text
        ):
            lines.append(
                "- **ok #41 honesty:** may still be open; do not claim it merged"
            )
        else:
            failures.append(
                "gate doc missing #41 may still be open / do not claim it merged"
            )
            lines.append(
                "- **FAIL #41:** need `#41` + `may still be open` + "
                "`do not claim it merged`"
            )

    lines.append("")
    lines.extend(
        [
            "Filesystem + process-gate markers only. This is **not** a",
            "landed middleware layer, not a percentile, and not Feishu",
            "field proof. #41 memory Hold may still be open — this script",
            "does not require that PR to exist or be merged.",
            "fastdds.xml / SCOREBOARD are existence-only in this script;",
            "the boundary job owns the content freeze. Agnocast / zenoh",
            "stay Hold. 《3》–《6》 stay Hold. Cross-host stays blocked.",
            "Do not bundle Cega+memory+XML. Do not rewrite XML.",
            "",
        ]
    )

    if failures:
        lines.append("FAIL:")
        for item in failures:
            lines.append(f"- {item}")
        lines.append("")
        lines.append(
            "Required one-layer process-gate doc, separate-PR marker, "
            "no XML/SCOREBOARD this cut, 《3》–《6》 Hold, cross-host "
            "blocked, ADR §13(5), or order-pointer target is gone. "
            "Restore the docs (no XML) or the marker. Exit 1."
        )
        lines.append("")
        return "\n".join(lines), 1

    lines.append(f"- **{SUCCESS_MARKER}**")
    lines.append("")
    lines.append(
        "One-layer process gate healthy: STATUS process gate, one-layer, "
        "separate PR, no XML/SCOREBOARD this cut, 《3》–《6》 Hold, "
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
