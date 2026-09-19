#!/usr/bin/env python3
"""Negative self-test for the frozen-path-literal guard (eval-only, not a gate).

Invoked by the Promptfoo local-script provider. It lives under ``evals/`` on
purpose, like ``fingerprint_check.py``: it is **not** one of the 13 CI gates,
is not enumerated by ``scripts/run_all_gates.py``, and needs no
``.github/workflows/ci.yml`` wiring (so it is not blocked by the GitHub
``workflow`` token scope).

Why this exists
---------------
``scripts/check_frozen_path_literals.py`` is a *regression guard*: its value is
that it fails (exit 1) when a gate script re-hardcodes
``config/fastdds.xml`` / ``SCOREBOARD.md`` inside a ``pathlib.Path(...)``
constructor. The normal green run only proves the current tree is clean; it
cannot prove the detector still fires. If someone widened the regex (or broke
the render/exemption logic) so the guard never triggered, every positive run
would stay green while the protection silently vanished. During iteration 4
this negative behaviour was verified only with throwaway ``/tmp`` fixtures;
this script commits that evidence as a re-runnable regression.

It asserts three things, using the guard's own pure ``_hits_in`` detector and
its injectable ``render(root=...)``:
  1. must-flag snippets (frozen paths inside ``Path(...)``, incl. r/f prefixes,
     single/double quotes, short SCOREBOARD form) ARE detected, with the right
     line number;
  2. non-flag snippets (importing the constant, ``Path(CONST)``, ``endswith``
     suffix checks, output prose, regex strings, unrelated paths) are NOT
     flagged (no false positives);
  3. end-to-end ``render`` on a temporary fake ``scripts/`` tree returns
     exit 1 + no success marker + a ``bad_gate.py:<line>`` failure when a bad
     file is present (and the exempt ``_freeze_paths.py`` is never flagged),
     then exit 0 + the marker once the bad file is removed.

Read-only: it creates files only inside a ``tempfile`` directory and never
edits the repo. Standard library only. Exit 0 when every expectation holds,
exit 1 (with details) otherwise.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent
ROOT = EVALS_DIR.parent
SCRIPTS = ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS))
import check_frozen_path_literals as fg  # noqa: E402  (sys.path set just above)

# --- 1. Snippets the detector MUST flag (frozen path inside Path(...)) -------
# Each entry is (label, source, expected_line_of_first_hit).
MUST_FLAG: list[tuple[str, str, int]] = [
    ("plain double quote", 'x = Path("config/fastdds.xml")\n', 1),
    ("plain scoreboard", 'p = Path("docs/artifacts/bench/SCOREBOARD.md")\n', 1),
    ("r-prefix", 'x = Path(r"config/fastdds.xml")\n', 1),
    ("f-prefix scoreboard", 'p = Path(f"docs/artifacts/bench/SCOREBOARD.md")\n', 1),
    ("single quote, line 3", "# header\n# another\nx = Path('config/fastdds.xml')\n", 3),
    ("short scoreboard form", 'p = Path("artifacts/bench/SCOREBOARD.md")\n', 1),
]

# --- 2. Snippets the detector MUST NOT flag (no second Path(...) source) -----
NON_FLAG: list[tuple[str, str]] = [
    ("import constant", "from _freeze_paths import FASTDDS_XML_REL\n"),
    ("Path of constant", "xml_path = Path(FASTDDS_XML_REL)\n"),
    ("Path of scoreboard constant", "sb = Path(SCOREBOARD_REL)\n"),
    (
        "endswith suffix check",
        'if not p.as_posix().endswith("config/fastdds.xml"):\n    raise SystemExit(1)\n',
    ),
    ("output prose", 'print("do not edit config/fastdds.xml; it is frozen")\n'),
    (
        "detector regex pattern string",
        'RE = re.compile(r\'Path\\(\\s*["\\\']config/fastdds\\.xml\')\n',
    ),
    ("unrelated path", 'helper = Path("scripts") / "_freeze_paths.py"\n'),
]

SUCCESS_MARKER = "frozen guard selftest: PASS"


def _check_unit_detector(failures: list[str]) -> tuple[int, int]:
    must_hits = 0
    for label, source, expected_line in MUST_FLAG:
        hits = fg._hits_in(source)
        if not hits:
            failures.append(f"must-flag '{label}': detector found NO hit")
            continue
        line_no, _snippet = hits[0]
        if line_no != expected_line:
            failures.append(
                f"must-flag '{label}': expected line {expected_line}, got {line_no}"
            )
            continue
        must_hits += 1

    non_flag_hits = 0
    for label, source in NON_FLAG:
        hits = fg._hits_in(source)
        if hits:
            failures.append(
                f"non-flag '{label}': unexpected hit {hits!r}"
            )
            continue
        non_flag_hits += 1

    return must_hits, non_flag_hits


def _write(dir_: Path, name: str, text: str) -> Path:
    path = dir_ / name
    path.write_text(text, encoding="utf-8")
    return path


def _check_render(tmp: Path, failures: list[str]) -> int:
    scripts_dir = tmp / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    # The exempt definition site: it DOES hardcode the paths inside Path(...),
    # but it must never be flagged because it is the single source of truth.
    _write(
        scripts_dir,
        fg.HELPER_NAME,
        'from pathlib import Path\n'
        'FASTDDS_XML_REL = Path("config/fastdds.xml")\n'
        'SCOREBOARD_REL = Path("docs/artifacts/bench/SCOREBOARD.md")\n',
    )
    # A clean gate: imports the constant, uses Path(CONST), endswith, prose.
    _write(
        scripts_dir,
        "ok_gate.py",
        "from pathlib import Path\n"
        "from _freeze_paths import FASTDDS_XML_REL\n"
        "p = Path(FASTDDS_XML_REL)\n"
        'assert p.as_posix().endswith("config/fastdds.xml")\n'
        'print("config/fastdds.xml is frozen")\n',
    )
    # A bad gate: offending constructor deliberately on line 2.
    bad = _write(
        scripts_dir,
        "bad_gate.py",
        "# bad gate\n"
        'x = Path("config/fastdds.xml")\n',
    )

    render_cases = 0

    # Case A: bad file present -> exit 1, no success marker, bad_gate.py:2 cited,
    # and the exempt helper is not reported.
    out_bad, code_bad = fg.render(root=tmp)
    # The FAIL summary renders one line per offender as
    # "- scripts/<name>:<line> hardcodes a frozen Path(...)". The exempt helper
    # legitimately hardcodes the paths, so it must never appear in that list;
    # its name does appear (in backticks) in the "ok scanned / exempt" prose.
    helper_fail_line = f"- scripts/{fg.HELPER_NAME}:"
    if code_bad != 1:
        failures.append(f"render with bad_gate: expected exit 1, got {code_bad}")
    elif fg.SUCCESS_MARKER in out_bad:
        failures.append("render with bad_gate: unexpectedly printed success marker")
    elif "bad_gate.py:2" not in out_bad:
        failures.append("render with bad_gate: did not cite `bad_gate.py:2`")
    elif helper_fail_line in out_bad:
        failures.append(f"render with bad_gate: exempt `{fg.HELPER_NAME}` was flagged")
    else:
        render_cases += 1

    # Case B: remove the bad file -> exit 0 and success marker present.
    bad.unlink()
    out_ok, code_ok = fg.render(root=tmp)
    if code_ok != 0:
        failures.append(f"render clean tree: expected exit 0, got {code_ok}")
    elif fg.SUCCESS_MARKER not in out_ok:
        failures.append("render clean tree: success marker missing")
    elif "ok_gate.py" in out_ok and "FAIL" in out_ok:
        failures.append("render clean tree: clean ok_gate.py was flagged")
    else:
        render_cases += 1

    return render_cases


def main() -> int:
    failures: list[str] = []

    must_hits, non_flag_hits = _check_unit_detector(failures)

    with tempfile.TemporaryDirectory(prefix="frozen_guard_selftest_") as tmp:
        render_cases = _check_render(Path(tmp), failures)

    print("# frozen-path-literal guard negative self-test")
    print(
        f"- must-flag cases detected: {must_hits}/{len(MUST_FLAG)}; "
        f"non-flag cases clean: {non_flag_hits}/{len(NON_FLAG)}; "
        f"render cases: {render_cases}/2"
    )

    if failures:
        print("\nFAIL:")
        for item in failures:
            print(f"- {item}")
        print(
            "\nThe frozen-path guard no longer behaves as specified. "
            f"Expected {SUCCESS_MARKER!r}. Exit 1."
        )
        return 1

    print(
        f"- **{SUCCESS_MARKER}** ({len(MUST_FLAG)} must-flag, "
        f"{len(NON_FLAG)} non-flag, 2 render cases)"
    )
    print(
        "\nThe guard fires on every forbidden Path(...) form, stays silent on "
        "allowed mentions, exempts the single-source helper, and render() "
        "returns the right exit code. Read-only, tempdir-only. Exit 0."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
