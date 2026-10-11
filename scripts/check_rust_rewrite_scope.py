#!/usr/bin/env python3
"""Assert the Rust rewrite-scope decision stays inside repo Holds.

Vanilla box (no ROS): exit 0 when the scope doc names the survey
handoff (rclrs + rosidl_rust as references; DDS study-only; no
rmw_zenoh; FastDDS 42 / Cyclone 0 stay) and does not claim 10x met.
Missing file, missing marker, or a positive 10x/adopt claim: FAIL
(exit 1). On success print a line containing exactly:
    rust rewrite scope: decided (10× unmet)
On failure do not print that success marker.

Does not vendor Rust, start an rmw, or edit fastdds.xml / SCOREBOARD.
Those two files are existence-only here; the `boundary` job owns the
freeze. Style follows scripts/check_sink_layers.py /
check_cega_bridge_hold.py.
"""

from __future__ import annotations

from pathlib import Path
import re

from _freeze_paths import (
    FASTDDS_XML_REL as XML_REL,
    SCOREBOARD_EXISTENCE_NOTE,
    SCOREBOARD_REL,
    XML_EXISTENCE_NOTE,
)
from _repo import append_failures_block, emit_render, line_at, repo_root, read_utf8, report_missing_file


SCOPE_REL = Path("docs/architecture/rust-rewrite-scope.md")
ADR_REL = Path("docs/architecture/feishu-middleware-adr.md")

SUCCESS_MARKER = "rust rewrite scope: decided (10× unmet)"

# Decision cell substrings. A lone layer name is not enough.
_DECISIONS = (
    ("client", "reference rclrs"),
    ("codegen", "reference rosidl_rust"),
    ("rcl", "keep C rcl"),
    ("rmw", "no custom RMW"),
    ("DDS", "study-only"),
    ("executor", "keep C wait set"),
    ("memory", "no SHM rewrite"),
)

_LAYER_ROW_RE = re.compile(
    r"(?m)^\|\s*\*\*(client|codegen|rcl|rmw|DDS|executor|memory)\*\*\s*\|"
    r"\s*([^|]*?)\s*\|"
)

# Contiguous policy phrases. Split tokens would let a rewrite keep
# "rclrs" and "zenoh" while dropping the actual decision.
_SCOPE_MARKERS = (
    "reference rclrs",
    "reference rosidl_rust",
    "keep C rcl",
    "no custom RMW",
    "study-only",
    "keep C wait set",
    "no SHM rewrite",
    "DDS interop is study-only",
    "do not adopt rmw_zenoh",
    "do not replace FastDDS 42 / Cyclone 0",
    "10×: unmet",
    "user confirmation open",
    "task ⑤ out of this change",
    "task ⑥ out of this change",
    "⑤–⑩ scope draftable",
    "not adopted",
    "no Cega",
    "no dimos_bridge runtime edits this cut",
    "no XML/SCOREBOARD",
    "《3》–《6》",
    "rmw_fastrtps_cpp",
    "rmw_cyclonedds_cpp",
    "Not Feishu field proof",
)

_ADR_MARKERS = (
    "不自研 RMW",
    "rust-rewrite-scope.md",
)

# Must not exist: this cut does not start a crate or a zenoh/Agnocast tree.
_ABSENT = (
    Path("Cargo.toml"),
    Path("vendor/rmw_zenoh"),
    Path("vendor/agnocast"),
)

_PROHIBITION_RE = re.compile(
    r"(do not|not adopt|not adopted|不得|不要|不采纳|不换|out of this change|"
    r"不是|不会|禁止)",
    re.IGNORECASE,
)

# Positive claims. The required "do not …" lines match these patterns
# and are skipped when the same line is a prohibition.
_FABRICATE_RES = (
    re.compile(r"10×:\s*met\b"),
    re.compile(r"10×:\s*PASS\b"),
    re.compile(r"(?i)adopt rmw_zenoh"),
    re.compile(r"(?i)replace FastDDS 42"),
    re.compile(r"(?i)custom RMW:\s*yes"),
)


def _decision_cells(text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for match in _LAYER_ROW_RE.finditer(text):
        found[match.group(1)] = match.group(2).strip()
    return found


def _missing_decisions(text: str) -> list[str]:
    cells = _decision_cells(text)
    missing: list[str] = []
    for name, needle in _DECISIONS:
        cell = cells.get(name)
        if cell is None or needle not in cell:
            missing.append(f"{name}={needle}")
    return missing


def _fabricate_hits(text: str) -> list[str]:
    hits: list[str] = []
    for pattern in _FABRICATE_RES:
        for match in pattern.finditer(text):
            if _PROHIBITION_RE.search(line_at(text, match.start())):
                continue
            hits.append(match.group(0).strip())
    return hits


def _first_status_line(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("Status:"):
            return line
    return None


def _status_ok(line: str | None) -> bool:
    if line is None:
        return False
    if "10× unmet" not in line or "user confirmation open" not in line:
        return False
    if re.search(r"(?i)\b(Done|PASS|met)\b", line) and "unmet" not in line:
        return False
    return True


def _row_self_check(scope_text: str) -> list[str]:
    """In-memory mutations must fail. Do not write the repo."""
    fails: list[str] = []
    flipped = scope_text.replace(
        "| **DDS** | study-only |",
        "| **DDS** | replace FastDDS |",
        1,
    )
    if not _missing_decisions(flipped):
        fails.append("self-check: DDS study-only flip still matched")
    adopted = scope_text + "\nWe adopt rmw_zenoh as the robot RMW.\n"
    if not _fabricate_hits(adopted):
        fails.append("self-check: bare 'adopt rmw_zenoh' was not flagged")
    met = scope_text + "\n10×: met on this host.\n"
    if not _fabricate_hits(met):
        fails.append("self-check: bare '10×: met' was not flagged")
    return fails


def render(root: Path | None = None) -> tuple[str, int]:
    root = (root or repo_root(SCOPE_REL, ADR_REL)).resolve()
    lines = [
        "# check_rust_rewrite_scope (task ③ rewrite scope)",
        "",
    ]
    failures: list[str] = []

    required = (
        (SCOPE_REL, _SCOPE_MARKERS, "layer decisions + 10× unmet + Holds"),
        (ADR_REL, _ADR_MARKERS, "no custom RMW; points at this scope doc"),
        (XML_REL, (), XML_EXISTENCE_NOTE),
        (SCOREBOARD_REL, (), SCOREBOARD_EXISTENCE_NOTE),
    )
    texts: dict[Path, str] = {}
    for rel, markers, hint in required:
        path = root / rel
        key = rel.as_posix()
        if not path.is_file():
            report_missing_file(failures, lines, key)
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

    scope_text = texts.get(SCOPE_REL)
    if scope_text is not None:
        status = _first_status_line(scope_text)
        if _status_ok(status):
            lines.append(
                "- **ok status header:** first `Status:` keeps "
                "`10× unmet` and `user confirmation open`"
            )
        else:
            failures.append(
                "scope doc first Status line must contain "
                "`10× unmet` and `user confirmation open`"
            )
            lines.append(
                "- **FAIL status:** first `Status:` must contain "
                "`10× unmet` and `user confirmation open`"
            )
        missing_layers = _missing_decisions(scope_text)
        if missing_layers:
            joined = ", ".join(missing_layers)
            failures.append(f"scope doc decision cell(s) missing: {joined}")
            lines.append(f"- **FAIL layers:** need {joined}")
        else:
            lines.append(
                "- **ok layers:** client=reference rclrs; "
                "codegen=reference rosidl_rust; rcl=keep C rcl; "
                "rmw=no custom RMW; DDS=study-only; "
                "executor=keep C wait set; memory=no SHM rewrite"
            )
        for item in _row_self_check(scope_text):
            failures.append(item)
            lines.append(f"- **FAIL {item}**")
        for hit in _fabricate_hits(scope_text):
            failures.append(f"scope doc positive claim: {hit}")
            lines.append(f"- **FAIL fabricate scope:** `{hit}`")
        if "DDS interop is study-only" in scope_text:
            lines.append("- **ok DDS:** `DDS interop is study-only`")
        else:
            failures.append("scope doc missing `DDS interop is study-only`")
            lines.append("- **FAIL DDS:** need `DDS interop is study-only`")
        if "do not adopt rmw_zenoh" in scope_text:
            lines.append("- **ok zenoh:** `do not adopt rmw_zenoh`")
        else:
            failures.append("scope doc missing `do not adopt rmw_zenoh`")
            lines.append("- **FAIL zenoh:** need `do not adopt rmw_zenoh`")
        if "10×: unmet" in scope_text:
            lines.append("- **ok 10×:** `10×: unmet`")
        else:
            failures.append("scope doc missing `10×: unmet`")
            lines.append("- **FAIL 10×:** need `10×: unmet`")

    for rel in _ABSENT:
        path = root / rel
        key = rel.as_posix()
        if path.exists():
            failures.append(f"rewrite artifact must not be present: `{key}`")
            lines.append(f"- **FAIL present:** `{key}`")
        else:
            lines.append(f"- **ok absent:** `{key}`")

    lines.append("")
    lines.extend(
        [
            "Filesystem + scope markers only. This is **not** a Rust",
            "middleware, not a percentile, and not Feishu field proof.",
            "Client/codegen may reference rclrs + rosidl_rust. DDS",
            "interop is study-only. do not adopt rmw_zenoh. do not",
            "replace FastDDS 42 / Cyclone 0. Tasks ⑤ and ⑥ stay out of",
            "this change. 10× stays unmet until a measured baseline",
            "exists. fastdds.xml / SCOREBOARD are existence-only; the",
            "boundary job owns the content freeze.",
            "",
        ]
    )

    if failures:
        append_failures_block(lines, failures)
        lines.append(
            "Required scope doc, layer decision, 10× unmet marker, "
            "or Hold phrase is gone, or a Rust/zenoh artifact appeared. "
            "Restore the doc (no XML) or the marker. Exit 1."
        )
        lines.append("")
        return "\n".join(lines), 1

    lines.append(f"- **{SUCCESS_MARKER}**")
    lines.append("")
    lines.append(
        "Rust rewrite scope healthy: reference rclrs, reference "
        "rosidl_rust, DDS study-only, no custom RMW, do not adopt "
        "rmw_zenoh, do not replace FastDDS 42 / Cyclone 0, "
        "10× unmet, user confirmation open. Exit 0."
    )
    lines.append("")
    return "\n".join(lines), 0


def main() -> int:
    return emit_render(render())


if __name__ == "__main__":
    raise SystemExit(main())
