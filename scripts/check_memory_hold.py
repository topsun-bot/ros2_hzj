#!/usr/bin/env python3
"""Assert Feishu memory sink-layer Hold docs stay honest.

Vanilla box (no ROS): exit 0 when the Hold doc + ADR / sink-layers /
cn-jp markers, Cyclone psmx_iox source contrast, and absent
vendor/iceoryx tree are present.
Missing file or expected marker: FAIL (exit 1).
On success print a line containing exactly:
    memory layer: Hold (no zero-copy land)
On failure do not print that success marker.

Does not invent latency or claim Iceoryx is running.
Does not prove fastdds.xml / SCOREBOARD contents are unchanged —
those files are existence-only here; the `boundary` job owns the freeze.
Style follows scripts/check_cega_bridge_hold.py /
check_dod_evidence.py (contiguous clauses; reject PASS/PROVEN/Active).
"""

from __future__ import annotations

from pathlib import Path
import re
import sys


HOLD_REL = Path("docs/architecture/feishu-memory-hold.md")
ADR_REL = Path("docs/architecture/feishu-middleware-adr.md")
SINK_REL = Path("docs/architecture/feishu-sink-layers.md")
CNJP_REL = Path("docs/architecture/cn-jp-ros2-absorb.md")
CYCLONE_CMAKE_REL = Path("vendor/CycloneDDS/src/CMakeLists.txt")
PSMX_REL = Path("vendor/CycloneDDS/src/psmx_iox")
ICEORYX_VENDOR_REL = Path("vendor/iceoryx")
XML_REL = Path("config/fastdds.xml")
SCOREBOARD_REL = Path("docs/artifacts/bench/SCOREBOARD.md")

SUCCESS_MARKER = "memory layer: Hold (no zero-copy land)"

# Exact substrings the Hold doc must keep. Contiguous so a leftover
# "Hold" / "Iceoryx" token cannot keep this gate green after a land.
_HOLD_MARKERS = (
    "STATUS: Hold",
    "Hold",
    "no zero-copy land",
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
    "heaphook",
    "Loaned",
    "Data Sharing",
    "data_sharing",
    "Iceoryx",
    "Iceoryx2",
    "psmx_iox",
    "ENABLE_ICEORYX",
    "ENABLE_ICEORYX2",
    "AUTO ≠ 已开零拷",
    "AUTO CMake ≠ zero-copy proven",
    "adapter source ≠ vendored Iceoryx",
    "没有 vendor/iceoryx",
    "派生自",
    "drop-in FAIL",
    "wire UNPROVEN",
    "blocked",
    "unmet",
    "三条链",
    "DoD",
    "Cega",
    "跨机",
    "并列",
    "Not Feishu field proof",
    "map ≠ reproduce",
)

_ADR_MARKERS = (
    "内存",
    "feishu-memory-hold.md",
    "check_memory_hold.py",
    "check_cega_bridge_hold.py",
    "Hold",
)

_SINK_MARKERS = (
    "feishu-memory-hold.md",
    "AUTO ≠ 已开零拷",
    "没有 vendor/iceoryx",
    "psmx_iox",
    "Hold",
)

_CNJP_MARKERS = (
    "Loaned",
    "Data Sharing",
    "Agnocast",
    "zenoh",
    "heaphook",
    "data_sharing",
    "不翻转现网",
    "Hold",
)

_CYCLONE_AUTO_MARKERS = (
    'set(ENABLE_ICEORYX "AUTO"',
    'set(ENABLE_ICEORYX2 "AUTO"',
)

# A prohibition / contrast on the same line may mention PASS without
# claiming it. Do not treat unmet/blocked as prohibition words.
_PROHIBITION_RE = re.compile(
    r"(不要|禁止|不得|不是|不会|不编造|不落地|不发明|不接|未接|"
    r"do not|not write|not claim|不得把|不要把|禁止把|≠)",
    re.IGNORECASE,
)
_STATUS_FABRICATE_RE = re.compile(
    r"(?i)STATUS:\s*\*?\s*(PASS|PROVEN|OK|SUCCESS|Active)\b"
)
_MEMORY_FABRICATE_RES = (
    re.compile(
        r"(?i)memory layer\s*[:：]\s*(PASS|PROVEN|OK|SUCCESS|Active)\b"
    ),
    re.compile(r"(?i)Iceoryx(?:2)?\s+(?:is\s+)?running\b"),
    re.compile(r"Iceoryx(?:2)?\s+已运行"),
    re.compile(r"(?i)zero-copy\s+(?:landed|proven|enabled)\b"),
    re.compile(r"(?i)(?:Loaned|Data Sharing)\s+(?:landed|enabled|Active|PROVEN)\b"),
    re.compile(r"已开零拷"),
    re.compile(r"已 vendor Iceoryx"),
)

# Booked tokens only. Policy words such as 分位数 are allowed.
_PERCENTILE_RE = re.compile(
    r"(?i)(?:(?<![A-Za-z0-9_])p(?:50|90|95|99(?:\.\d+)?)(?![A-Za-z0-9_.])|"
    r"(?:50|90|95|99)(?:st|nd|rd|th)\s+percentile)"
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


def _fabricate_hits(text: str) -> list[str]:
    hits: list[str] = []
    for match in _STATUS_FABRICATE_RE.finditer(text):
        line = _line_at(text, match.start())
        # Status header must stay Hold even if the same line says 不是.
        if not line.startswith("Status:") and _PROHIBITION_RE.search(line):
            continue
        hits.append(match.group(0).strip())
    for pattern in _MEMORY_FABRICATE_RES:
        for match in pattern.finditer(text):
            if _PROHIBITION_RE.search(_line_at(text, match.start())):
                continue
            hits.append(match.group(0).strip())
    return hits


def _hold_status_ok(text: str) -> tuple[bool, str]:
    first_status = _first_status_line(text)
    if not first_status or not first_status.startswith("Status: **Hold**"):
        return False, "first `Status:` must be `Status: **Hold**`"
    if _STATUS_FABRICATE_RE.search(first_status):
        return False, "first `Status:` must stay Hold, not PASS"
    if "STATUS: Hold" not in text:
        return False, "need contiguous `STATUS: Hold`"
    return True, "first `Status:` is `**Hold**` + `STATUS: Hold`"


def _status_self_check(hold_text: str) -> list[str]:
    """In-memory mutations must fail. Do not write the repo."""
    fails: list[str] = []
    pass_header = re.sub(
        r"^Status: \*\*Hold\*\*",
        "Status: **PASS**",
        hold_text,
        count=1,
        flags=re.MULTILINE,
    )
    ok, _ = _hold_status_ok(pass_header)
    if ok:
        fails.append("self-check: Status **PASS** rewrite still matched")
    pass_phrase = hold_text.replace("STATUS: Hold", "STATUS: PASS", 1)
    ok_pass, _ = _hold_status_ok(pass_phrase)
    if ok_pass:
        fails.append("self-check: STATUS: PASS rewrite still matched")
    if not _fabricate_hits(pass_phrase):
        fails.append("self-check: STATUS: PASS rewrite not caught")
    return fails


def render(root: Path | None = None) -> tuple[str, int]:
    root = (root or _repo_root()).resolve()
    lines = [
        "# check_memory_hold (Feishu memory sink layer Hold)",
        "",
    ]
    failures: list[str] = []

    # XML / SCOREBOARD: existence only. Content freeze is the `boundary` job.
    required = (
        (HOLD_REL, _HOLD_MARKERS, "STATUS: Hold + no zero-copy land + no XML/SCOREBOARD"),
        (ADR_REL, _ADR_MARKERS, "内存 + memory checker + Cega checker inventory"),
        (SINK_REL, _SINK_MARKERS, "memory row still points at Hold page"),
        (CNJP_REL, _CNJP_MARKERS, "Loaned / Data Sharing / Agnocast / zenoh Hold"),
        (CYCLONE_CMAKE_REL, _CYCLONE_AUTO_MARKERS, "ENABLE_ICEORYX* still AUTO (source contrast)"),
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

    psmx = root / PSMX_REL
    psmx_cmake = psmx / "CMakeLists.txt"
    if psmx.is_dir() and psmx_cmake.is_file():
        lines.append(
            f"- **ok source contrast:** `{PSMX_REL.as_posix()}/` "
            "(adapter source; not a running Iceoryx)"
        )
    else:
        failures.append(
            f"missing Cyclone PSMX adapter source `{PSMX_REL.as_posix()}/`"
        )
        lines.append(
            f"- **FAIL missing:** `{PSMX_REL.as_posix()}/` "
            "(need adapter source contrast)"
        )

    iceoryx = root / ICEORYX_VENDOR_REL
    if iceoryx.exists():
        failures.append(
            f"Hold tree must not be vendored: `{ICEORYX_VENDOR_REL.as_posix()}`"
        )
        lines.append(f"- **FAIL vendored:** `{ICEORYX_VENDOR_REL.as_posix()}`")
    else:
        lines.append(
            f"- **ok absent:** `{ICEORYX_VENDOR_REL.as_posix()}` "
            "(adapter source ≠ vendored Iceoryx)"
        )

    hold_text = texts.get(HOLD_REL)
    if hold_text is not None:
        ok_status, status_detail = _hold_status_ok(hold_text)
        if ok_status:
            lines.append(f"- **ok status header:** {status_detail}")
        else:
            failures.append(f"hold doc {status_detail}")
            lines.append(f"- **FAIL status:** {status_detail}")
        if "no zero-copy land" in hold_text:
            lines.append("- **ok freeze phrase:** `no zero-copy land`")
        else:
            failures.append("hold doc missing contiguous `no zero-copy land`")
            lines.append("- **FAIL zero-copy:** need `no zero-copy land`")
        if "no XML/SCOREBOARD" in hold_text:
            lines.append("- **ok freeze phrase:** `no XML/SCOREBOARD`")
        else:
            failures.append("hold doc missing `no XML/SCOREBOARD`")
            lines.append("- **FAIL XML/SCOREBOARD:** need `no XML/SCOREBOARD`")
        if "AUTO CMake ≠ zero-copy proven" in hold_text:
            lines.append("- **ok AUTO clause:** `AUTO CMake ≠ zero-copy proven`")
        else:
            failures.append("hold doc missing `AUTO CMake ≠ zero-copy proven`")
            lines.append("- **FAIL AUTO:** need `AUTO CMake ≠ zero-copy proven`")
        if "adapter source ≠ vendored Iceoryx" in hold_text:
            lines.append(
                "- **ok adapter clause:** `adapter source ≠ vendored Iceoryx`"
            )
        else:
            failures.append(
                "hold doc missing `adapter source ≠ vendored Iceoryx`"
            )
            lines.append(
                "- **FAIL adapter:** need `adapter source ≠ vendored Iceoryx`"
            )
        missing_phase = [m for m in ("《3》", "《4》", "《5》", "《6》") if m not in hold_text]
        if missing_phase:
            joined = ", ".join(missing_phase)
            failures.append(f"hold doc missing phase marker(s): {joined}")
            lines.append(f"- **FAIL 《3》–《6》:** need {joined}")
        else:
            lines.append("- **ok phase Hold:** 《3》–《6》")
        for hit in _fabricate_hits(hold_text):
            failures.append(f"hold doc positive claim: {hit}")
            lines.append(f"- **FAIL fabricate hold:** `{hit}`")
        invented = _PERCENTILE_RE.findall(hold_text)
        if invented:
            failures.append(
                "hold doc invents booked percentile token(s): "
                + ", ".join(sorted({str(m) for m in invented}))
            )
            lines.append("- **FAIL percentiles:** do not invent booked pNN tokens")
        else:
            lines.append("- **ok no invented booked percentile tokens**")
        for item in _status_self_check(hold_text):
            failures.append(item)
            lines.append(f"- **FAIL {item}**")

    for rel, label in (
        (ADR_REL, "ADR"),
        (SINK_REL, "sink-layers"),
        (CNJP_REL, "cn-jp"),
    ):
        text = texts.get(rel)
        if text is None:
            continue
        hits = _fabricate_hits(text)
        if hits:
            joined = ", ".join(hits)
            failures.append(f"{label} positive claim: {joined}")
            lines.append(f"- **FAIL fabricate {label}:** `{joined}`")
        else:
            lines.append(f"- **ok honesty {label}:** no PASS/PROVEN/Active land claim")

    lines.append("")
    lines.extend(
        [
            "Filesystem + Hold markers only. This is **not** an Iceoryx",
            "runtime, not a Loaned land, not a percentile, and not Feishu",
            "field proof. psmx_iox is adapter-source contrast; AUTO CMake",
            "is not zero-copy proven. fastdds.xml / SCOREBOARD are",
            "existence-only in this script; the boundary job owns the",
            "content freeze. Agnocast / zenoh stay Hold. 《3》–《6》 stay",
            "Hold. Three-chain / DoD stay unmet / blocked. Unitree drop-in",
            "stays FAIL. Cega / Bridge stays Hold.",
            "",
        ]
    )

    if failures:
        lines.append("FAIL:")
        for item in failures:
            lines.append(f"- {item}")
        lines.append("")
        lines.append(
            "Required memory Hold doc, no-zero-copy / no XML/SCOREBOARD "
            "marker, AUTO/adapter contrast, psmx_iox source, absent "
            "vendor/iceoryx, or pointer doc is gone, or the page "
            "fabricates PASS/PROVEN/Active / Iceoryx-running. Restore "
            "the docs (no XML) or the marker. Exit 1."
        )
        lines.append("")
        return "\n".join(lines), 1

    lines.append(f"- **{SUCCESS_MARKER}**")
    lines.append("")
    lines.append(
        "Memory layer Hold healthy: STATUS Hold, no zero-copy land, "
        "AUTO CMake ≠ zero-copy proven, adapter source ≠ vendored "
        "Iceoryx, no XML/SCOREBOARD, 《3》–《6》 Hold. Exit 0."
    )
    lines.append("")
    return "\n".join(lines), 0


def main() -> int:
    text, code = render()
    sys.stdout.write(text)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
