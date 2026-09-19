#!/usr/bin/env python3
"""Stdout fingerprint regression for the gate commands (eval-only, not a gate).

Invoked by the Promptfoo local-script provider (eval case #17). It lives under
``evals/`` on purpose: it is **not** one of the 13 CI gates, is not enumerated
by ``scripts/run_all_gates.py``, and needs no ``.github/workflows/ci.yml``
wiring (so it is not blocked by the GitHub ``workflow`` token scope).

What it guards
--------------
``run_all_gates`` only checks exit code + one success marker per gate. It
cannot see unintended drift anywhere else in a gate's stdout: a dropped or
added ``ok`` line, a changed count, or a rewritten verdict sentence that still
exits 0 with the marker present would all pass. This check captures the full,
normalized stdout of every gate command plus ``config/env/load.py print-a|b``
and compares it byte-for-byte against a committed fixture under
``evals/fixtures/``.

It complements, and does not duplicate, the existing layers:
  * ``run_all_gates`` -> exit code + marker (red/green);
  * Promptfoo ``contains`` assertions -> key contract phrases must be present
    (loose, catches flipped/removed verdicts);
  * this fingerprint -> the whole stdout must equal the reviewed baseline
    (strict, catches any other drift).

Intended, reviewed stdout changes are real review events. After such a change,
regenerate the fixtures and commit them in the same PR:

    python3 evals/fingerprint_check.py --update

Normalization (environment/noise only, never contract text)
-----------------------------------------------------------
  * the repo-root absolute path -> ``<REPO_ROOT>`` (e.g. the print-a
    ``FASTRTPS_DEFAULT_PROFILES_FILE=.../config/fastdds.xml`` line), so the
    fixtures are portable across clone locations and CI;
  * ``check_frozen_path_literals`` dynamic ``**ok scanned:** N`` -> ``<N>``:
    N counts top-level ``scripts/*.py`` and changes whenever a helper or gate
    file is added, which is file-count noise already covered by the
    ``run_all_gates`` GATES list. Every other count (e.g. source-map cited
    paths / allowlisted symbols) is left exact, because it reflects reviewed
    map/vendor content rather than the environment.

Read-only by default: it never edits repo files except with explicit
``--update``.
"""

from __future__ import annotations

import argparse
import difflib
import re
import subprocess
import sys
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent
ROOT = EVALS_DIR.parent
SCRIPTS = ROOT / "scripts"
FIX_DIR = EVALS_DIR / "fixtures"

# Single source of truth for the gate command list.
sys.path.insert(0, str(SCRIPTS))
from run_all_gates import GATES  # noqa: E402  (sys.path set just above)

# (fixture name, argv run from repo root). The 13 gates come from
# run_all_gates.GATES; the two load.py subcommands are added so the dual-chain
# executable source of truth is fingerprinted as well.
COMMANDS: list[tuple[str, list[str]]] = [
    (Path(rel).stem, [sys.executable, rel]) for rel, _marker in GATES
]
COMMANDS.extend(
    [
        ("load_print_a", [sys.executable, "config/env/load.py", "print-a"]),
        ("load_print_b", [sys.executable, "config/env/load.py", "print-b"]),
    ]
)

# check_frozen_path_literals prints: "- **ok scanned:** 15 top-level ...".
_SCANNED_COUNT_RE = re.compile(r"(\*\*ok scanned:\*\* )\d+")

# Cap per-command unified-diff output so a real drift cannot flood the log.
_DIFF_LINES_CAP = 60

STABLE_MARKER = "stdout fingerprint: stable"


def normalize(text: str) -> str:
    """Normalize only environment/noise; never rewrite contract phrases."""
    text = text.replace(str(ROOT), "<REPO_ROOT>")
    text = _SCANNED_COUNT_RE.sub(r"\1<N>", text)
    return text


def run_command(argv: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        argv,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def render_diff(name: str, baseline: str, live: str) -> str:
    diff = difflib.unified_diff(
        baseline.splitlines(keepends=True),
        live.splitlines(keepends=True),
        fromfile=f"evals/fixtures/{name}.txt",
        tofile=f"live:{name}",
        n=2,
    )
    lines = "".join(diff).splitlines()
    if len(lines) > _DIFF_LINES_CAP:
        lines = lines[:_DIFF_LINES_CAP] + [
            f"... ({len(lines) - _DIFF_LINES_CAP} more diff lines omitted)"
        ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--update",
        action="store_true",
        help="regenerate evals/fixtures/*.txt from current stdout",
    )
    args = parser.parse_args(argv)

    FIX_DIR.mkdir(exist_ok=True)

    if args.update:
        for name, cmd in COMMANDS:
            code, out, err = run_command(cmd)
            if code != 0:
                sys.stderr.write(
                    f"refusing to update fixture for {name}: command exited "
                    f"{code}\n{err}\n"
                )
                return 1
            (FIX_DIR / f"{name}.txt").write_text(normalize(out), encoding="utf-8")
        print("# stdout fingerprint check")
        print(f"- **updated:** {len(COMMANDS)} fixtures under `evals/fixtures/`")
        print("- run without `--update` to verify them.")
        return 0

    failures: list[str] = []
    matched = 0
    for name, cmd in COMMANDS:
        code, out, err = run_command(cmd)
        fixture_path = FIX_DIR / f"{name}.txt"
        if code != 0:
            failures.append(
                f"- **FAIL command exit {code}:** `{name}`\n\n```\n{err.strip()}\n```"
            )
            continue
        if not fixture_path.exists():
            failures.append(
                f"- **FAIL missing fixture:** `{name}` — run "
                f"`python3 evals/fingerprint_check.py --update`"
            )
            continue
        baseline = fixture_path.read_text(encoding="utf-8")
        live = normalize(out)
        if live != baseline:
            failures.append(
                f"- **FAIL stdout drift:** `{name}`\n\n```diff\n"
                f"{render_diff(name, baseline, live)}\n```"
            )
        else:
            matched += 1

    print("# stdout fingerprint check")
    print(f"- **commands:** {len(COMMANDS)}")
    if failures:
        print("\n".join(failures))
        print(
            f"\nstdout fingerprint: DRIFT ({matched}/{len(COMMANDS)} stable). "
            "If this is a reviewed, intentional output change, regenerate with "
            "`python3 evals/fingerprint_check.py --update` and commit the "
            "fixtures in the same PR."
        )
        return 1

    print(
        f"- **{STABLE_MARKER}** ({matched} commands match `evals/fixtures/`; "
        "repo-root path and frozen scanned count normalized)"
    )
    print(
        "\nRead-only regression: full gate/load.py stdout equals the committed "
        "baseline. Exit 0."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
