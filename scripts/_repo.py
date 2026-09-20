#!/usr/bin/env python3
"""Shared repository-root lookup and UTF-8 text reading for gate scripts.

Every ``scripts/check_*.py`` historically carried its own private copy of
two small helpers:

* ``_repo_root()`` — resolve the repository root from the current working
  directory when run from the repo root, with a fallback to the parent of
  this ``scripts/`` directory; abort when neither location holds the
  anchor artifact(s).
* ``_read(path)`` — lenient UTF-8 read used for every markdown/source
  probe.
* ``line_at(text, index)`` — return the full source line containing a
  character index, used by same-line prohibition checks (a flagged token
  on the same line as its exemption sentence must not be reported).
* ``emit_render(result)`` — write a gate's rendered ``(text, exit_code)`` pair to
  stdout and return the exit code unchanged, so every gate keeps a one-line ``main()``.

This module is the single home for these (modernization plan §5.3
helper-boundary spec). It deliberately carries **no** business assertions:
each gate keeps its own anchor constants, required-marker sets, allowlists
and rendering. The underscore prefix keeps it out of the CI command list
(shared library, not a runnable gate).
"""

from __future__ import annotations

import sys
from pathlib import Path


def repo_root(*anchors: Path) -> Path:
    """Locate the repository root, anchored on one or more required files.

    Returns the current working directory when any anchor exists directly
    under it; otherwise the parent of this ``scripts/`` directory when any
    anchor exists there. Aborts (exit 1) if no anchor is found in either
    place, matching the previous per-script behavior.
    """
    if not anchors:
        raise ValueError("repo_root() requires at least one anchor path")
    cwd = Path.cwd()
    if any((cwd / anchor).is_file() for anchor in anchors):
        return cwd.resolve()
    here = Path(__file__).resolve().parent
    candidate = here.parent
    if any((candidate / anchor).is_file() for anchor in anchors):
        return candidate
    sys.exit(f"cannot find repo root from cwd={cwd} or {candidate}")


def read_utf8(path: Path) -> str:
    """Read a text file as UTF-8, replacing undecodable bytes (lenient)."""
    return path.read_text(encoding="utf-8", errors="replace")


def line_at(text: str, index: int) -> str:
    """Return the full line of ``text`` that contains character ``index``.

    The line spans from just after the previous newline (or start of text)
    to the next newline (or end of text), excluding the newline itself.
    """
    start = text.rfind("\n", 0, index) + 1
    end = text.find("\n", index)
    if end < 0:
        end = len(text)
    return text[start:end]

def emit_render(result: tuple[str, int]) -> int:
    """Write a gate's rendered ``(text, exit_code)`` pair to stdout.

    Returns the exit code unchanged so each gate's ``main()`` stays a
    one-liner: ``return emit_render(render())``.
    """
    text, exit_code = result
    sys.stdout.write(text)
    return exit_code
