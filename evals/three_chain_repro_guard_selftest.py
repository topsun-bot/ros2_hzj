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
  * N3/N4 do not append; the repro doc shell stays present while one Hold ban
    word (``Agnocast`` / ``zenoh``) is removed, which the marker scan must
    catch as ``FAIL markers`` (need the word); the independent phrase/status/
    chains/honesty checks read other content and stay ok.

The ordinary chain markers and ``_has_three_chains`` are intentionally not
re-tested: they are direct ``token in text`` / marker-co-occurrence checks
whose stated design boundary is "filesystem + honesty markers only" (the guard
makes no claim of semantic chain validation). The two Hold **ban** words in
the marker tuple, ``Agnocast`` / ``zenoh`` (one occurrence each), are the
exception and are pinned by N3/N4: the doc stays present but loses one ban
word, which must fail the marker scan and name it (symmetric with the #20 /
#41 Hold-ban negatives) while the phrase/status/chains/honesty checks still
report ok. The same-line prohibition
exemption (``_PROHIBITION_RE`` + ``line_at``) is pinned here on this guard's
own Chinese/English prohibition vocabulary, so a future tightening that
flagged a legitimate "do not write …" instruction would also go red.

Fixtures are built by **copying the six real files the guard reads** (the
reproduce status doc, source-map, WaitSet map, ADR, plus the existence-only
fastdds.xml / SCOREBOARD) into a temp tree, appending one sentence at a time to
the reproduce doc, and driving the injectable ``render(root=...)``. It asserts:
  1. four negative scenarios ARE caught (exit 1, no success marker). N1/N2
     pin ``FAIL fabricate`` naming the fabricated string with no collateral
     FAIL missing/markers/phrase/status/chains (the healthy markers survive);
     N3/N4 pin ``FAIL markers`` naming a stripped Hold ban word
     (Agnocast/zenoh) while phrase/status/chains/honesty still report ok;
  2. three non-flag scenarios stay green: one same-line prohibition sentence
     ("不要把 map = reproduce …") is exempt by the prohibition regex, and the
     two existence-only files — an empty SCOREBOARD and an arbitrary
     fastdds.xml with a bogus domainId — are content-ignored (the content
     freeze is the boundary job, not this guard);
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


def _seed_tree(tmp: Path, repro_append: str = "",
               repro_drop: str = "") -> None:
    """Copy the six real files into the temp tree; append / drop repro text."""
    for rel in CONTENT_RELS:
        dst = tmp / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        text = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
        if rel == g.REPRO_REL:
            if repro_drop:
                text = text.replace(repro_drop, "")
            if repro_append:
                text = text.rstrip("\n") + "\n" + repro_append + "\n"
        dst.write_text(text, encoding="utf-8")


def _render(repro_append: str = "", repro_drop: str = ""):
    with tempfile.TemporaryDirectory(prefix="tc_neg_") as d:
        tmp = Path(d)
        _seed_tree(tmp, repro_append, repro_drop)
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

    # N3/N4: present-but-stripped Hold ban words. The repro doc stays present
    # but loses Agnocast (1) / zenoh (1), which ride the generic marker tuple.
    # N1/N2 only appended extra sentences and never removed a marker, so the
    # doc losing a Hold ban word while present had zero coverage; a future
    # "simplification" that drops a ban word would let the Hold contract
    # vanish while the existing negatives stayed green. The phrase/status/
    # chains/honesty checks read other content and must still report ok, and
    # no fabrication must be implied. Probed on the real guard.
    def expect_drop(label: str, word: str) -> None:
        nonlocal caught
        out, code = _render(repro_drop=word)
        ok = (
            code == 1
            and g.SUCCESS_MARKER not in out
            and "FAIL markers" in out
            and f"(need {word})" in out
            and "ok phrase" in out
            and "ok status" in out
            and "ok chains" in out
            and "ok honesty" in out
            and "FAIL fabricate" not in out
        )
        if ok:
            caught += 1
        else:
            failures.append(
                f"negative '{label}': not caught as expected (code={code}, "
                f"FAIL markers={'FAIL markers' in out}, need={word in out})"
            )

    expect_drop("N3 Hold ban Agnocast dropped", "Agnocast")
    expect_drop("N4 Hold ban zenoh dropped",zenoh_drop := "zenoh")
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


def _check_existence_nonflags(failures: list[str]) -> int:
    """The existence-only XML / SCOREBOARD must be content-ignored here.

    The guard opens both files with an empty marker tuple (the content freeze
    is the boundary job). An empty SCOREBOARD or an arbitrary fastdds.xml (even
    a bogus domainId) must therefore stay exit 0 with the success marker and no
    rendered FAIL line. This pins the allow side of that existence-only
    contract, symmetric with the NF cases of the unitree/dcb guards, so a
    future change that starts validating their contents here would be caught.
    """
    allowed = 0

    def expect_ok(label: str, rewrite) -> None:
        nonlocal allowed
        with tempfile.TemporaryDirectory(prefix="tc_exnf_") as d:
            tmp = Path(d)
            _seed_tree(tmp)
            rewrite(tmp)
            out, code = g.render(root=tmp)
        has_fail = any(line.startswith("- **FAIL") for line in out.splitlines())
        if code == 0 and g.SUCCESS_MARKER in out and not has_fail:
            allowed += 1
        else:
            failures.append(
                f"existence non-flag '{label}': expected exit 0 + success "
                f"marker + no FAIL line (code={code}, has_fail={has_fail})"
            )

    # NF-existence 1: an empty SCOREBOARD stays green.
    expect_ok(
        "empty SCOREBOARD",
        lambda t: (t / g.SCOREBOARD_REL).write_text("", encoding="utf-8"),
    )

    # NF-existence 2: arbitrary fastdds.xml content (bogus domainId) stays green.
    expect_ok(
        "bogus fastdds.xml",
        lambda t: (t / g.XML_REL).write_text(
            "<profiles><domainId>99</domainId></profiles>\n", encoding="utf-8"
        ),
    )

    return allowed


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
    existence = _check_existence_nonflags(failures)
    healthy = _check_healthy(failures)
    mutation = _check_mutation(failures)

    print("# Three-chain-reproduce guard negative self-test")
    print(
        f"- negative scenarios caught: {negative}/4; "
        f"prohibition lines exempt: {nonflag}/1; "
        f"existence-only content green: {existence}/2; "
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

    print(f"- **{SUCCESS_MARKER}** (4 negative, 3 non-flag, 2 healthy, 1 mutation)")
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
