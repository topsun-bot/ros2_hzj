#!/usr/bin/env python3
"""AGENTS.md Commands-block <-> run_all_gates.GATES registry self-test (#40).

Context
-------
``AGENTS.md`` is the operator entry point: its ``## Commands`` bash block lists
the python entry points a human runs. ``scripts/run_all_gates.py`` is the
machine runner whose ``GATES`` tuple is the single source of truth for the gate
sequence. Round 5 added a 13th gate (``check_frozen_path_literals.py``) and the
CI wiring is blocked on a missing ``workflow`` scope, so the CI ``structure``
job still hard-codes only the first twelve gates -- the AGENTS.md command block
is the only place that documents the *full* local set for operators.

Round 44 found that the 13th gate had never been added to the AGENTS.md command
block: a gate could run green under ``run_all_gates.py`` while being invisible
in the operator checklist, and nothing failed. #29 pins the gate registry on
the ``scripts/`` side (disk gate scripts <-> GATES) and #35 pins the eval
registry (selftests <-> yaml <-> README counts); neither covers the operator
documentation surface. This test closes that gap.

It parses ONLY the fenced ``## Commands`` bash block (prose mentions of
``python3 ...`` elsewhere are not an enumeration), takes the first whitespace
token after ``python3`` (so ``load.py print-a`` / ``print-b`` collapse to one
script), and asserts:

  * every ``run_all_gates.GATES`` script is documented in the block (a gate the
    operator checklist does not know about is reported);
  * every script listed in the block exists on disk;
  * the only non-gate script allowed in the block is the manual env helper
    ``config/env/load.py`` (an exact allowlist, so unrelated commands cannot
    quietly accumulate, and a gate deleted from GATES but left documented is
    also caught).

It reads the REAL repo for the healthy case; all negatives mutate in memory
(no temp files, no repo edits).

Scenarios: 3 negative (a GATES row missing from AGENTS.md; an injected new
gate absent from AGENTS.md; a listed script missing on disk), 2 non-flag
(``load.py print-a/print-b`` collapse to one allowlisted manual script with
args stripped; ``python3 ...`` text outside the fenced Commands block is not
enumerated), 1 healthy (real repo: every gate documented, every listed script
on disk, exact manual allowlist), 1 mutation (force one real listed script to
look missing via an exists wrapper; it must be reported, proving the disk
check is not vacuous).
"""

from __future__ import annotations

import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import run_all_gates  # noqa: E402  (import after sys.path setup)

AGENTS_PATH = REPO_ROOT / "AGENTS.md"
SUCCESS_MARKER = "agents commands selftest: PASS"

# The only non-gate python entry point allowed in the operator Commands block.
MANUAL_NON_GATE = {"config/env/load.py"}

_BLOCK_RE = re.compile(r"## Commands\s*```bash\n(.*?)```", re.S)
_PY_LINE_RE = re.compile(r"(?m)^\s*python3\s+(\S+)")


def parse_listed_scripts(agents_text: str):
    """Return the ordered-unique python script paths in the Commands bash block.

    Only the fenced block under ``## Commands`` is parsed; the first token after
    ``python3`` is taken (subcommand args such as ``print-a`` are dropped).
    Raises ValueError if the block cannot be located.
    """
    m = _BLOCK_RE.search(agents_text)
    if not m:
        raise ValueError("AGENTS.md has no ## Commands fenced bash block")
    block = m.group(1)
    listed = []
    for lm in _PY_LINE_RE.finditer(block):
        path = lm.group(1).strip()
        if path not in listed:
            listed.append(path)
    return listed


def evaluate(gate_scripts, agents_text, root: pathlib.Path, exists=pathlib.Path.exists):
    """Return a list of problem strings for the gate<->AGENTS command registry.

    Pure/injectable: ``gate_scripts`` is the GATES path sequence, ``agents_text``
    is AGENTS.md contents, ``exists`` reports a resolved path's presence.
    """
    problems = []
    listed = parse_listed_scripts(agents_text)
    listed_set = set(listed)
    gate_set = set(gate_scripts)

    # 1) every gate must be documented in the operator block.
    for g in sorted(gate_set - listed_set):
        problems.append(f"gate missing from AGENTS.md Commands block: {g}")

    # 2) every listed script must exist on disk.
    for script in listed:
        if not exists((root / script).resolve()):
            problems.append(f"AGENTS.md Commands script missing on disk: {script}")

    # 3) the only documented non-gate script is the exact manual allowlist.
    extra = listed_set - gate_set
    if extra != MANUAL_NON_GATE:
        problems.append(
            "AGENTS.md Commands non-gate scripts "
            f"{sorted(extra)} != allowlist {sorted(MANUAL_NON_GATE)}"
        )
    return problems


def _real_inputs():
    gate_scripts = [path for path, _marker in run_all_gates.GATES]
    agents_text = AGENTS_PATH.read_text(encoding="utf-8")
    return gate_scripts, agents_text


def main() -> int:
    try:
        gate_scripts, agents_text = _real_inputs()
        listed = parse_listed_scripts(agents_text)

        # healthy: real repo is fully consistent.
        problems = evaluate(gate_scripts, agents_text, REPO_ROOT)
        assert problems == [], "real repo should be consistent: " + repr(problems)
        assert len(gate_scripts) >= 13, f"expected >=13 gates, got {len(gate_scripts)}"
        print(
            f"  ok healthy {len(gate_scripts)} gates all documented, "
            f"{len(listed)} listed commands (manual allowlist: load.py), 0 problems"
        )

        # N1: drop one real gate line from the AGENTS block -> must be reported.
        victim = "scripts/check_frozen_path_literals.py"
        assert victim in agents_text, "fixture: frozen gate line should be present"
        a1 = agents_text.replace(f"python3 {victim}\n", "")
        p1 = evaluate(gate_scripts, a1, REPO_ROOT)
        assert any(victim in x and "missing from AGENTS" in x for x in p1), p1
        print("  ok negative a GATES row dropped from AGENTS.md is reported")

        # N2: inject a brand-new gate that AGENTS.md does not document.
        ghost = "scripts/zzz_round45_ghost_gate.py"
        p2 = evaluate(list(gate_scripts) + [ghost], agents_text, REPO_ROOT)
        assert any(ghost in x and "missing from AGENTS" in x for x in p2), p2
        print("  ok negative an injected new gate absent from AGENTS.md is reported")

        # N3: a listed script (treated as a gate) that does not exist on disk.
        missing = "scripts/zzz_round45_missing.py"
        a3 = agents_text.replace("```\n", f"python3 {missing}\n```\n", 1)
        p3 = evaluate(list(gate_scripts) + [missing], a3, REPO_ROOT)
        assert any(missing in x and "missing on disk" in x for x in p3), p3
        assert not any("non-gate" in x for x in p3), p3
        print("  ok negative a Commands script missing on disk is reported")

        # NF1: load.py print-a/print-b collapse to one allowlisted manual script.
        nf1 = parse_listed_scripts(agents_text)
        assert nf1.count("config/env/load.py") == 1, nf1
        assert not any("print-a" in s or "print-b" in s for s in nf1), nf1
        assert set(nf1) - set(gate_scripts) == MANUAL_NON_GATE, nf1
        print("  ok non-flag load.py print-a/print-b collapse to one allowlisted manual script")

        # NF2: python3 text outside the fenced Commands block is not enumerated.
        prose = agents_text + "\nSome prose: run `python3 scripts/zzz_not_in_block.py` later.\n"
        nf2 = parse_listed_scripts(prose)
        assert "scripts/zzz_not_in_block.py" not in nf2, nf2
        assert nf2 == listed, "prose mention must not change the enumeration"
        print("  ok non-flag python3 text outside the fenced Commands block is ignored")

        # mutation: force one real listed gate script to look absent on disk.
        target = (REPO_ROOT / "scripts/prove_rmw.py").resolve()

        def exists_deny(dest: pathlib.Path) -> bool:
            return False if dest == target else pathlib.Path.exists(dest)

        pm = evaluate(gate_scripts, agents_text, REPO_ROOT, exists=exists_deny)
        assert any("prove_rmw.py" in x and "missing on disk" in x for x in pm), pm
        print("  ok mutation a real listed script forced missing is caught")

    except AssertionError as exc:
        print(SUCCESS_MARKER.replace("PASS", "FAIL") + f": {exc}")
        return 1
    except ValueError as exc:
        print(SUCCESS_MARKER.replace("PASS", "FAIL") + f": {exc}")
        return 1
    print(SUCCESS_MARKER)
    print("3 negative, 2 non-flag, 1 healthy, 1 mutation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
