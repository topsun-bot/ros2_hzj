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
import sys


HOLD_REL = Path("docs/architecture/feishu-cega-bridge-hold.md")
ADR_REL = Path("docs/architecture/feishu-middleware-adr.md")
XML_REL = Path("config/fastdds.xml")
SCOREBOARD_REL = Path("docs/artifacts/bench/SCOREBOARD.md")

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

# ADR §13(4) row must stay Hold. Require the section + Cega + Hold.
_ADR_MARKERS = (
    "§13",
    "Cega / Bridge",
    "Hold",
    "不接 Cega",
    "dimos_bridge",
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
        (ADR_REL, _ADR_MARKERS, "§13(4) Cega / Bridge still Hold"),
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

    hold_text = texts.get(HOLD_REL)
    if hold_text is not None:
        if "STATUS: Hold" in hold_text:
            lines.append("- **ok status phrase:** `STATUS: Hold`")
        else:
            failures.append("hold doc missing contiguous `STATUS: Hold`")
            lines.append("- **FAIL status:** need `STATUS: Hold`")
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
