#!/usr/bin/env python3
"""Negative self-test for the product-DoD honesty guard (eval-only).

Invoked by the Promptfoo local-script provider. It lives under ``evals/`` on
purpose, like ``fingerprint_check.py`` and the other ``*_guard_selftest.py``
scripts: it is **not** one of the 13 CI gates, is not enumerated by
``scripts/run_all_gates.py``, and needs no ``.github/workflows/ci.yml`` wiring
(so it is not blocked by the GitHub ``workflow`` token scope).

Why this exists
---------------
``scripts/check_dod_evidence.py`` guards the wiki3 §6.3 product honesty claim:
the evidence doc must stay ``DoD: unmet`` / ``STATUS: blocked``, name the five
unmet product items, and must **not** fabricate a positive ``STATUS: PASS`` /
``DoD: met`` / measured-delta / "Humble ran here" claim, nor invent booked
percentile tokens (p50/p99). The positive eval case (#12) only proves the
*current, healthy* doc prints the success marker. It cannot prove the
anti-fabrication detectors still fire. If someone widened a fabrication regex
(or the same-line prohibition exemption), a doc that secretly flipped to PASS
would keep the gate, #12, and the #17 stdout fingerprint all green while the
honesty verdict silently reversed — the same "guard disabled but all green"
blind spot the frozen/env/unitree/source-map/executor self-tests cover.

Scope is deliberately the guard's **unique** anti-fabrication logic, not the
plain substring/file-existence checks (a missing-marker/missing-file case is
the same shape already represented by #20 N5 / #22 N2·N5):
  * ``_STATUS_FABRICATE_RE`` / ``_DOD_FABRICATE_RE`` / the ``_FABRICATE_RES``
    family catch positive PASS/PROVEN/measured-delta/Humble-here claims;
  * ``_PROHIBITION_RE`` exempts a claim only when the **same line** carries a
    prohibition word ("do not write STATUS: PASS") — it must not treat
    unmet/blocked themselves as prohibition words;
  * ``_PERCENTILE_RE`` catches booked pNN tokens while allowing policy words
    such as the Chinese 分位数.

Fixtures are built by **copying the seven real content files the guard reads**
into a temp tree (plus empty placeholders for the existence-only
fastdds.xml / SCOREBOARD.md) and appending one tampered line at a time to the
DoD doc — the doc carries ~28 contiguous markers, so hand-writing a minimal
healthy doc would be brittle. The guard's injectable ``render(root=...)`` is
then driven against each tree. It asserts:
  1. five negative scenarios ARE caught (exit 1, no success marker, the right
     FAIL family):
       N1 standalone "STATUS: PASS"            (FAIL fabricate);
       N2 "DoD: met"                           (FAIL fabricate);
       N3 this-host measured-delta: PASS       (FAIL fabricate);
       N4 "Humble runtime existed here"        (FAIL fabricate);
       N5 invented booked token "p99 = 12 ms"  (FAIL percentiles);
  2. two non-flag (anti-false-positive) scenarios stay green (exit 0, success
     marker, no fabricate/percentile FAIL) — the bidirectional contract the
     other self-tests mostly lack:
       P1 a prohibited line "do not write STATUS: PASS" must be exempted;
       P2 the policy word 分位数 must not trip the percentile regex;
  3. two healthy cases: the real repo ``render()`` and a pristine copied tree
     both exit 0 with the success marker (proves the copied fixture is valid,
     so the negative cases do not fail for the wrong reason);
  4. one mutation: neutering ``_STATUS_FABRICATE_RE`` to never match makes N1
     slip through undetected, and restoring the regex catches it again.

Read-only: files are created only inside a ``tempfile`` directory; the repo is
never written. Standard library only. Exit 0 when every expectation holds,
exit 1 (with details) otherwise.
"""

from __future__ import annotations

import re
import shutil
import sys
import tempfile
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent
ROOT = EVALS_DIR.parent
SCRIPTS = ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS))
import check_dod_evidence as g  # noqa: E402  (sys.path set just above)

SUCCESS_MARKER = "dod evidence guard selftest: PASS"

# The seven content files render(root=...) actually reads; XML/SCOREBOARD are
# existence-only in this guard and get empty placeholders.
CONTENT_RELS = (
    g.DOD_REL,
    g.ADR_REL,
    g.PROVENANCE_REL,
    g.MAP_REL,
    g.METHOD_REL,
    g.SWAP_REL,
    g.PROVE_RMW_REL,
)
EXISTENCE_RELS = (g.XML_REL, g.SCOREBOARD_REL)

# Tampered lines appended to the real DoD doc, one scenario per tree.
N1_STATUS_PASS = "\nSTATUS: PASS\n"
N2_DOD_MET = "\nDoD: met\n"
N3_MEASURED = "\nthis-host measured-delta: PASS\n"
N4_HUMBLE = "\nHumble runtime existed here\n"
N5_PERCENTILE = "\np99 = 12 ms\n"
P1_PROHIBITED = "\nplease do not write STATUS: PASS in this cut\n"
P2_POLICY_WORD = "\n分位数仅作为政策词，不给出 booked 数值\n"

# A detector disabled the way a careless refactor might: never matches.
NEVER_RE = re.compile(r"(?!)")


def _seed_tree(tmp: Path, dod_append: str = "") -> None:
    """Copy the seven real content files into the temp tree; append to DoD."""
    for rel in CONTENT_RELS:
        src = ROOT / rel
        dst = tmp / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        text = src.read_text(encoding="utf-8")
        if rel == g.DOD_REL:
            text += dod_append
        dst.write_text(text, encoding="utf-8")
    for rel in EXISTENCE_RELS:
        dst = tmp / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text("placeholder\n", encoding="utf-8")


def _check_negatives(failures: list[str]) -> int:
    caught = 0

    def expect(label: str, dod_append: str, must: str) -> None:
        nonlocal caught
        with tempfile.TemporaryDirectory(prefix="dod_neg_") as d:
            tmp = Path(d)
            _seed_tree(tmp, dod_append)
            out, code = g.render(root=tmp)
        ok = (
            code == 1
            and g.SUCCESS_MARKER not in out
            and must in out
        )
        if ok:
            caught += 1
        else:
            failures.append(
                f"negative '{label}': not caught as expected "
                f"(code={code}, need {must!r})"
            )

    expect("STATUS: PASS", N1_STATUS_PASS, "FAIL fabricate")
    expect("DoD: met", N2_DOD_MET, "FAIL fabricate")
    expect("measured-delta PASS", N3_MEASURED, "FAIL fabricate")
    expect("Humble runtime existed here", N4_HUMBLE, "FAIL fabricate")
    expect("invented p99 token", N5_PERCENTILE, "FAIL percentiles")
    return caught


def _check_non_flag(failures: list[str]) -> int:
    """Bidirectional contract: prohibition lines / policy words stay green."""
    ok_count = 0

    def expect(label: str, dod_append: str) -> None:
        nonlocal ok_count
        with tempfile.TemporaryDirectory(prefix="dod_nonflag_") as d:
            tmp = Path(d)
            _seed_tree(tmp, dod_append)
            out, code = g.render(root=tmp)
        ok = (
            code == 0
            and g.SUCCESS_MARKER in out
            and "FAIL fabricate" not in out
            and "FAIL percentiles" not in out
        )
        if ok:
            ok_count += 1
        else:
            failures.append(
                f"non-flag '{label}': falsely flagged (code={code})"
            )

    expect("prohibited STATUS: PASS line", P1_PROHIBITED)
    expect("policy word 分位数", P2_POLICY_WORD)
    return ok_count


def _check_healthy(failures: list[str]) -> int:
    healthy = 0

    # H1: the real repo renders green (regression guard for this self-test).
    out_real, code_real = g.render()
    if code_real == 0 and g.SUCCESS_MARKER in out_real:
        healthy += 1
    else:
        failures.append("healthy real repo: expected exit 0 + success marker")

    # H2: a pristine copied temp tree renders green (proves the seeded fixture
    # is a valid, equivalent healthy tree).
    with tempfile.TemporaryDirectory(prefix="dod_ok_") as d:
        tmp = Path(d)
        _seed_tree(tmp)
        out_copy, code_copy = g.render(root=tmp)
    if code_copy == 0 and g.SUCCESS_MARKER in out_copy:
        healthy += 1
    else:
        failures.append("healthy copied tree: expected exit 0 + success marker")

    return healthy


def _check_mutation(failures: list[str]) -> int:
    """Neutering the STATUS fabrication regex must silence N1, restore re-catch."""
    original = g._STATUS_FABRICATE_RE
    try:
        with tempfile.TemporaryDirectory(prefix="dod_mut_") as d:
            tmp = Path(d)
            _seed_tree(tmp, N1_STATUS_PASS)

            g._STATUS_FABRICATE_RE = NEVER_RE
            out_neutered, code_neutered = g.render(root=tmp)

            g._STATUS_FABRICATE_RE = original
            out_restored, code_restored = g.render(root=tmp)
    finally:
        g._STATUS_FABRICATE_RE = original

    neutered_silenced = (
        code_neutered == 0
        and g.SUCCESS_MARKER in out_neutered
        and "FAIL fabricate" not in out_neutered
    )
    restored_catches = (
        code_restored == 1 and "FAIL fabricate" in out_restored
    )
    if neutered_silenced and restored_catches:
        return 1
    failures.append(
        "mutation: neutering _STATUS_FABRICATE_RE did not silence N1 "
        f"(silenced={neutered_silenced}) or restore did not re-catch it "
        f"(restored_catches={restored_catches})"
    )
    return 0


def main() -> int:
    failures: list[str] = []

    negative = _check_negatives(failures)
    non_flag = _check_non_flag(failures)
    healthy = _check_healthy(failures)
    mutation = _check_mutation(failures)

    print("# Product-DoD honesty guard negative self-test")
    print(
        f"- negative scenarios caught: {negative}/5; "
        f"non-flag scenarios green: {non_flag}/2; "
        f"healthy trees green: {healthy}/2; "
        f"mutation behaves: {mutation}/1"
    )

    if failures:
        print("\nFAIL:")
        for item in failures:
            print(f"- {item}")
        print(
            "\nThe DoD honesty guard no longer behaves as specified. "
            f"Expected {SUCCESS_MARKER!r}. Exit 1."
        )
        return 1

    print(
        f"- **{SUCCESS_MARKER}** "
        "(5 negative, 2 non-flag, 2 healthy, 1 mutation)"
    )
    print(
        "\nThe guard catches a fabricated STATUS: PASS / DoD: met / "
        "measured-delta / Humble-here claim and an invented booked p99 token, "
        "while a same-line prohibition and the policy word 分位数 stay green; "
        "a healthy tree stays green; and neutering the STATUS fabrication "
        "regex demonstrably silences the check. Read-only, tempdir-only. "
        "Exit 0."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
