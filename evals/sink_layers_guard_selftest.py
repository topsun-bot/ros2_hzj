#!/usr/bin/env python3
"""Negative self-test for the sink-layers guard (eval-only).

Invoked by the Promptfoo local-script provider. It lives under ``evals/`` on
purpose, like ``fingerprint_check.py`` and the other ``*_guard_selftest.py``
scripts: it is **not** one of the 13 CI gates, is not enumerated by
``scripts/run_all_gates.py``, and needs no ``.github/workflows/ci.yml`` wiring
(so it is not blocked by the GitHub ``workflow`` token scope).

Why this exists
---------------
``scripts/check_sink_layers.py`` asserts the Feishu sink-layer record
(app / rcl / rmw / DDS / executor / memory) keeps one table row per layer and
stays honest about Hold vs allowed. The positive eval case (#10) only proves
the *current, healthy* doc prints the success marker
(``sink layers: mapped (Hold vs allowed)``); the #17 stdout fingerprint only
pins that healthy output byte-for-byte. Neither can prove the guard's one
**unique parser** still fires when it is secretly loosened.

That parser is ``_LAYER_ROW_RE``::

    re.compile(r"(?m)^\\|\\s*\\*\\*(app|rcl|rmw|DDS|executor|memory)\\*\\*\\s*\\|")

The line-anchored, bold-label match is deliberate — the script itself comments
that a bare substring ``rcl`` would also match ``rclpy`` in the **app** row. In
the real doc the app row body literally contains ``rclpy`` and the executor
row body contains ``rclcpp`` / ``rclpy``; the word ``DDS`` appears all over the
prose. So if a future "simplification" rewrote the row check as a bare-word
scan, deleting the ``| **rcl** |`` (or ``| **DDS** |``) table-row label while
leaving the surrounding prose would keep the gate, #10, and the #17
fingerprint all green while the layer table silently lost a row — the same
"guard disabled but all green" blind spot the other self-tests cover.

Scope covers the unique row-anchor parser plus the sink doc's two unique
Hold policy clauses. The other plain marker-substring checks (``eCAL`` /
``DPDK`` / ``Isaac`` / ``Cega`` / ``自定义 RMW`` / three-chain / Unitree
pointers) are direct ``token in text`` checks; the absent-vendor-tree
mechanism (``ABSENT_VENDOR_TREES``) is covered by the #22 executor-map
self-test. The overarching ``Hold vs allowed`` stance phrase is covered
by N5 (it mirrors the risk-matrix overall-stance case).

The two policy clauses are unique to this sink doc and are not asserted by
any other self-test:
  * N3 strips ``AUTO ≠ 已开零拷`` -- the zero-copy status honesty clause
    (automatic shared-memory transport must not be reported as zero-copy
    already enabled);
  * N4 strips ``没有 vendor/iceoryx`` -- the iceoryx Hold clause.
A policy clause lives in both ``_SINK_MARKERS`` and the standalone policy
check, so dropping one must fail BOTH ``FAIL markers`` (naming the clause)
and ``FAIL policy``, while the six layer rows still print ``ok layers`` and
the other six files stay ``ok file`` (no row/other-file collateral).

Fixtures are built by **copying the seven real files the guard reads** (the
sink, ADR, source-map, executor, and Unitree-swap docs plus the
existence-only fastdds.xml / SCOREBOARD) into a temp tree, then blanking one
table-row label at a time (the row body, with all its markers, is kept) and
driving the injectable ``render(root=...)``. It asserts:
  1. five negative scenarios ARE caught (exit 1, no success marker):
       N1 the ``| **rcl** |`` label is blanked — ``FAIL layers`` naming the
          row, no collateral ``FAIL markers`` / ``FAIL policy`` (the row body
          is preserved); a bare-word scan would be rescued by ``rclpy`` /
          ``rclcpp`` in the app/executor rows;
       N2 the ``| **DDS** |`` label is blanked — same, rescued by the word
          ``DDS`` throughout the prose if the scan were loosened;
       N3 the ``AUTO ≠ 已开零拷`` policy clause is stripped — ``FAIL
          markers`` AND ``FAIL policy`` naming it, with ``ok layers`` and the
          other six files still ``ok file``;
       N4 the ``没有 vendor/iceoryx`` policy clause is stripped — same;
       N5 ALL occurrences of the overarching stance phrase ``Hold vs
          allowed`` are stripped (the guard only checks it appears
          somewhere -- it is in 6 places -- so a single-point strip is
          rescued by the other five) — ``FAIL markers`` AND the standalone
          ``FAIL Hold vs allowed``, while ``ok layers`` / ``ok policy`` and
          the other six files stay ``ok file``;
  2. two healthy cases: the real repo ``render()`` and a pristine copied tree
     both exit 0 with the success marker (this also proves the rich app/
     executor prose is NOT mistaken for a missing/extra row — the no-false-
     positive direction);
  3. one mutation: widening ``_LAYER_ROW_RE`` to a bare-word scan makes N1
     slip through undetected, and restoring the line-anchored regex catches
     it again.

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
import check_sink_layers as g  # noqa: E402  (sys.path set just above)

SUCCESS_MARKER = "sink layers guard selftest: PASS"

# All seven required files are copied verbatim (the five content docs carry
# many markers; fastdds.xml / SCOREBOARD are existence-only here). A hand-
# written minimal tree would rot and drift from the real record.
CONTENT_RELS = (
    g.SINK_REL,
    g.ADR_REL,
    g.MAP_REL,
    g.EXEC_REL,
    g.SWAP_REL,
    g.XML_REL,
    g.SCOREBOARD_REL,
)


def _mut_blank_label(layer: str):
    """Blank the bold table-row label for ``layer`` but keep the row body.

    Keeping the body matters: the rcl/DDS rows carry markers (Humble, Rolling,
    eCAL/DPDK/Isaac, 0.10.2/11.0.1, …) that must stay present so the ONLY thing
    that fails is the row-anchor check, not a collateral marker check.
    """
    label = f"| **{layer}** |"

    def _mut(text: str) -> str:
        if label not in text:
            raise RuntimeError(f"fixture anchor: row label {label!r} not found")
        return text.replace(label, "|  |", 1)

    return _mut


def _seed_tree(tmp: Path, sink_mut=None) -> None:
    """Copy the seven real files into the temp tree; mutate the sink doc."""
    for rel in CONTENT_RELS:
        dst = tmp / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        text = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
        if rel == g.SINK_REL and sink_mut is not None:
            text = sink_mut(text)
        dst.write_text(text, encoding="utf-8")


def _render(sink_mut=None):
    with tempfile.TemporaryDirectory(prefix="sink_neg_") as d:
        tmp = Path(d)
        _seed_tree(tmp, sink_mut)
        return g.render(root=tmp)


def _check_negatives(failures: list[str]) -> int:
    caught = 0

    def expect(layer: str) -> None:
        nonlocal caught
        label = f"| **{layer}** |"
        out, code = _render(_mut_blank_label(layer))
        ok = (
            code == 1
            and g.SUCCESS_MARKER not in out
            and "FAIL layers" in out
            and label in out
            # The row body (and its markers) is preserved, so only the
            # row-anchor check may fire — no collateral marker/policy FAIL.
            and "FAIL markers" not in out
            and "FAIL policy" not in out
        )
        if ok:
            caught += 1
        else:
            failures.append(
                f"negative 'blank {layer} row label': not caught cleanly "
                f"(code={code}, need FAIL layers naming {label}, no marker/"
                "policy collateral)"
            )

    expect("rcl")
    expect("DDS")
    return caught


def _check_policy_negatives(failures: list[str]) -> int:
    # The sink doc's two unique Hold policy clauses must fail when stripped.
    caught = 0

    def expect_clause(label: str, clause: str) -> None:
        nonlocal caught
        mut = lambda text: text.replace(clause, "")
        out, code = _render(mut)
        ok = (
            code == 1
            and g.SUCCESS_MARKER not in out
            # A policy clause is in both _SINK_MARKERS and the standalone
            # policy check, so both must fire and name the clause.
            and "FAIL markers" in out
            and f"need {clause}" in out
            and "FAIL policy" in out
            # The six layer rows and the other six files are untouched.
            and "ok layers" in out
            and out.count("ok file:") == 6
            and "FAIL layers" not in out
        )
        if ok:
            caught += 1
        else:
            failures.append(
                f"negative 'strip policy {label}': not caught cleanly "
                f"(code={code}, need FAIL markers + FAIL policy naming "
                f"{clause!r}, ok layers, 6 ok files, no FAIL layers)"
            )

    expect_clause("N3", "AUTO ≠ 已开零拷")
    expect_clause("N4", "没有 vendor/iceoryx")
    return caught


def _check_stance_negatives(failures: list[str]) -> int:
    # The overarching Hold-vs-allowed stance must fail when fully stripped.
    phrase = "Hold vs allowed"

    def mut(text: str) -> str:
        return text.replace(phrase, "")

    out, code = _render(mut)
    ok = (
        code == 1
        and g.SUCCESS_MARKER not in out
        and "FAIL markers" in out
        and f"need {phrase}" in out
        and "FAIL Hold vs allowed" in out
        # Layer rows, the five policy clauses, and the other six files are
        # untouched; the stance check is separate from the policy check.
        and "ok layers" in out
        and "ok policy" in out
        and out.count("ok file:") == 6
        and "FAIL layers" not in out
        and "FAIL policy" not in out
    )
    if ok:
        return 1
    failures.append(
        "negative 'strip overall Hold vs allowed stance': not caught "
        f"cleanly (code={code}, need FAIL markers + FAIL Hold vs allowed, "
        "ok layers/ok policy, 6 ok files, no FAIL layers/policy)"
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
    """A bare-word row scan must silence N1; the anchored regex re-catches it."""
    original = g._LAYER_ROW_RE
    # Drop the line anchor and the bold-label requirement, exactly the
    # "simplification" the guard comment warns about (bare rcl matches rclpy).
    widened = re.compile(r"(?m)(app|rcl|rmw|DDS|executor|memory)")
    mut_rcl = _mut_blank_label("rcl")
    try:
        with tempfile.TemporaryDirectory(prefix="sink_mut_") as d:
            tmp = Path(d)
            _seed_tree(tmp, mut_rcl)

            g._LAYER_ROW_RE = widened
            out_wide, code_wide = g.render(root=tmp)

            g._LAYER_ROW_RE = original
            out_restored, code_restored = g.render(root=tmp)
    finally:
        g._LAYER_ROW_RE = original

    widened_silenced = (
        code_wide == 0
        and g.SUCCESS_MARKER in out_wide
        and "FAIL layers" not in out_wide
    )
    restored_catches = code_restored == 1 and "FAIL layers" in out_restored
    if widened_silenced and restored_catches:
        return 1
    failures.append(
        "mutation: widening _LAYER_ROW_RE to bare words did not silence the "
        f"missing-rcl-row case (silenced={widened_silenced}) or restore did "
        f"not re-catch it (restored_catches={restored_catches})"
    )
    return 0


def main() -> int:
    failures: list[str] = []

    row_negative = _check_negatives(failures)
    policy_negative = _check_policy_negatives(failures)
    stance_negative = _check_stance_negatives(failures)
    negative = row_negative + policy_negative + stance_negative
    healthy = _check_healthy(failures)
    mutation = _check_mutation(failures)

    print("# Sink-layers guard negative self-test")
    print(
        f"- negative scenarios caught: {negative}/5; "
        f"healthy trees green: {healthy}/2; "
        f"mutation behaves: {mutation}/1"
    )

    if failures:
        print("\nFAIL:")
        for item in failures:
            print(f"- {item}")
        print(
            "\nThe sink-layers guard no longer behaves as specified. "
            f"Expected {SUCCESS_MARKER!r}. Exit 1."
        )
        return 1

    print(f"- **{SUCCESS_MARKER}** (5 negative, 2 healthy, 1 mutation)")
    print(
        "\nThe guard catches a blanked rcl/DDS table-row label even though the "
        "app row still mentions rclpy and the prose is full of DDS, and it "
        "catches a stripped AUTO != zero-copy / no-vendor-iceoryx policy "
        "clause via both markers and policy checks while the six rows stay "
        "ok, and it catches the fully stripped Hold-vs-allowed stance via "
        "markers and the standalone stance check; a healthy six-row tree "
        "stays green; and widening the row regex to a bare-word "
        "scan demonstrably silences the missing-row check. Read-only, "
        "tempdir-only. Exit 0."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
