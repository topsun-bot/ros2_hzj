#!/usr/bin/env python3
"""Negative self-test for the wiki3 §9.4 risk-matrix Hold guard (eval-only).

Invoked by the Promptfoo local-script provider. It lives under ``evals/`` on
purpose, like ``fingerprint_check.py`` and the other ``*_guard_selftest.py``
scripts: it is **not** one of the 13 CI gates, is not enumerated by
``scripts/run_all_gates.py``, and needs no ``.github/workflows/ci.yml`` wiring
(so it is not blocked by the GitHub ``workflow`` token scope).

Why this exists
---------------
``scripts/check_risk_matrix.py`` is one of the few exit-1 document guards that
had no dedicated negative self-test. The positive gate run only proves the
*current, healthy* docs print ``Risk matrix healthy``; it cannot prove the
Hold-marker detectors still fire when a doc is weakened. The guard carries one
deliberate anti-abbreviation contract (see its source comment): the matrix must
name each of ``《3》`` ``《4》`` ``《5》`` ``《6》`` as its **own** token, so a
lone ``《3》–《6》`` range cannot hide a dropped subtask. Nothing asserted that
this contract actually fails closed.

Scope is deliberately the guard's **unique** checks, not the generic
file-existence shape already covered elsewhere:
  * N1 strips the standalone ``《4》`` token while leaving the ``《3》–《6》``
    range in place -- the range must NOT satisfy the per-token requirement
    (exit 1, ``FAIL markers`` naming ``《4》``);
  * N2 drops a required file (the R0 interface freeze) -- exit 1,
    ``FAIL missing`` naming the path;
  * N3 strips ``§9.4`` from the ADR -- exit 1, ``FAIL markers`` naming it
    (proves markers are enforced per file, not only on the matrix);
  * N4/N5/N6 strip one core Hold-ban word each (``Agnocast`` / ``zenoh`` /
    ``Cega``) from the matrix -- exit 1, ``FAIL markers`` naming the dropped
    word, while the other seven files still print ``ok file`` (no collateral
    failure). The three bans ride the generic matrix marker tuple, and each is
    asserted on its own so dropping just one from the guard's tuple cannot hide
    behind the other two, mirroring the per-token 《3》..《6》 contract;
  * NF1/NF2 are the bidirectional, anti-false-positive half: the two Hold
    -frozen files are checked at a **minimal anchor only** -- SCOREBOARD needs
    just ``STATUS`` (its numbers are never read) and fastdds.xml needs just the
    ``domainId>42`` substring (existence-only seed, content never edited). A
    tree whose frozen files contain only those anchors must stay green;
  * H1/H2 healthy: the real repo and a pristine copied tree both exit 0 with
    the success marker (proves the copied fixture is valid, so negatives do
    not fail for the wrong reason);
  * one mutation: a ``read_utf8`` blind stub that always returns the pristine
    matrix must silence N1, and restoring the real reader must re-catch it.

Fixtures are built by **copying the eight real files the guard reads** (the six
content docs plus the read-only fastdds.xml / SCOREBOARD.md, which here carry a
single required anchor) into a temp tree, then tampering one file per tree.
The guard's injectable ``render(root=...)`` is driven against each tree.

Read-only: files are created only inside a ``tempfile`` directory; the repo
(and especially fastdds.xml / SCOREBOARD.md, which are copied but never
modified) is never written. Standard library only. Exit 0 when every
expectation holds, exit 1 otherwise.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent
ROOT = EVALS_DIR.parent
SCRIPTS = ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS))
import check_risk_matrix as g  # noqa: E402  (sys.path set just above)

SUCCESS_MARKER = "risk matrix guard selftest: PASS"
GATE_HEALTHY = "Risk matrix healthy"

# All eight required files render(root=...) reads, copied verbatim.
ALL_RELS = (
    g.MATRIX_REL,
    g.ADR_REL,
    g.R0_REL,
    g.MAP_REL,
    g.METHOD_REL,
    g.GATES_REL,
    g.SCOREBOARD_REL,
    g.XML_REL,
)


def _real_text(rel: Path) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _seed_tree(
    tmp: Path,
    *,
    matrix_text: str | None = None,
    adr_text: str | None = None,
    scoreboard_text: str | None = None,
    xml_text: str | None = None,
    drop: tuple[Path, ...] = (),
) -> None:
    overrides = {
        g.MATRIX_REL: matrix_text,
        g.ADR_REL: adr_text,
        g.SCOREBOARD_REL: scoreboard_text,
        g.XML_REL: xml_text,
    }
    for rel in ALL_RELS:
        if rel in drop:
            continue
        dst = tmp / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        text = overrides.get(rel)
        if text is None:
            text = _real_text(rel)
        dst.write_text(text, encoding="utf-8")


def _check_negatives(failures: list[str]) -> int:
    caught = 0

    def expect(label: str, must: str, also_ok: tuple[str, ...] = (), **seed) -> None:
        nonlocal caught
        with tempfile.TemporaryDirectory(prefix="risk_neg_") as d:
            tmp = Path(d)
            _seed_tree(tmp, **seed)
            out, code = g.render(root=tmp)
        ok = (
            code == 1
            and GATE_HEALTHY not in out
            and must in out
            and all(s in out for s in also_ok)
        )
        if ok:
            caught += 1
        else:
            failures.append(
                f"negative '{label}': not caught as expected "
                f"(code={code}, need {must!r}, also_ok={also_ok!r})"
            )

    # N1: drop the standalone 《4》 token; the 《3》–《6》 range remains and must
    # not satisfy the per-token Hold contract.
    expect(
        "matrix drops standalone 《4》, keeps range",
        "《4》",
        matrix_text=_real_text(g.MATRIX_REL).replace("《4》", ""),
    )
    # N2: a required file is gone.
    expect("missing R0 freeze file", "FAIL missing", drop=(g.R0_REL,))
    # N3: the ADR loses its §9.4 anchor (per-file marker enforcement).
    expect(
        "ADR loses §9.4",
        "§9.4",
        adr_text=_real_text(g.ADR_REL).replace("§9.4", ""),
    )
    # N4/N5/N6: the three core Hold-ban words (Agnocast / zenoh / Cega) ride
    # the generic matrix marker tuple. Dropping any one from the matrix must
    # fail markers and name it, while the other seven files still report ok
    # (a matrix marker miss must not collaterally fail a sibling file). Each
    # word gets its own case so removing just one from the guard's marker
    # tuple cannot hide behind the other two -- same per-token logic as the
    # 《3》/《4》/《5》/《6》 anti-abbreviation contract.
    sibling_ok = ("ok file:", "feishu-middleware-adr.md")
    expect(
        "matrix drops Hold-ban marker Agnocast",
        "need Agnocast",
        also_ok=sibling_ok,
        matrix_text=_real_text(g.MATRIX_REL).replace("Agnocast", ""),
    )
    expect(
        "matrix drops Hold-ban marker zenoh",
        "need zenoh",
        also_ok=sibling_ok,
        matrix_text=_real_text(g.MATRIX_REL).replace("zenoh", ""),
    )
    expect(
        "matrix drops Hold-ban marker Cega",
        "need Cega",
        also_ok=sibling_ok,
        matrix_text=_real_text(g.MATRIX_REL).replace("Cega", ""),
    )
    return caught


def _check_non_flag(failures: list[str]) -> int:
    ok_count = 0

    def expect(label: str, **seed) -> None:
        nonlocal ok_count
        with tempfile.TemporaryDirectory(prefix="risk_nonflag_") as d:
            tmp = Path(d)
            _seed_tree(tmp, **seed)
            out, code = g.render(root=tmp)
        ok = code == 0 and GATE_HEALTHY in out and "FAIL" not in out
        if ok:
            ok_count += 1
        else:
            failures.append(
                f"non-flag '{label}': falsely flagged (code={code})"
            )

    # NF1: SCOREBOARD is read for the STATUS anchor only, never its numbers.
    expect("minimal SCOREBOARD (STATUS only, no numbers)",
           scoreboard_text="STATUS: blocked\n")
    # NF2: fastdds.xml is an existence-only seed checked at the domainId anchor.
    expect("minimal fastdds.xml (domainId anchor only)",
           xml_text="<profiles>\n  <domainId>42</domainId>\n</profiles>\n")
    return ok_count


def _check_healthy(failures: list[str]) -> int:
    healthy = 0

    out_real, code_real = g.render()
    if code_real == 0 and GATE_HEALTHY in out_real:
        healthy += 1
    else:
        failures.append("healthy real repo: expected exit 0 + healthy marker")

    with tempfile.TemporaryDirectory(prefix="risk_ok_") as d:
        tmp = Path(d)
        _seed_tree(tmp)
        out_copy, code_copy = g.render(root=tmp)
    if code_copy == 0 and GATE_HEALTHY in out_copy:
        healthy += 1
    else:
        failures.append("healthy copied tree: expected exit 0 + healthy marker")

    return healthy


def _check_mutation(failures: list[str]) -> int:
    """A reader that always returns the pristine matrix must silence N1."""
    original_read = g.read_utf8
    tampered_matrix = _real_text(g.MATRIX_REL).replace("《4》", "")
    pristine_matrix = _real_text(g.MATRIX_REL)

    def blind_read(path, *args, **kwargs):  # noqa: ANN001
        if str(path).endswith(g.MATRIX_REL.name):
            return pristine_matrix
        return original_read(path, *args, **kwargs)

    try:
        with tempfile.TemporaryDirectory(prefix="risk_mut_") as d:
            tmp = Path(d)
            _seed_tree(tmp, matrix_text=tampered_matrix)

            g.read_utf8 = blind_read
            out_neutered, code_neutered = g.render(root=tmp)

            g.read_utf8 = original_read
            out_restored, code_restored = g.render(root=tmp)
    finally:
        g.read_utf8 = original_read

    neutered_silenced = (
        code_neutered == 0
        and GATE_HEALTHY in out_neutered
        and "FAIL markers" not in out_neutered
    )
    restored_catches = (
        code_restored == 1 and "FAIL markers" in out_restored and "《4》" in out_restored
    )
    if neutered_silenced and restored_catches:
        return 1
    failures.append(
        "mutation: blind matrix reader did not silence N1 "
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

    print("# Risk-matrix §9.4 Hold guard negative self-test")
    print(
        f"- negative scenarios caught: {negative}/6; "
        f"non-flag scenarios green: {non_flag}/2; "
        f"healthy trees green: {healthy}/2; "
        f"mutation behaves: {mutation}/1"
    )

    if failures:
        print("\nFAIL:")
        for item in failures:
            print(f"- {item}")
        print(
            "\nThe risk-matrix Hold guard no longer behaves as specified. "
            f"Expected {SUCCESS_MARKER!r}. Exit 1."
        )
        return 1

    print(
        f"- **{SUCCESS_MARKER}** "
        "(6 negative, 2 non-flag, 2 healthy, 1 mutation)"
    )
    print(
        "\nThe guard fails closed when a standalone 《3》/《4》/《5》/《6》 Hold "
        "token is replaced by a bare 《3》–《6》 range, when a required file is "
        "missing, when the ADR loses §9.4, or when one of the Agnocast / "
        "zenoh / Cega Hold-ban words is dropped from the matrix; the frozen "
        "SCOREBOARD (STATUS only) and fastdds.xml (domainId anchor only) stay "
        "green at their minimal anchors; a healthy tree stays green; and a "
        "reader that hides the tampered matrix demonstrably silences the "
        "check. Read-only, tempdir-only. Exit 0."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
