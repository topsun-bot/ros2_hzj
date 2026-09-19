#!/usr/bin/env python3
"""Shared frozen-path constants for the gate scripts.

Single source of truth for the two Hold-frozen repository paths and the
exact existence-only hint strings that appear in gate stdout. Other scripts
and CI assert on these strings byte-for-byte (see
docs/refactor/02-modernization-plan.md §2 contract list), so change them
here only together with the gates that consume them.

Underscore prefix: this is a helper module, not itself a CI gate. Do not add
it to the command list in docs/architecture/ci-cd-gates.md or
scripts/run_all_gates.py.
"""

from __future__ import annotations

from pathlib import Path

# The two frozen paths. Gates assert existence + selected markers only;
# content freeze itself is owned by the `boundary` CI job.
FASTDDS_XML_REL = Path("config/fastdds.xml")
SCOREBOARD_REL = Path("docs/artifacts/bench/SCOREBOARD.md")

# Exact hint strings printed after the frozen files' "ok file" lines.
XML_EXISTENCE_NOTE = "existence only; content freeze is boundary"
SCOREBOARD_EXISTENCE_NOTE = "existence only; numbers not read; freeze is boundary"
