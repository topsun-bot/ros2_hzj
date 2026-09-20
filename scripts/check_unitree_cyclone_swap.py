#!/usr/bin/env python3
"""Assert Unitree SDK2 ↔ vendor Cyclone swap docs stay honest.

Vanilla box (no ROS): exit 0 when the swap doc + VERSIONS pin + quoted
0.10.2 marker are present. Missing file or expected marker: FAIL (exit 1).
On success print a line containing exactly: drop-in: FAIL / wire: UNPROVEN
On failure do not print that success marker.

Does not invent SHAs, percentiles, or claim wire interop was run.
Does not prove fastdds.xml / SCOREBOARD contents are unchanged —
those files are existence-only here; the `boundary` job owns the freeze.
Style follows scripts/check_runtime_provenance.py / check_risk_matrix.py.
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
from _repo import emit_render, repo_root, read_utf8


SWAP_REL = Path("docs/architecture/unitree-sdk2-dds-swap.md")
VERSIONS_REL = Path("vendor/VERSIONS.md")
CMAKE_REL = Path("vendor/CycloneDDS/CMakeLists.txt")

SUCCESS_MARKER = "drop-in: FAIL / wire: UNPROVEN"
DOC_VERDICT = "drop-in FAIL / wire UNPROVEN"

# Exact substrings the swap doc must keep. Verdict is one contiguous
# phrase so `drop-in PASS / wire PROVEN` cannot keep this gate green.
_SWAP_MARKERS = (
    "0.10.2",
    'DDS_VERSION "0.10.2"',
    "11.0.1",
    DOC_VERDICT,
    "fastdds.xml",
    "SCOREBOARD",
    "Agnocast",
    "zenoh",
    "vendor/VERSIONS.md",
    "libddsc",
    "libddscxx",
    "cyclonedds>=0.10.5",
    "/opt/ros/humble",
    "STATUS: blocked",
    "Unitree",
    "in-place overwrite",
    "bundled",
    "UNITREE_DDS_PROVIDER=external",
    "unitree_sdk2_hzj",
)

_VERSIONS_MARKERS = (
    "vendor/CycloneDDS/",
    "11.0.1",
    "e54e991f75a3e67f8e628da3171122e36ea5b872",
)

# project(CycloneDDS … VERSION 11.0.1 …) — not a loose VERSION 11.0.1.
_CMAKE_PROJECT_RE = re.compile(
    r"(?m)^\s*project\s*\(\s*CycloneDDS\b[^)\n]*\bVERSION\s+11\.0\.1\b"
)


def _versions_cyclone_row(text: str) -> tuple[bool, str]:
    pin_path, pin_ver, pin_sha = _VERSIONS_MARKERS
    hits = [
        line
        for line in text.splitlines()
        if pin_path in line and pin_ver in line and pin_sha in line
    ]
    if not hits:
        return (
            False,
            f"VERSIONS missing CycloneDDS {pin_ver} row with SHA {pin_sha}",
        )
    return True, f"vendor/CycloneDDS/ {pin_ver} SHA {pin_sha} on same row"


def _cmake_project_version(text: str) -> tuple[bool, str]:
    if _CMAKE_PROJECT_RE.search(text):
        return True, "project(CycloneDDS … VERSION 11.0.1 …)"
    return False, "CMakeLists missing project(CycloneDDS … VERSION 11.0.1 …)"


def render(root: Path | None = None) -> tuple[str, int]:
    root = (root or repo_root(SWAP_REL, VERSIONS_REL)).resolve()
    lines = [
        "# check_unitree_cyclone_swap (Unitree 0.10.2 vs vendor 11.0.1)",
        "",
    ]
    failures: list[str] = []

    # XML / SCOREBOARD: existence only. Content freeze is the `boundary` job.
    required = (
        (SWAP_REL, _SWAP_MARKERS, "contiguous verdict + Hold"),
        (VERSIONS_REL, (), "opened; Cyclone pin checked on the SHA row"),
        (CMAKE_REL, (), "opened; project() VERSION checked separately"),
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

    versions_text = texts.get(VERSIONS_REL)
    if versions_text is not None:
        ok, detail = _versions_cyclone_row(versions_text)
        if ok:
            lines.append(f"- **ok VERSIONS row:** {detail}")
        else:
            failures.append(detail)
            lines.append(f"- **FAIL VERSIONS row:** {detail}")

    cmake_text = texts.get(CMAKE_REL)
    if cmake_text is not None:
        ok, detail = _cmake_project_version(cmake_text)
        if ok:
            lines.append(f"- **ok CMake project():** {detail}")
        else:
            failures.append(detail)
            lines.append(f"- **FAIL CMake project():** {detail}")

    swap_text = texts.get(SWAP_REL)
    if swap_text is not None:
        quoted = 'DDS_VERSION "0.10.2"' in swap_text
        if quoted:
            lines.append('- **ok quoted 0.10.2:** `DDS_VERSION "0.10.2"`')
        else:
            failures.append('swap doc missing quoted DDS_VERSION "0.10.2"')
            lines.append("- **FAIL quote:** need `DDS_VERSION \"0.10.2\"`")
        if DOC_VERDICT in swap_text:
            lines.append(f"- **ok verdict phrase:** `{DOC_VERDICT}`")
        else:
            failures.append(f"swap doc missing contiguous `{DOC_VERDICT}`")
            lines.append(f"- **FAIL verdict:** need `{DOC_VERDICT}`")

    lines.append("")
    lines.extend(
        [
            "Filesystem + version markers only. This is **not** a loaded",
            "`.so` proof, not a percentile, and not Feishu field proof.",
            "Vendor SHA is read from the CycloneDDS 11.0.1 VERSIONS row,",
            "not invented here and not accepted from an unrelated line.",
            "drop-in of vendor 11.0.1 onto Unitree 0.10.2 is FAIL.",
            "Not an in-place overwrite: default stays bundled 0.10.2.",
            "Legal replace path is unitree_sdk2_hzj + opt-in",
            "UNITREE_DDS_PROVIDER=external. Wire interop stays UNPROVEN.",
            "fastdds.xml / SCOREBOARD are existence-only in this script;",
            "the boundary job owns the content freeze. Agnocast / zenoh",
            "stay Hold. Do not copy rolling vendor onto a robot or",
            "/opt/ros/humble.",
            "",
        ]
    )

    if failures:
        lines.append("FAIL:")
        for item in failures:
            lines.append(f"- {item}")
        lines.append("")
        lines.append(
            "Required swap doc, quoted Unitree 0.10.2, vendor 11.0.1 pin, "
            "contiguous verdict, or Hold marker is gone. Restore the "
            "docs (no XML) or the marker. Exit 1."
        )
        lines.append("")
        return "\n".join(lines), 1

    lines.append(f"- **{SUCCESS_MARKER}**")
    lines.append("")
    lines.append(
        "Unitree Cyclone swap record healthy: bundled 0.10.2 vs vendor "
        "11.0.1 is not drop-in; default stays bundled; legal path is "
        "unitree_sdk2_hzj + UNITREE_DDS_PROVIDER=external; wire interop "
        "remains UNPROVEN. Exit 0."
    )
    lines.append("")
    return "\n".join(lines), 0


def main() -> int:
    return emit_render(render())


if __name__ == "__main__":
    raise SystemExit(main())
