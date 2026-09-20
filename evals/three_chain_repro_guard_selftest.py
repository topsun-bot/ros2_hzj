#!/usr/bin/env python3
r"""Negative self-test for the three-chain-reproduce guard (eval-only).

Invoked by the Promptfoo local-script provider. It lives under ``evals/`` on
purpose, like ``fingerprint_check.py`` and the other ``*_guard_selftest.py``
scripts: it is **not** one of the 13 CI gates, is not enumerated by
``scripts/run_all_gates.py``, and needs no ``.github/workflows/ci.yml`` wiring
(so it is not blocked by the GitHub ``workflow`` token scope).

Why this exists
---------------
``scripts/check_three_chain_repro.py`` guards wiki3 §13(2): the three-chain
reproduce record must stay honestly ``map ≠ reproduce`` / ``STATUS: blocked``
on a vanilla box with no ROS, and must never claim a fabricated
PASS/PROVEN reproduce. The positive eval case (#8) and the #17 stdout
fingerprint only prove the *current, healthy* doc renders green. They cannot
prove the guard's fabrication regexes still fire when they are secretly
loosened.

Scope is deliberately the guard's **unique** fabrication detection that no
earlier self-test covers. The DoD self-test (#23) and the Cega/Bridge Hold
self-test (#24) already pin the same *family* of mechanism (a STATUS-fabricate
regex plus a same-line prohibition exemption), but on different docs with
different regexes and different fabricated strings. This script pins the two
``_FABRICATE_RES`` patterns that are unique to the three-chain record, where
the tamper is an **extra contradictory sentence appended while every healthy
marker — including the contiguous ``map ≠ reproduce`` phrase and
``STATUS: blocked`` — stays in place**. In that shape the plain phrase/status
existence checks pass; only the fabrication regex can catch it:

  * N1 appends a bare ``map = reproduce`` (ASCII ``=``). The doc still contains
    ``map ≠ reproduce`` (U+2260), so the phrase check passes; only the regex
    ``\bmap\s*=\s*reproduce\b`` catches the contradiction.
  * N2 appends ``three-chain repro: PROVEN``, caught by the
    ``(three-chain repro|三条链复现) : (PASS|PROVEN|OK)`` regex (the sibling
    ``reproduce:`` regex deliberately does not match the short word ``repro``).

The marker-substring file checks and ``_has_three_chains`` are intentionally
not re-tested: they are direct ``token in text`` / marker-co-occurrence checks
whose stated design boundary is "filesystem + honesty markers only" (the guard
makes no claim of semantic chain validation). The same-line prohibition
exemption (``_PROHIBITION_RE`` + ``_line_at``) is pinned here on this guard's
own Chinese/English prohibition vocabulary, so a future tightening that
flagged a legitimate "do not write …" instruction would also go red.

Fixtures are built by **copying the six real files the guard reads** (the
reproduce status doc, source-map, WaitSet map, ADR, plus the existence-only
fastdds.xml / SCOREBOARD) into a temp tree, appending one sentence at a time to
the reproduce doc, and driving the injectable ``render(root=...)``. It asserts:
  1. two negative scenarios ARE caught (exit 1, no success marker,
     ``FAIL fabricate`` naming the fabricated string, and no collateral
     FAIL missing/markers/phrase/status/chains — the healthy markers survive);
  2. one non-flag scenario: a same-line prohibition sentence
     ("不要把 map = reproduce …") is exempt and the tree stays green;
  3. two healthy cases: the real repo ``render()`` and a pristine copied tree
     both exit 0 with the success marker;
  4. one mutation: neutralising the ``\bmap\s*=\s*reproduce\b`` regex (to a
     never-matching pattern) makes N1 slip through undetected (exit 0, no
     FAIL fabricate), and restoring it re-catches N1 (try/finally).

Read-only: files are created only inside a ``tempfile`` directory; the repo is
never written. Standard library only. Exit 0 when every expectation holds,
exit 1 (with details) otherwise.
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent
ROOT = EVALS_DIR.parent
SCRIPTS = ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS))
import check_three_chain_repro as g  # noqa: E402  (sys.path set just above)

SUCCESS_MARKER = "three-chain repro guard selftest: PASS"

# All six required files are copied verbatim (the content docs carry many
# contiguous markers; a hand-written minimal tree would rot and drift).
CONTENT_RELS = (
    g.REPRO_REL,
    g.MAP_REL,
    g.WAITSET_REL,
    g.ADR_REL,
    g.XML_REL,
    g.SCOREBOARD_REL,
)

# FAIL families that must NOT appear when only an extra sentence is appended
# (appending never removes a required marker).
_NO_COLLATERAL = (
    "FAIL missing",
    "FAIL markers",
    "FAIL phrase",
    "FAIL status",
    "FAIL chains",
)


def _seed_tree(tmp: Path, repro_append: str = "") -> None:
    """Copy the six real files into the temp tree; append one repro-doc line."""
    for rel in CONTENT_RELS:
        dst = tmp / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        text = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
        if rel == g.REPRO_REL and repro_append:
            text = text.rstrip("\n") + "\n" + repro_append + "\n"
        dst.write_text(text, encoding="utf-8")


def _render(repro_append: str = ""):
    with tempfile.TemporaryDirectory(prefix="tc_neg_") as d:
        tmp = Path(d)
        _seed_tree(tmp, repro_append)
        return g.render(root=tmp)


def _check_negatives(failures: list[str]) -> int:
    caught = 0

    def expect(label: str, appended: str, named: str) -> None:
        nonlocal caught
        out, code = _render(appended)
        ok = (
            code == 1
            and g.SUCCESS_MARKER not in out
            and "FAIL fabricate" in out
            and named in out
            and all(fam not in out for fam in _NO_COLLATERAL)
        )
        if ok:
            caught += 1
        else:
            collateral = [fam for fam in _NO_COLLATERAL if fam in out]
            failures.append(
                f"negative '{label}': not caught as expected "
                f"(code={code}, FAIL fabricate={'FAIL fabricate' in out}, "
                f"named={named in out}, collateral={collateral})"
            )

    # N1: ASCII `map = reproduce` while `map ≠ reproduce` still present.
    expect("extra 'map = reproduce' contradiction", "map = reproduce", "map = reproduce")
    # N2: a fabricated three-chain repro PROVEN claim.
    expect("extra 'three-chain repro: PROVEN'", "three-chain repro: PROVEN", "PROVEN")
    return caught


def _check_nonflag(failures: list[str]) -> int:
    """A same-line prohibition on the exact string must stay exempt."""
    out, code = _render("不要把 map = reproduce 写进结论")
    if code == 0 and g.SUCCESS_MARKER in out and "FAIL fabricate" not in out:
        return 1
    failures.append(
        "non-flag: same-line prohibition '不要把 map = reproduce …' was not "
        f"exempt (code={code}, FAIL fabricate={'FAIL fabricate' in out})"
    )
    return 0


def _check_healthy(failures: list[str]) -> int:
    healthy = 0

    # H1: the real repo renders green.
    out_real, code_real = g.render()
    if code_real == 0 and g.SUCCESS_MARKER in out_real:
        healthy += 1
    else:
        failures.append("healthy real repo: expected exit 0 + success marker")

    # H2: a pristine copied temp tree renders green.
    out_copy, code_copy = _render()
    if code_copy == 0 and g.SUCCESS_MARKER in out_copy:
        healthy += 1
    else:
        failures.append("healthy copied tree: expected exit 0 + success marker")

    return healthy


def _check_mutation(failures: list[str]) -> int:
    """Neutralising the map=reproduce regex must silence N1; restore re-catches."""
    original = g._FABRICATE_RES
    neutered = (original[0], original[1], re.compile(r"(?!)"))
    try:
        with tempfile.TemporaryDirectory(prefix="tc_mut_") as d:
            tmp = Path(d)
            _seed_tree(tmp, "map = reproduce")

            g._FABRICATE_RES = neutered
            out_wide, code_wide = g.render(root=tmp)

            g._FABRICATE_RES = original
            out_restored, code_restored = g.render(root=tmp)
    finally:
        g._FABRICATE_RES = original

    widened_silenced = (
        code_wide == 0
        and g.SUCCESS_MARKER in out_wide
        and "FAIL fabricate" not in out_wide
    )
    restored_catches = code_restored == 1 and "FAIL fabricate" in out_restored
    if widened_silenced and restored_catches:
        return 1
    failures.append(
        "mutation: neutralising the map=reproduce regex did not silence N1 "
        f"(silenced={widened_silenced}) or restore did not re-catch it "
        f"(restored_catches={restored_catches})"
    )
    return 0


def main() -> int:
    failures: list[str] = []

    negative = _check_negatives(failures)
    nonflag = _check_nonflag(failures)
    healthy = _check_healthy(failures)
    mutation = _check_mutation(failures)

    print("# Three-chain-reproduce guard negative self-test")
    print(
        f"- negative scenarios caught: {negative}/2; "
        f"prohibition lines exempt: {nonflag}/1; "
        f"healthy trees green: {healthy}/2; "
        f"mutation behaves: {mutation}/1"
    )

    if failures:
        print("\nFAIL:")
        for item in failures:
            print(f"- {item}")
        print(
            "\nThe three-chain-reproduce guard no longer behaves as specified. "
            f"Expected {SUCCESS_MARKER!r}. Exit 1."
        )
        return 1

    print(f"- **{SUCCESS_MARKER}** (2 negative, 1 non-flag, 2 healthy, 1 mutation)")
    print(
        "\nThe guard catches an extra contradictory 'map = reproduce' and a "
        "fabricated 'three-chain repro: PROVEN' even while map ≠ reproduce / "
        "STATUS: blocked and every chain marker stay present; a same-line "
        "'do not write' prohibition stays exempt; a healthy tree stays green; "
        "and neutralising the map=reproduce regex demonstrably silences the "
        "check. Read-only, tempdir-only. Exit 0."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
