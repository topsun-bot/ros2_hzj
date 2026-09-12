#!/usr/bin/env python3
"""Assert Unitree SDK2 ↔ vendor Cyclone swap docs stay honest.

Vanilla box (no ROS): exit 0 when the swap doc + VERSIONS pin + quoted
0.10.2 marker are present. Missing file or expected marker: FAIL (exit 1).
On success print a line containing exactly: drop-in: FAIL / wire: UNPROVEN
On failure do not print that success marker.

Does not invent SHAs, percentiles, or claim wire interop was run.
Style follows scripts/check_runtime_provenance.py / check_risk_matrix.py.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys


SWAP_REL = Path("docs/architecture/unitree-sdk2-dds-swap.md")
VERSIONS_REL = Path("vendor/VERSIONS.md")
CMAKE_REL = Path("vendor/CycloneDDS/CMakeLists.txt")
XML_REL = Path("config/fastdds.xml")
SCOREBOARD_REL = Path("docs/artifacts/bench/SCOREBOARD.md")

SUCCESS_MARKER = "drop-in: FAIL / wire: UNPROVEN"

# Exact substrings the swap doc must keep. Not scores, not invented SHAs.
_SWAP_MARKERS = (
    "0.10.2",
    'DDS_VERSION "0.10.2"',
    "11.0.1",
    "drop-in",
    "FAIL",
    "UNPROVEN",
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

_CMAKE_MARKERS = ("VERSION 11.0.1",)

_SHA_RE = re.compile(r"\b[0-9a-f]{40}\b")


def _repo_root() -> Path:
    cwd = Path.cwd()
    if (cwd / SWAP_REL).is_file() or (cwd / VERSIONS_REL).is_file():
        return cwd.resolve()
    here = Path(__file__).resolve().parent
    candidate = here.parent
    if (candidate / SWAP_REL).is_file() or (candidate / VERSIONS_REL).is_file():
        return candidate
    sys.exit(f"cannot find repo root from cwd={cwd} or {candidate}")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _versions_cyclone_row(text: str) -> tuple[bool, str]:
    hits = [
        line
        for line in text.splitlines()
        if "vendor/CycloneDDS/" in line and "11.0.1" in line and _SHA_RE.search(line)
    ]
    if not hits:
        return False, "VERSIONS missing CycloneDDS 11.0.1 SHA row"
    return True, "vendor/CycloneDDS/ 11.0.1 SHA row"


def render(root: Path | None = None) -> tuple[str, int]:
    root = (root or _repo_root()).resolve()
    lines = [
        "# check_unitree_cyclone_swap (Unitree 0.10.2 vs vendor 11.0.1)",
        "",
    ]
    failures: list[str] = []

    required = (
        (SWAP_REL, _SWAP_MARKERS, "drop-in FAIL / wire UNPROVEN + Hold"),
        (VERSIONS_REL, _VERSIONS_MARKERS, "vendor Cyclone 11.0.1 pin"),
        (CMAKE_REL, _CMAKE_MARKERS, "source snapshot VERSION 11.0.1"),
        (XML_REL, (), "read-only contract seed; content not edited"),
        (SCOREBOARD_REL, (), "current-best pointer; numbers not printed"),
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

    versions_text = texts.get(VERSIONS_REL)
    if versions_text is not None:
        ok, detail = _versions_cyclone_row(versions_text)
        if ok:
            lines.append(f"- **ok VERSIONS row:** {detail}")
        else:
            failures.append(detail)
            lines.append(f"- **FAIL VERSIONS row:** {detail}")

    swap_text = texts.get(SWAP_REL)
    if swap_text is not None:
        quoted = 'DDS_VERSION "0.10.2"' in swap_text
        if quoted:
            lines.append('- **ok quoted 0.10.2:** `DDS_VERSION "0.10.2"`')
        else:
            failures.append('swap doc missing quoted DDS_VERSION "0.10.2"')
            lines.append("- **FAIL quote:** need `DDS_VERSION \"0.10.2\"`")

    lines.append("")
    lines.extend(
        [
            "Filesystem + version markers only. This is **not** a loaded",
            "`.so` proof, not a percentile, and not Feishu field proof.",
            "Vendor SHA is read from VERSIONS.md, not invented here.",
            "drop-in of vendor 11.0.1 onto Unitree 0.10.2 is FAIL.",
            "Not an in-place overwrite: default stays bundled 0.10.2.",
            "Legal replace path is unitree_sdk2_hzj + opt-in",
            "UNITREE_DDS_PROVIDER=external. Wire interop stays UNPROVEN.",
            "fastdds.xml / SCOREBOARD stay untouched. Agnocast / zenoh",
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
            "or Hold marker is gone. Restore the docs (no XML) or the "
            "marker. Exit 1."
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
    text, code = render()
    sys.stdout.write(text)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
