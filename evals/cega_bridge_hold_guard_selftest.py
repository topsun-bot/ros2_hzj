#!/usr/bin/env python3
"""Negative self-test for the Cega / Bridge Hold guard (eval-only).

Invoked by the Promptfoo local-script provider. It lives under ``evals/`` on
purpose, like ``fingerprint_check.py`` and the other ``*_guard_selftest.py``
scripts: it is **not** one of the 13 CI gates, is not enumerated by
``scripts/run_all_gates.py``, and needs no ``.github/workflows/ci.yml`` wiring
(so it is not blocked by the GitHub ``workflow`` token scope).

Why this exists
---------------
``scripts/check_cega_bridge_hold.py`` guards wiki3 §13(4): Cega is not
integrated this cut and the ``dimos_bridge`` runtime is not rewritten. The
positive eval case (#9) only proves the *current, healthy* docs print the
success marker. It cannot prove the guard's unique detectors still fire when
the Hold verdict is secretly flipped. If someone widened those detectors, a
doc that integrated Cega would keep the gate, #9, and the #17 stdout
fingerprint all green while the Hold silently reversed — the same "guard
disabled but all green" blind spot the other guard self-tests cover.

Scope is deliberately the guard's **unique** parsing logic. The generic
``STATUS: PASS`` + same-line prohibition mechanism is a separate copy of the
same idea already covered by the #23 DoD self-test, so it is not re-tested
here. This script pins what only this guard has:
  * ``_ADR_ROW_RE`` / ``_adr_row_ok`` / ``_CELL_POSITIVE_RE`` parse the single
    ADR table row ``| (4) | Cega / Bridge 后置 | … |``: the cell must start
    with ``**Hold**`` AND must not contain PASS/PROVEN/Active/已接 Cega/
    integrate Cega anywhere in the cell, so a ``**Hold** … PASS`` rewrite or a
    dropped row cannot stay green;
  * the guard's built-in ``_row_self_check`` mutates the real ADR in memory
    and must reject both a ``**PASS**`` substitution and a
    ``**Hold** … PASS / 已接 Cega`` cell (defense in depth);
  * the Chinese-only fabrication pattern ``已接 Cega`` (one of
    ``_CEGA_FABRICATE_RES``) is independent of the STATUS / Cega-Bridge:PASS /
    integrate-Cega patterns;
  * ``_first_status_line`` checks only the FIRST ``Status:`` line of the Hold
    doc, which must stay ``Status: **Hold**``.

Fixtures are built by **copying the two real content files the guard parses**
(the Hold doc and the ADR) into a temp tree, plus empty placeholders for the
existence-only fastdds.xml / SCOREBOARD.md and the nine read-only
``dimos_bridge`` runtime paths, then mutating one doc at a time and driving
the injectable ``render(root=...)``. It asserts:
  1. five negative scenarios ARE caught (exit 1, no success marker, the right
     FAIL family):
       N1 ADR §13(4) cell **Hold** -> **PASS**   (FAIL ADR row);
       N2 ADR cell keeps the Hold prefix but appends a bare " ... PASS" with
          no Cega word (FAIL ADR row, and NOT FAIL fabricate — proving the
          cell-level detector, not the full-text fabrication scan, catches it);
       N3 Hold doc first Status: line -> **PASS** (FAIL status);
       N4 Hold doc appends a standalone "已接 Cega" line (FAIL fabricate hold);
       N5 the ADR §13(4) row is deleted (FAIL ADR row);
  2. two non-flag (anti-false-positive) scenarios stay green (exit 0, success
     marker, no fabricate FAIL) — a same-line prohibition exempts an
     "integrate Cega" mention in either the Hold doc (P1) or ADR prose outside
     the §13(4) cell (P2);
  3. one builtin self-check: on the real ADR ``_row_self_check`` reports
     nothing, and both in-memory disguises it constructs are rejected by
     ``_adr_row_ok`` (the guard's own defense-in-depth stays effective);
  4. two healthy cases: the real repo ``render()`` and a pristine copied tree
     both exit 0 with the success marker;
  5. one mutation: replacing the ``已接 Cega`` regex in ``_CEGA_FABRICATE_RES``
     with a never-matching pattern makes N4 slip through undetected, and
     restoring the tuple catches it again.

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
import check_cega_bridge_hold as g  # noqa: E402  (sys.path set just above)

SUCCESS_MARKER = "cega bridge hold guard selftest: PASS"

# The two parsed content files; everything else render(root=...) touches is
# existence-only (XML / SCOREBOARD / nine read-only runtime paths) and gets an
# empty placeholder.
CONTENT_RELS = (g.HOLD_REL, g.ADR_REL)
EXISTENCE_RELS = (g.XML_REL, g.SCOREBOARD_REL) + tuple(g._RUNTIME_RELS)

# A detector disabled the way a careless refactor might: never matches.
NEVER_RE = re.compile(r"(?!)")


def _adr_row_line_span(text: str) -> tuple[int, int]:
    """Return (start, end) offsets of the ADR §13(4) table row line."""
    match = g._ADR_ROW_RE.search(text)
    if match is None:
        raise RuntimeError("fixture anchor: ADR §13(4) row not found")
    end = text.find("\n", match.start())
    if end < 0:
        end = len(text)
    return match.start(), end


def _mut_adr_pass(text: str) -> str:
    """N1: substitute **Hold** -> **PASS** inside the §13(4) cell."""
    mutated = re.sub(
        r"(?m)^(\s*\|\s*\(4\)\s*\|\s*Cega / Bridge 后置\s*\|\s*)\*\*Hold\*\*",
        r"\1**PASS**",
        text,
        count=1,
    )
    if mutated == text:
        raise RuntimeError("fixture anchor: **Hold** cell prefix not found")
    return mutated


def _mut_adr_cell_append_pass(text: str) -> str:
    """N2: keep the **Hold** prefix but append a bare ' ... PASS' to the cell."""
    start, end = _adr_row_line_span(text)
    line = text[start:end].rstrip()
    if not line.endswith("|"):
        raise RuntimeError("fixture anchor: §13(4) row does not end with |")
    new_line = line[:-1].rstrip() + " ... PASS |"
    return text[:start] + new_line + text[end:]


def _mut_adr_delete_row(text: str) -> str:
    """N5: delete the entire §13(4) table row."""
    start, end = _adr_row_line_span(text)
    return text[:start] + text[end:]


def _mut_hold_first_status_pass(text: str) -> str:
    """N3: flip the FIRST Status: line of the Hold doc to **PASS**."""
    mutated = re.sub(r"(?m)^Status:\s*\*\*Hold\*\*", "Status: **PASS**", text, count=1)
    if mutated == text:
        raise RuntimeError("fixture anchor: first Status: **Hold** line not found")
    return mutated


def _seed_tree(tmp: Path, hold_mut=None, adr_mut=None) -> None:
    """Copy the two real content files into the temp tree; mutate as asked."""
    for rel in CONTENT_RELS:
        dst = tmp / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        text = (ROOT / rel).read_text(encoding="utf-8")
        if rel == g.HOLD_REL and hold_mut is not None:
            text = hold_mut(text)
        if rel == g.ADR_REL and adr_mut is not None:
            text = adr_mut(text)
        dst.write_text(text, encoding="utf-8")
    for rel in EXISTENCE_RELS:
        dst = tmp / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text("placeholder\n", encoding="utf-8")


def _render(hold_mut=None, adr_mut=None):
    with tempfile.TemporaryDirectory(prefix="cega_neg_") as d:
        tmp = Path(d)
        _seed_tree(tmp, hold_mut, adr_mut)
        return g.render(root=tmp)


def _check_negatives(failures: list[str]) -> int:
    caught = 0

    def expect(label: str, must: str, must_not: str = "", hold_mut=None, adr_mut=None) -> None:
        nonlocal caught
        out, code = _render(hold_mut=hold_mut, adr_mut=adr_mut)
        ok = code == 1 and g.SUCCESS_MARKER not in out and must in out
        if ok and must_not:
            ok = must_not not in out
        if ok:
            caught += 1
        else:
            failures.append(
                f"negative '{label}': not caught as expected "
                f"(code={code}, need {must!r}"
                + (f", absent {must_not!r}" if must_not else "")
                + ")"
            )

    expect("ADR cell Hold->PASS", "FAIL ADR row", adr_mut=_mut_adr_pass)
    # N2 must be caught by the cell detector alone: no full-text fabricate hit
    # is expected because the appended text has no STATUS:/Cega wording.
    expect(
        "ADR Hold cell with bare PASS appended",
        "FAIL ADR row",
        must_not="FAIL fabricate",
        adr_mut=_mut_adr_cell_append_pass,
    )
    expect("Hold doc first Status -> PASS", "FAIL status", hold_mut=_mut_hold_first_status_pass)
    expect(
        "Hold doc appends 已接 Cega",
        "FAIL fabricate hold",
        hold_mut=lambda t: t + "\n已接 Cega\n",
    )
    expect("ADR §13(4) row deleted", "FAIL ADR row", adr_mut=_mut_adr_delete_row)
    return caught


def _check_non_flag(failures: list[str]) -> int:
    """Bidirectional contract: same-line prohibition exempts 'integrate Cega'."""
    ok_count = 0

    def expect(label: str, hold_mut=None, adr_mut=None) -> None:
        nonlocal ok_count
        out, code = _render(hold_mut=hold_mut, adr_mut=adr_mut)
        ok = (
            code == 0
            and g.SUCCESS_MARKER in out
            and "FAIL fabricate" not in out
            and "FAIL ADR row" not in out
        )
        if ok:
            ok_count += 1
        else:
            failures.append(f"non-flag '{label}': falsely flagged (code={code})")

    expect(
        "Hold doc prohibited integrate-Cega line",
        hold_mut=lambda t: t + "\nwe do not integrate Cega in this cut\n",
    )
    expect(
        "ADR prose prohibited integrate-Cega line outside the cell",
        adr_mut=lambda t: t
        + "\nnote: we do not integrate Cega; no Cega/Bridge PASS here\n",
    )
    return ok_count


def _check_builtin_self_check(failures: list[str]) -> int:
    """The guard's own in-memory row self-check must stay effective."""
    adr_text = (ROOT / g.ADR_REL).read_text(encoding="utf-8")

    # Healthy ADR: no self-check failure.
    healthy_ok = g._row_self_check(adr_text) == []

    # Both disguises the built-in check builds must be rejected by _adr_row_ok.
    pass_row = re.sub(
        r"(?m)^(\s*\|\s*\(4\)\s*\|\s*Cega / Bridge 后置\s*\|\s*)\*\*Hold\*\*",
        r"\1**PASS**",
        adr_text,
        count=1,
    )
    hold_plus = re.sub(
        r"(?m)^(\s*\|\s*\(4\)\s*\|\s*Cega / Bridge 后置\s*\|\s*\*\*Hold\*\*)",
        r"\1 … PASS / 已接 Cega",
        adr_text,
        count=1,
    )
    disguises_rejected = (not g._adr_row_ok(pass_row)) and (
        not g._adr_row_ok(hold_plus)
    )

    if healthy_ok and disguises_rejected:
        return 1
    failures.append(
        "builtin self-check: healthy ADR self-check not clean "
        f"({healthy_ok}) or in-memory disguises not both rejected "
        f"({disguises_rejected})"
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
    with tempfile.TemporaryDirectory(prefix="cega_ok_") as d:
        tmp = Path(d)
        _seed_tree(tmp)
        out_copy, code_copy = g.render(root=tmp)
    if code_copy == 0 and g.SUCCESS_MARKER in out_copy:
        healthy += 1
    else:
        failures.append("healthy copied tree: expected exit 0 + success marker")

    return healthy


def _check_mutation(failures: list[str]) -> int:
    """Neutering the 已接 Cega regex must silence N4; restore re-catches it."""
    original = g._CEGA_FABRICATE_RES
    neutered = (original[0], NEVER_RE, original[2])
    hold_mut = lambda t: t + "\n已接 Cega\n"  # noqa: E731 (fixture closure)
    try:
        with tempfile.TemporaryDirectory(prefix="cega_mut_") as d:
            tmp = Path(d)
            _seed_tree(tmp, hold_mut=hold_mut)

            g._CEGA_FABRICATE_RES = neutered
            out_neutered, code_neutered = g.render(root=tmp)

            g._CEGA_FABRICATE_RES = original
            out_restored, code_restored = g.render(root=tmp)
    finally:
        g._CEGA_FABRICATE_RES = original

    neutered_silenced = (
        code_neutered == 0
        and g.SUCCESS_MARKER in out_neutered
        and "FAIL fabricate hold" not in out_neutered
    )
    restored_catches = code_restored == 1 and "FAIL fabricate hold" in out_restored
    if neutered_silenced and restored_catches:
        return 1
    failures.append(
        "mutation: neutering the 已接 Cega regex did not silence N4 "
        f"(silenced={neutered_silenced}) or restore did not re-catch it "
        f"(restored_catches={restored_catches})"
    )
    return 0


def main() -> int:
    failures: list[str] = []

    negative = _check_negatives(failures)
    non_flag = _check_non_flag(failures)
    builtin = _check_builtin_self_check(failures)
    healthy = _check_healthy(failures)
    mutation = _check_mutation(failures)

    print("# Cega / Bridge Hold guard negative self-test")
    print(
        f"- negative scenarios caught: {negative}/5; "
        f"non-flag scenarios green: {non_flag}/2; "
        f"builtin row self-check effective: {builtin}/1; "
        f"healthy trees green: {healthy}/2; "
        f"mutation behaves: {mutation}/1"
    )

    if failures:
        print("\nFAIL:")
        for item in failures:
            print(f"- {item}")
        print(
            "\nThe Cega / Bridge Hold guard no longer behaves as specified. "
            f"Expected {SUCCESS_MARKER!r}. Exit 1."
        )
        return 1

    print(
        f"- **{SUCCESS_MARKER}** "
        "(5 negative, 2 non-flag, 1 builtin self-check, 2 healthy, 1 mutation)"
    )
    print(
        "\nThe guard catches an ADR §13(4) cell flipped to PASS, a Hold cell "
        "smuggling a PASS token, a first Status: line flipped to PASS, a "
        "standalone 已接 Cega claim, and a deleted ADR row; a same-line "
        "prohibition stays exempt in either doc; the built-in row self-check "
        "rejects both disguises; a healthy tree stays green; and neutering the "
        "已接 Cega regex demonstrably silences the check. Read-only, "
        "tempdir-only. Exit 0."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
