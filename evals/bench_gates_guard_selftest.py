#!/usr/bin/env python3
"""Negative self-test for the bench-gates guard (eval-only).

Invoked by the Promptfoo local-script provider. It lives under ``evals/`` on
purpose, like ``fingerprint_check.py`` and the other ``*_guard_selftest.py``
scripts: it is **not** one of the 13 CI gates, is not enumerated by
``scripts/run_all_gates.py``, and needs no ``.github/workflows/ci.yml`` wiring
(so it is not blocked by the GitHub ``workflow`` token scope).

Why this exists
---------------
``scripts/print_bench_gates.py`` guards wiki3 §12 / §13.3 (bench attribution is
pointer-only and cross-host UDP stays honestly blocked). The positive eval
case only proves the *current, healthy* tree prints the success marker
(``Bench gates healthy``). It cannot prove the guard's two **unique** checks
still fire when they are secretly loosened:

  * the placeholder cross-host directory
    (``docs/artifacts/bench/2026-09-11-cross-host/``) **must exist** while UDP is
    blocked — deleting it must fail even though every required file is intact;
  * ``_cross_host_hits`` scans five candidate files with the unique regex
    ``_STATUS_BLOCKED_RE`` (``STATUS:\\s*\\*?\\s*blocked``) and must find at
    least one honest ``STATUS: blocked``. Rewording every marker to a
    non-blocked status must fail, and a bare ``STATUS`` token must not count.

If someone deleted the directory check or widened the blocked regex, the gate,
the positive case and the #17 stdout fingerprint would all stay green while the
cross-host claim silently became unprovable — the same "guard disabled but all
green" blind spot the other guard self-tests cover. Rounds 12–21 covered the
ten guards with unique parsers; this fills the one missed guard that also
carries a unique regex + a directory-existence branch (``prove_rmw.py`` has no
FAIL path by design and is covered by the Mac HIL notes; ``check_risk_matrix``
is plain marker substring whose §9.4 "order" block re-checks tokens already in
its marker tuple, so neither gets a negative script).

The plain required-file / marker-substring loop is intentionally not re-tested
(same direct ``token in text`` shape already covered by #23 and others).

Fixtures are built by **copying the four real files the guard reads plus the
real cross-host directory** into a temp tree (the files carry the exact
markers; a hand-written minimal tree would rot), then mutating one thing at a
time and driving the injectable ``render(root=...)``. It asserts:
  1. two negative scenarios ARE caught (exit 1, no success marker, the right
     FAIL family, no collateral FAIL):
       N1 the cross-host directory is deleted while all required files stay
          (FAIL missing — the directory branch);
       N2 every candidate's ``STATUS: blocked`` is reworded to a non-blocked
          status while the required ``STATUS`` marker substring is kept
          (FAIL cross-host — the regex scan, not a marker miss);
  2. one non-flag: a tree where ONLY ``BLOCKED.txt`` still says blocked (the
     other four candidates reworded) stays green with exactly one hit, pinning
     the "any candidate hit" semantics rather than "every file must say
     blocked";
  3. two healthy cases: the real repo ``render()`` and a pristine copied tree
     both exit 0 with the success marker;
  4. one mutation: widening ``_STATUS_BLOCKED_RE`` to a bare ``STATUS`` token
     makes N2 slip through undetected (the reworded files still contain
     ``STATUS``), and restoring the regex catches it again.

Read-only: files are created only inside a ``tempfile`` directory; the repo is
never written (the frozen SCOREBOARD is copied, never edited in place).
Standard library only. Exit 0 when every expectation holds, exit 1 (with
details) otherwise.
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
import print_bench_gates as g  # noqa: E402  (sys.path set just above)

SUCCESS_MARKER = "bench gates guard selftest: PASS"
HEALTHY = "Bench gates healthy"

# The four required files (existence + marker substring) and the five
# _cross_host_hits candidates (SCOREBOARD / bench README also carry a blocked
# marker on the healthy host; summary.md deliberately does not).
FILE_RELS = (
    g.SCOREBOARD_REL,
    g.BENCH_README_REL,
    g.SCRIPTS_README_REL,
    g.METHOD_REL,
)
CANDIDATE_RELS = (
    g.SCOREBOARD_REL,
    g.BENCH_README_REL,
    g.CROSS_HOST_REL / "README.md",
    g.CROSS_HOST_REL / "summary.md",
    g.CROSS_HOST_REL / "BLOCKED.txt",
)
_BLOCKED_RE = re.compile(r"STATUS:\s*\*?\s*blocked", re.IGNORECASE)


def _reword_blocked(text: str) -> str:
    """Replace every STATUS:blocked with a non-blocked status (keep STATUS)."""
    out = text
    while _BLOCKED_RE.search(out):
        out = _BLOCKED_RE.sub("STATUS: **ready**", out, count=1)
    return out


def _seed_tree(
    tmp: Path,
    *,
    drop_cross_dir: bool = False,
    reword_all: bool = False,
    only_blocked_txt: bool = False,
) -> None:
    """Copy the real files + cross-host dir into tmp; mutate as asked."""
    for rel in FILE_RELS:
        dst = tmp / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text((ROOT / rel).read_text(encoding="utf-8"), encoding="utf-8")

    if not drop_cross_dir:
        shutil.copytree(ROOT / g.CROSS_HOST_REL, tmp / g.CROSS_HOST_REL)

    if only_blocked_txt:
        reword_targets = [
            rel for rel in CANDIDATE_RELS if rel != g.CROSS_HOST_REL / "BLOCKED.txt"
        ]
    elif reword_all:
        reword_targets = list(CANDIDATE_RELS)
    else:
        reword_targets = []

    for rel in reword_targets:
        path = tmp / rel
        if path.is_file():
            path.write_text(
                _reword_blocked(path.read_text(encoding="utf-8")), encoding="utf-8"
            )


def _render(**kwargs):
    with tempfile.TemporaryDirectory(prefix="bench_neg_") as d:
        tmp = Path(d)
        _seed_tree(tmp, **kwargs)
        return g.render(root=tmp)


def _check_negatives(failures: list[str]) -> int:
    caught = 0

    # N1: cross-host directory deleted; required files intact.
    out, code = _render(drop_cross_dir=True)
    if (
        code == 1
        and HEALTHY not in out
        and "FAIL missing" in out
        and "FAIL cross-host" not in out
        and "FAIL markers" not in out
    ):
        caught += 1
    else:
        failures.append(
            "N1 'cross-host dir deleted': expected exit 1 with only "
            f"'FAIL missing' (code={code}, missing={'FAIL missing' in out}, "
            f"cross={'FAIL cross-host' in out}, markers={'FAIL markers' in out})"
        )

    # N2: every blocked marker reworded but STATUS substring kept.
    out, code = _render(reword_all=True)
    if (
        code == 1
        and HEALTHY not in out
        and "FAIL cross-host" in out
        and "FAIL markers" not in out
    ):
        caught += 1
    else:
        failures.append(
            "N2 'all blocked reworded': expected exit 1 with only "
            f"'FAIL cross-host' (code={code}, cross={'FAIL cross-host' in out}, "
            f"markers={'FAIL markers' in out})"
        )

    return caught


def _check_non_flag(failures: list[str]) -> int:
    """Only BLOCKED.txt says blocked -> still healthy, exactly one hit."""
    with tempfile.TemporaryDirectory(prefix="bench_nonflag_") as d:
        tmp = Path(d)
        _seed_tree(tmp, only_blocked_txt=True)
        hits = g._cross_host_hits(tmp)
        out, code = g.render(root=tmp)
    want_hit = (g.CROSS_HOST_REL / "BLOCKED.txt").as_posix()
    if code == 0 and HEALTHY in out and hits == [want_hit]:
        return 1
    failures.append(
        "non-flag 'only BLOCKED.txt blocked': expected exit 0 with exactly "
        f"[BLOCKED.txt] hit (code={code}, hits={hits})"
    )
    return 0


def _check_healthy(failures: list[str]) -> int:
    healthy = 0

    # H1: the real repo renders green.
    out_real, code_real = g.render()
    if code_real == 0 and HEALTHY in out_real:
        healthy += 1
    else:
        failures.append("healthy real repo: expected exit 0 + success marker")

    # H2: a pristine copied temp tree renders green.
    out_copy, code_copy = _render()
    if code_copy == 0 and HEALTHY in out_copy and "cross-host: blocked" in out_copy:
        healthy += 1
    else:
        failures.append(
            "healthy copied tree: expected exit 0 + success marker + blocked line"
        )

    return healthy


def _check_mutation(failures: list[str]) -> int:
    """Widening _STATUS_BLOCKED_RE to a bare STATUS must silence N2; restore re-catches."""
    original = g._STATUS_BLOCKED_RE
    widened = re.compile(r"STATUS", re.IGNORECASE)
    try:
        with tempfile.TemporaryDirectory(prefix="bench_mut_") as d:
            tmp = Path(d)
            _seed_tree(tmp, reword_all=True)

            g._STATUS_BLOCKED_RE = widened
            out_wide, code_wide = g.render(root=tmp)

            g._STATUS_BLOCKED_RE = original
            out_restored, code_restored = g.render(root=tmp)
    finally:
        g._STATUS_BLOCKED_RE = original

    widened_silenced = code_wide == 0 and "FAIL cross-host" not in out_wide
    restored_catches = code_restored == 1 and "FAIL cross-host" in out_restored
    if widened_silenced and restored_catches:
        return 1
    failures.append(
        "mutation: widening _STATUS_BLOCKED_RE did not silence N2 "
        f"(silenced={widened_silenced}) or restore did not re-catch it "
        f"(restored_catches={restored_catches})"
    )
    return 0


def main() -> int:
    failures: list[str] = []

    negative = _check_negatives(failures)
    non_flag = _check_non_flag(failures)
    healthy = _check_healthy(failures)
    mutation = _check_mutation(failures)

    print("# Bench-gates guard negative self-test")
    print(
        f"- negative scenarios caught: {negative}/2; "
        f"non-flag: {non_flag}/1; healthy trees green: {healthy}/2; "
        f"mutation behaves: {mutation}/1"
    )

    if failures:
        print("\nFAIL:")
        for item in failures:
            print(f"- {item}")
        print(
            "\nThe bench-gates guard no longer behaves as specified. "
            f"Expected {SUCCESS_MARKER!r}. Exit 1."
        )
        return 1

    print(f"- **{SUCCESS_MARKER}** (2 negative, 1 non-flag, 2 healthy, 1 mutation)")
    print(
        "\nThe guard fails when the cross-host placeholder directory is removed "
        "or when no candidate carries an honest STATUS: blocked marker; a single "
        "blocked candidate keeps it green; a healthy tree stays green; and "
        "widening the blocked regex to a bare STATUS token demonstrably silences "
        "the cross-host check. Read-only, tempdir-only. Exit 0."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
