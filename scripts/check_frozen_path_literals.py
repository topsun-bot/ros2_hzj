#!/usr/bin/env python3
"""Assert gate scripts do not re-hardcode the frozen Hold paths.

Modernization plan §5.3 rule 1 (regression guard for Step 2): the frozen
Hold paths ``config/fastdds.xml`` and
``docs/artifacts/bench/SCOREBOARD.md`` have a single source in
``scripts/_freeze_paths.py`` (``FASTDDS_XML_REL`` / ``SCOREBOARD_REL``).
A gate script must not re-introduce its own ``Path("config/fastdds.xml")``
/ ``Path("...SCOREBOARD.md")`` constructor, or the "single source of
truth" de-duplication silently regresses.

Scope (deliberately narrow, to avoid flagging honest output text):
- Scans top-level ``scripts/*.py`` only (the gate / runner scripts), not
  ``scripts/bench/**`` or docs.
- Flags only a ``pathlib.Path(...)`` *constructor* whose string literal
  embeds a frozen path. Output markers, Hold prose, ``endswith(...)``
  suffix checks, and regex pattern strings are NOT path constructors and
  stay allowed (they do not create a second path source of truth).
- ``scripts/_freeze_paths.py`` is the definition site and is exempt; this
  checker is exempt as well (its detection patterns mention the names but
  never inside a ``Path(...)`` constructor).

Vanilla box (no ROS): exit 0 when no gate script hardcodes a frozen
Path(...); exit 1 when one does, printing file:line for each hit.
On success print a line containing exactly:
    Frozen-path literals healthy
On failure do not print that success marker.

Read-only. Does not edit any file, does not touch fastdds.xml /
SCOREBOARD.md content, and does not compile vendor.
Style follows scripts/check_dod_evidence.py / check_dual_chain_baseline.py.
"""

from __future__ import annotations

from pathlib import Path
import re

from _repo import append_bullets, append_failures_block, emit_render, repo_root, read_utf8

SCRIPTS_REL = Path("scripts")
HELPER_NAME = "_freeze_paths.py"
SELF_NAME = "check_frozen_path_literals.py"

# A pathlib.Path(...) constructor whose quoted literal embeds one of the
# frozen Hold paths. Optional string prefixes (r/b/u/f and rf/fr) allowed.
_FROZEN_PATH_RE = re.compile(
    r"Path\(\s*(?:[rRbBuUfF]{0,2})?(?P<q>['\"])"
    r"[^'\"\n]*(?:"
    r"config/fastdds\.xml"
    r"|(?:docs/artifacts/bench/|artifacts/bench/)?SCOREBOARD\.md"
    r")[^'\"\n]*(?P=q)"
)

SUCCESS_MARKER = "Frozen-path literals healthy"


def _hits_in(text: str) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    for match in _FROZEN_PATH_RE.finditer(text):
        line_no = text.count("\n", 0, match.start()) + 1
        line_start = text.rfind("\n", 0, match.start()) + 1
        line_end = text.find("\n", match.start())
        if line_end < 0:
            line_end = len(text)
        hits.append((line_no, text[line_start:line_end].strip()))
    return hits


def render(root: Path | None = None) -> tuple[str, int]:
    root = (root or repo_root(SCRIPTS_REL / HELPER_NAME)).resolve()
    scripts_dir = root / SCRIPTS_REL
    lines = [
        "# check_frozen_path_literals (modernization plan §5.3 rule 1)",
        "",
    ]
    failures: list[str] = []

    if not scripts_dir.is_dir():
        failures.append(f"missing directory `{SCRIPTS_REL.as_posix()}/`")
        lines.append(f"- **FAIL missing:** `{SCRIPTS_REL.as_posix()}/`")
    else:
        targets = sorted(
            p
            for p in scripts_dir.glob("*.py")
            if p.name not in (HELPER_NAME, SELF_NAME)
        )
        lines.append(
            f"- **ok scanned:** {len(targets)} top-level `scripts/*.py` "
            f"(exempt: `{HELPER_NAME}` is the single source, "
            f"`{SELF_NAME}` is this checker)"
        )
        for path in targets:
            text = read_utf8(path)
            for line_no, source in _hits_in(text):
                rel = path.relative_to(root).as_posix()
                failures.append(f"{rel}:{line_no} hardcodes a frozen Path(...)")
                lines.append(
                    f"- **FAIL literal:** `{rel}:{line_no}` embeds a frozen "
                    f"path in `Path(...)`; import `FASTDDS_XML_REL` / "
                    f"`SCOREBOARD_REL` from `{HELPER_NAME}` instead"
                )
                lines.append(f"  ```python")
                lines.append(f"  {source}")
                lines.append(f"  ```")

    lines.append("")
    lines.extend(
        [
            "Static regression guard only. Output markers, Hold prose,",
            "endswith() suffix checks and regex patterns may still mention",
            "the names; only a second pathlib.Path(...) source is forbidden.",
            "This checker does not edit files and does not own the content",
            "freeze (the `boundary` job does). Read-only, no vendor build.",
            "",
        ]
    )

    if failures:
        append_failures_block(lines, failures)
        lines.append(
            "A gate script re-hardcoded config/fastdds.xml or SCOREBOARD.md "
            "in a Path(...) constructor. Import the constant from "
            "_freeze_paths.py instead. Exit 1."
        )
        lines.append("")
        return "\n".join(lines), 1

    lines.append(f"- **{SUCCESS_MARKER}**")
    lines.append("")
    lines.append(
        "Frozen-path literals healthy: every gate script sources the Hold "
        "paths from _freeze_paths.py; no second Path(...) copy exists. Exit 0."
    )
    lines.append("")
    return "\n".join(lines), 0


def main() -> int:
    return emit_render(render())


if __name__ == "__main__":
    raise SystemExit(main())
