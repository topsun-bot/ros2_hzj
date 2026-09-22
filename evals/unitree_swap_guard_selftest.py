#!/usr/bin/env python3
"""Negative self-test for the Unitree Cyclone-swap honesty guard (eval-only).

Invoked by the Promptfoo local-script provider. It lives under ``evals/`` on
purpose, like ``fingerprint_check.py`` and ``frozen_guard_selftest.py``: it is
**not** one of the 13 CI gates, is not enumerated by
``scripts/run_all_gates.py``, and needs no ``.github/workflows/ci.yml`` wiring
(so it is not blocked by the GitHub ``workflow`` token scope).

Why this exists
---------------
``scripts/check_unitree_cyclone_swap.py`` guards the safety-relevant honesty
verdict that the Unitree bundled Cyclone 0.10.2 is **not** a drop-in for the
vendored Cyclone 11.0.1 (``drop-in: FAIL / wire: UNPROVEN``), that the default
stays bundled, and that the only legal replace path is
``unitree_sdk2_hzj + UNITREE_DDS_PROVIDER=external``. The positive eval case
(#7) only proves the *current, healthy* tree prints the success marker. It
cannot prove the checks still fire. If someone flipped the doc verdict to
``drop-in PASS / wire PROVEN``, dropped the quoted ``DDS_VERSION "0.10.2"``,
loosened the vendored SHA / CMake ``project() VERSION`` pin, or deleted the
swap doc, and the guard had been widened to accept it, the healthy-tree run
(gate, #7, and the #17 stdout fingerprint) would all stay green while the
safety verdict silently reversed.

Unlike the frozen/env guards, the fixtures here are built by **copying the
five real files the guard reads** into a temp tree and mutating one at a time
(the swap doc carries 18 contiguous markers, so hand-writing a minimal healthy
doc would be brittle and drift from the real record). The guard's injectable
``render(root=...)`` is then driven against each mutated tree. It asserts:
  1. five negative scenarios ARE caught (exit 1, no success marker, the right
     FAIL family), and the independent checks still report ``ok`` (a swap-doc
     mutation must not spuriously fail VERSIONS/CMake and vice versa):
       N1 verdict flipped FAIL/UNPROVEN -> PASS/PROVEN (FAIL verdict);
       N2 quoted DDS_VERSION "0.10.2" tampered, bare 0.10.2 kept (FAIL quote);
       N3 vendored CycloneDDS SHA row tampered (FAIL VERSIONS row);
       N4 CMake project() VERSION 11.0.1 tampered (FAIL CMake project());
       N5 swap doc deleted (FAIL missing);
  2. two non-flag (existence-only) scenarios stay green: an empty SCOREBOARD
     and an arbitrary fastdds.xml (even a bogus domainId) both exit 0 with the
     success marker, since this guard opens those two files but never reads
     their contents (the content freeze is the boundary job);
  3. two healthy cases: the real repo ``render()`` and a pristine copied tree
     both exit 0 with the success marker (proves the copied fixture itself is
     valid and equivalent to the real tree);
  4. one mutation: widening ``_CMAKE_PROJECT_RE`` to drop the VERSION pin makes
     N4 go undetected (the tampered tree prints ``ok CMake project()``), and
     restoring the regex catches it again — proving N4 actually depends on the
     version pin in the detector rather than passing by accident.

Read-only: it creates files only inside a ``tempfile`` directory and never
edits the repo. Standard library only. Exit 0 when every expectation holds,
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
import check_unitree_cyclone_swap as g  # noqa: E402  (sys.path set just above)

SUCCESS_MARKER = "unitree swap guard selftest: PASS"

# The five files render(root=...) opens, in the guard's own relative-path terms.
REQUIRED_RELS = (
    g.SWAP_REL,
    g.VERSIONS_REL,
    g.CMAKE_REL,
    g.XML_REL,
    g.SCOREBOARD_REL,
)

# Real, contiguous strings taken verbatim from the checked files (grep-verified).
FLIPPED_VERDICT = "drop-in PASS / wire PROVEN"
TAMPERED_QUOTE = 'DDS_VERSION "9.9.9"'
GOOD_QUOTE = 'DDS_VERSION "0.10.2"'
REAL_SHA = "e54e991f75a3e67f8e628da3171122e36ea5b872"
TAMPERED_SHA = "0" * len(REAL_SHA)
# A regex widened the way a careless refactor might: matches project(CycloneDDS
# but no longer pins VERSION 11.0.1, so a tampered version slips through.
WIDENED_CMAKE_RE = re.compile(r"(?m)^\s*project\s*\(\s*CycloneDDS\b")


def _seed_tree(tmp: Path) -> None:
    """Copy the five real files into the temp tree, preserving rel paths."""
    for rel in REQUIRED_RELS:
        src = ROOT / rel
        dst = tmp / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)


def _mutate(tmp: Path, rel: Path, old: str, new: str) -> None:
    path = tmp / rel
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"fixture anchor not found in {rel.as_posix()}: {old!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def _remove(tmp: Path, rel: Path) -> None:
    (tmp / rel).unlink()


def _check_negatives(failures: list[str]) -> int:
    caught = 0

    def expect(label: str, mutate, must: tuple[str, ...],
               ok_anyway: tuple[str, ...] = ()) -> None:
        nonlocal caught
        with tempfile.TemporaryDirectory(prefix="unitree_swap_neg_") as d:
            tmp = Path(d)
            _seed_tree(tmp)
            mutate(tmp)
            out, code = g.render(root=tmp)
        ok = code == 1 and g.SUCCESS_MARKER not in out
        ok = ok and all(s in out for s in must)
        ok = ok and all(s in out for s in ok_anyway)
        if ok:
            caught += 1
        else:
            failures.append(
                f"negative '{label}': not caught as expected "
                f"(code={code}, need={must}, ok_anyway={ok_anyway})"
            )

    # N1: flip the contiguous verdict. Must fail the verdict check; VERSIONS and
    # CMake are untouched and must still report ok (checks are independent).
    expect(
        "verdict flipped",
        lambda t: _mutate(t, g.SWAP_REL, g.DOC_VERDICT, FLIPPED_VERDICT),
        ("FAIL verdict",),
        ("ok VERSIONS row:", "ok CMake project():"),
    )

    # N2: tamper the quoted DDS_VERSION while bare "0.10.2" stays elsewhere in
    # the doc. The dedicated quote check must still fire.
    expect(
        "quoted 0.10.2 tampered",
        lambda t: _mutate(t, g.SWAP_REL, GOOD_QUOTE, TAMPERED_QUOTE),
        ("FAIL quote",),
        ("ok VERSIONS row:", "ok CMake project():"),
    )

    # N3: tamper the vendored CycloneDDS SHA. The SHA-row check must fire; the
    # swap doc is untouched so its verdict still reports ok.
    expect(
        "VERSIONS SHA row tampered",
        lambda t: _mutate(t, g.VERSIONS_REL, REAL_SHA, TAMPERED_SHA),
        ("FAIL VERSIONS row",),
        ("ok verdict phrase:",),
    )

    # N4: tamper CMake project() VERSION. The CMake check must fire; the swap
    # doc is untouched so its verdict still reports ok.
    expect(
        "CMake project VERSION tampered",
        lambda t: _mutate(t, g.CMAKE_REL, "VERSION 11.0.1", "VERSION 9.9.9"),
        ("FAIL CMake project()",),
        ("ok verdict phrase:",),
    )

    # N5: delete the swap doc entirely. Must fail on the missing file and never
    # print the success marker; VERSIONS/CMake still open and report ok.
    expect(
        "swap doc deleted",
        lambda t: _remove(t, g.SWAP_REL),
        ("FAIL missing",),
        ("ok VERSIONS row:", "ok CMake project():"),
    )

    return caught


def _check_nonflags(failures: list[str]) -> int:
    """Existence-only files (fastdds.xml / SCOREBOARD) must be content-ignored.

    The guard opens both files but never reads their contents (the content
    freeze is the ``boundary`` job). An empty SCOREBOARD or an arbitrary
    fastdds.xml (even a bogus domainId) must therefore stay exit 0 with the
    success marker and no rendered FAIL line. This pins the allow side of the
    existence-only contract so a future change that starts validating their
    contents here would be caught.
    """
    allowed = 0

    def expect_ok(label: str, rewrite) -> None:
        nonlocal allowed
        with tempfile.TemporaryDirectory(prefix="unitree_swap_nf_") as d:
            tmp = Path(d)
            _seed_tree(tmp)
            rewrite(tmp)
            out, code = g.render(root=tmp)
        has_fail = any(line.startswith("- **FAIL") for line in out.splitlines())
        if code == 0 and g.SUCCESS_MARKER in out and not has_fail:
            allowed += 1
        else:
            failures.append(
                f"non-flag '{label}': expected exit 0 + success marker + no "
                f"FAIL line (code={code}, has_fail={has_fail})"
            )

    # NF1: an empty SCOREBOARD stays green -- its number freeze is owned by
    # boundary, not this guard.
    expect_ok(
        "empty SCOREBOARD",
        lambda t: (t / g.SCOREBOARD_REL).write_text("", encoding="utf-8"),
    )

    # NF2: arbitrary fastdds.xml content (even a bogus domainId) stays green.
    expect_ok(
        "bogus fastdds.xml",
        lambda t: (t / g.XML_REL).write_text(
            "<profiles><domainId>99</domainId></profiles>\n", encoding="utf-8"
        ),
    )

    return allowed


def _check_healthy(failures: list[str]) -> int:
    healthy = 0

    # H1: the real repo renders green (regression guard for this very self-test).
    out_real, code_real = g.render()
    if code_real == 0 and g.SUCCESS_MARKER in out_real:
        healthy += 1
    else:
        failures.append("healthy real repo: expected exit 0 + success marker")

    # H2: a pristine copied temp tree renders green (proves the seeded fixture
    # is a valid, equivalent healthy tree — otherwise the negative cases above
    # could be failing for the wrong reason).
    with tempfile.TemporaryDirectory(prefix="unitree_swap_ok_") as d:
        tmp = Path(d)
        _seed_tree(tmp)
        out_copy, code_copy = g.render(root=tmp)
    if code_copy == 0 and g.SUCCESS_MARKER in out_copy:
        healthy += 1
    else:
        failures.append("healthy copied tree: expected exit 0 + success marker")

    return healthy


def _check_mutation(failures: list[str]) -> int:
    """Widening the CMake regex must make N4 slip, and restoring must catch it."""
    original = g._CMAKE_PROJECT_RE
    try:
        with tempfile.TemporaryDirectory(prefix="unitree_swap_mut_") as d:
            tmp = Path(d)
            _seed_tree(tmp)
            _mutate(tmp, g.CMAKE_REL, "VERSION 11.0.1", "VERSION 9.9.9")

            g._CMAKE_PROJECT_RE = WIDENED_CMAKE_RE
            out_wide, _code_wide = g.render(root=tmp)

            g._CMAKE_PROJECT_RE = original
            out_restored, code_restored = g.render(root=tmp)
    finally:
        g._CMAKE_PROJECT_RE = original

    widened_silenced = (
        "FAIL CMake project()" not in out_wide
        and "ok CMake project():" in out_wide
    )
    restored_catches = (
        code_restored == 1 and "FAIL CMake project()" in out_restored
    )
    if widened_silenced and restored_catches:
        return 1
    failures.append(
        "mutation: widening _CMAKE_PROJECT_RE did not silence N4 "
        f"(silenced={widened_silenced}) or restore did not re-catch it "
        f"(restored_catches={restored_catches})"
    )
    return 0


def main() -> int:
    failures: list[str] = []

    negative = _check_negatives(failures)
    nonflags = _check_nonflags(failures)
    healthy = _check_healthy(failures)
    mutation = _check_mutation(failures)

    print("# Unitree Cyclone-swap honesty guard negative self-test")
    print(
        f"- negative scenarios caught: {negative}/5; "
        f"non-flag existence-only green: {nonflags}/2; "
        f"healthy trees green: {healthy}/2; "
        f"mutation behaves: {mutation}/1"
    )

    if failures:
        print("\nFAIL:")
        for item in failures:
            print(f"- {item}")
        print(
            "\nThe Unitree swap guard no longer behaves as specified. "
            f"Expected {SUCCESS_MARKER!r}. Exit 1."
        )
        return 1

    print(
        f"- **{SUCCESS_MARKER}** (5 negative, 2 non-flag, 2 healthy, 1 mutation)"
    )
    print(
        "\nThe guard catches a flipped drop-in/wire verdict, a tampered quoted"
        " 0.10.2, a changed vendored SHA/CMake pin, and a deleted swap doc; "
        "independent checks still report ok; a healthy tree stays green; and "
        "widening the CMake version regex demonstrably silences the check. "
        "Read-only, tempdir-only. Exit 0."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
