#!/usr/bin/env python3
"""Assert underlay vs overlay vs vendor-snapshot docs stay consistent.

Vanilla box (no ROS): exit 0 when required files + Humble/rolling markers
and VERSIONS SHA rows are present.
Missing file or expected marker: FAIL (exit 1).
On success print a line containing exactly: underlay != vendor snapshot
On failure do not print that success marker.

Does not invent SHAs, percentiles, or risk scores. Style follows
scripts/check_risk_matrix.py / scripts/prove_rmw.py.
"""

from __future__ import annotations

from pathlib import Path
import re
from _repo import append_bullets, emit_render, repo_root, read_utf8, report_missing_file


PROVENANCE_REL = Path("docs/architecture/feishu-runtime-provenance.md")
MANIFEST_REL = Path("vendor/MANIFEST.md")
VERSIONS_REL = Path("vendor/VERSIONS.md")
DOCKERFILE_REL = Path("docker/ros/Dockerfile")
PROVE_RMW_REL = Path("scripts/prove_rmw.py")

SUCCESS_MARKER = "underlay != vendor snapshot"

# Humble underlay + rolling/master snapshot. Not scores, not SHAs.
_PROVENANCE_MARKERS = (
    "Underlay",
    "Overlay",
    "Vendor snapshot",
    "/opt/ros/humble",
    "AMENT_PREFIX_PATH",
    "Humble",
    "rolling",
    "master",
    "严禁覆盖",
    "Rolling ≠ Humble",
    "派生自",
    "Not Feishu field proof",
    "prove_rmw.py",
    "ROS_DISTRO=humble",
    "域 42",
    "域 0",
    "rmw_fastrtps_cpp",
    "rmw_cyclonedds_cpp",
)

_MANIFEST_MARKERS = (
    "Humble",
    "rolling",
    "master",
    "/opt/ros/humble",
    "严禁",
)

# Six vendor trees pinned in VERSIONS.md — structure only; do not invent SHAs.
_VERSIONS_ROWS = (
    "vendor/rmw/",
    "vendor/rmw_implementation/",
    "vendor/rmw_fastrtps/",
    "vendor/Fast-DDS/",
    "vendor/rmw_cyclonedds/",
    "vendor/CycloneDDS/",
)

_SHA_RE = re.compile(r"\b[0-9a-f]{40}\b")
_ENV_DISTRO_RE = re.compile(
    r"(?im)^\s*ENV\s+ROS_DISTRO(?:=|\s+)[\"']?(\w+)[\"']?\s*$"
)


def _dockerfile_pins_humble(text: str) -> tuple[bool, str]:
    found = _ENV_DISTRO_RE.findall(text)
    if not found:
        if re.search(r"(?im)^\s*ENV\s+ROS_DISTRO\b", text):
            return False, "Dockerfile ENV ROS_DISTRO is not humble"
        return False, "Dockerfile missing ENV ROS_DISTRO=humble"
    bad = [value for value in found if value != "humble"]
    if bad:
        return False, f"Dockerfile ENV ROS_DISTRO pins {', '.join(bad)} (need humble)"
    return True, "ENV ROS_DISTRO=humble"


def _versions_rows(text: str) -> list[str]:
    missing: list[str] = []
    for row in _VERSIONS_ROWS:
        hits = [
            line
            for line in text.splitlines()
            if row in line and _SHA_RE.search(line)
        ]
        if not hits:
            missing.append(row)
    return missing


def render(root: Path | None = None) -> tuple[str, int]:
    root = (root or repo_root(PROVENANCE_REL, MANIFEST_REL)).resolve()
    lines = [
        "# check_runtime_provenance (wiki3 §13 underlay vs vendor)",
        "",
    ]
    failures: list[str] = []

    required_files = (
        MANIFEST_REL,
        VERSIONS_REL,
        DOCKERFILE_REL,
        PROVENANCE_REL,
        PROVE_RMW_REL,
    )
    texts: dict[Path, str] = {}
    for rel in required_files:
        path = root / rel
        key = rel.as_posix()
        if not path.is_file():
            report_missing_file(failures, lines, key)
            continue
        texts[rel] = read_utf8(path)
        extra = ""
        if rel == PROVE_RMW_REL:
            extra = " (wiki3 §6.3 identity; not vendor path)"
        lines.append(f"- **ok file:** `{key}`{extra}")

    docker_text = texts.get(DOCKERFILE_REL)
    if docker_text is not None:
        ok, detail = _dockerfile_pins_humble(docker_text)
        if ok:
            lines.append(f"- **ok Dockerfile:** {detail}")
        else:
            failures.append(detail)
            lines.append(f"- **FAIL Dockerfile:** {detail}")

    marker_specs = (
        (MANIFEST_REL, _MANIFEST_MARKERS, "Humble underlay + rolling/master snapshot"),
        (PROVENANCE_REL, _PROVENANCE_MARKERS, "underlay / overlay / vendor snapshot"),
    )
    for rel, markers, hint in marker_specs:
        text = texts.get(rel)
        if text is None:
            continue
        key = rel.as_posix()
        missing_markers = [m for m in markers if m not in text]
        if missing_markers:
            joined = ", ".join(missing_markers)
            failures.append(f"`{key}` missing marker(s): {joined}")
            lines.append(f"- **FAIL markers:** `{key}` (need {joined})")
        else:
            lines.append(f"- **ok markers:** `{key}` ({hint})")

    versions_text = texts.get(VERSIONS_REL)
    if versions_text is not None:
        missing_rows = _versions_rows(versions_text)
        if missing_rows:
            joined = ", ".join(missing_rows)
            failures.append(f"VERSIONS missing SHA row(s): {joined}")
            lines.append(f"- **FAIL VERSIONS rows:** {joined}")
        else:
            lines.append(
                f"- **ok VERSIONS rows:** {len(_VERSIONS_ROWS)} vendor SHA tables present"
            )

    lines.append("")
    lines.extend(
        [
            "Filesystem + Humble/rolling markers only. This is **not** a loaded",
            "`.so` proof, not a percentile, and not Feishu field proof.",
            "Vendor SHA values are not invented here; only row structure is",
            "checked. fastdds.xml / SCOREBOARD stay untouched. Cross-host",
            "stays blocked. Rolling ≠ Humble.",
            "",
        ]
    )

    if failures:
        lines.append("FAIL:")
        append_bullets(lines, failures)
        lines.append("")
        lines.append(
            "Required provenance file, Humble underlay pin, rolling/master "
            "marker, or VERSIONS SHA row is gone. Restore the docs (no XML) "
            "or the marker. Exit 1."
        )
        lines.append("")
        return "\n".join(lines), 1

    lines.append(f"- **{SUCCESS_MARKER}**")
    lines.append("")
    lines.append(
        "Runtime provenance healthy: Humble underlay, overlay-if-present, "
        "and vendor snapshot stay distinct. Exit 0."
    )
    lines.append("")
    return "\n".join(lines), 0


def main() -> int:
    return emit_render(render())


if __name__ == "__main__":
    raise SystemExit(main())
