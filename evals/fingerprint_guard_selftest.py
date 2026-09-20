#!/usr/bin/env python3
"""Negative self-test for ``evals/fingerprint_check.py`` (eval #31, eval-only).

Context
-------
Promptfoo case #17 only asserts the *healthy* path: with every fixture matching,
``fingerprint_check.py`` prints ``stdout fingerprint: stable`` and exits 0. It
never proves that the strict, byte-for-byte layer actually fails when it must.
If that check were hollowed out (e.g. ``normalize`` collapsed every live output
to the baseline, a failing command were tolerated, or a missing/drifted fixture
still reported green), stdout drift in the 13 gates / ``load.py print-a|b``
would silently pass while both ``run_all_gates`` (exit code + one marker) and
the loose Promptfoo ``contains`` assertions stayed green.

This script pins the negative, non-flag, healthy and mutation behavior of the
fingerprint checker itself. Like #18-#30 it is eval-only, pure standard
library, and tempdir-only: it monkey-patches ``fingerprint_check`` module
globals (``ROOT`` / ``FIX_DIR`` / ``COMMANDS`` / ``normalize``) at tiny fake
fixtures and restores them in ``finally``; it never edits the real
``evals/fixtures/`` baseline and is not a CI gate (not in
``run_all_gates.GATES``, not enumerated by CI structure, no ci.yml wiring).

Scenarios (all real FAIL lines were first captured verbatim via a /tmp probe):
  * 4 negative: live stdout != fixture  -> ``FAIL stdout drift`` + DRIFT, rc 1;
    a healthy command with no fixture   -> ``FAIL missing fixture``, rc 1;
    a command exiting non-zero          -> ``FAIL command exit N``, rc 1;
    ``--update`` for a failing command   -> refused on stderr, rc 1, and no
    fixture file is written;
  * 1 non-flag: a command whose stdout embeds the absolute repo root still
    verifies stable, because ``normalize`` rewrites that path to
    ``<REPO_ROOT>`` (portability; the raw temp path must not leak into the
    fixture and must not cause a false DRIFT);
  * 1 healthy: ``--update`` writes the normalized fixture and a clean verify
    prints the stable banner with rc 0;
  * 1 mutation: a ``normalize`` stub that always returns the fixture baseline
    (the "comparison is bypassed / output is flattened" regression) hides a
    drifted command as rc 0; restoring the real ``normalize`` re-catches it as
    rc 1 with DRIFT.
"""

from __future__ import annotations

import contextlib
import io
import pathlib
import sys
import tempfile

EVALS_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(EVALS_DIR))

import fingerprint_check as fp  # noqa: E402  (sys.path set just above)

SUCCESS_MARKER = "fingerprint guard selftest: PASS"

HEALTHY_BODY = 'print("FAKE FINGERPRINT HEALTHY MARKER")\n'
NONZERO_BODY = (
    'import sys\n'
    'sys.stderr.write("boom stderr line\\n")\n'
    'sys.exit(1)\n'
)
# Prints the absolute cwd (== the patched ROOT), which normalize must rewrite
# to <REPO_ROOT> so the fixture is location-independent.
PATH_BODY = 'import pathlib\nprint("cwd=" + str(pathlib.Path.cwd()))\n'

WRONG_BASELINE = "TOTALLY DIFFERENT FINGERPRINT BASELINE\n"


@contextlib.contextmanager
def _bound(root: pathlib.Path):
    """Point fingerprint_check globals at a temp repo; restore on exit."""
    saved = (fp.ROOT, fp.FIX_DIR, fp.COMMANDS)
    fp.ROOT = root
    fp.FIX_DIR = root / "fixtures"
    fp.COMMANDS = []
    try:
        yield
    finally:
        fp.ROOT, fp.FIX_DIR, fp.COMMANDS = saved


def _set_command(root: pathlib.Path, name: str, body: str) -> pathlib.Path:
    """Write a fake command under the temp ROOT and register it as the only one."""
    (root / f"{name}.py").write_text(body, encoding="utf-8")
    fp.COMMANDS = [(name, [sys.executable, f"{name}.py"])]
    return fp.FIX_DIR / f"{name}.txt"


def _run_main(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = fp.main(argv)
    return rc, out.getvalue(), err.getvalue()


def _check_healthy(root: pathlib.Path) -> None:
    fx = _set_command(root, "healthy_gate", HEALTHY_BODY)
    rc_u, out_u, _ = _run_main(["--update"])
    assert rc_u == 0, f"healthy --update must exit 0, got {rc_u}"
    assert "updated:" in out_u and "1 fixtures" in out_u, out_u.strip()
    assert fx.exists(), "--update must write the fixture"
    assert fx.read_text(encoding="utf-8") == "FAKE FINGERPRINT HEALTHY MARKER\n", \
        repr(fx.read_text(encoding="utf-8"))
    rc, out, _ = _run_main([])
    assert rc == 0, f"healthy verify must exit 0, got {rc}\n{out}"
    assert "stdout fingerprint: stable" in out, "missing stable banner"
    assert "(1 commands match" in out, out.strip()


def _check_negative_drift(root: pathlib.Path) -> None:
    fx = _set_command(root, "drift_gate", HEALTHY_BODY)
    rc_u, _, _ = _run_main(["--update"])
    assert rc_u == 0, "setup --update must succeed"
    # Now the live command is unchanged but the reviewed baseline is altered:
    # any byte difference must be reported as drift, not tolerated.
    fx.write_text(WRONG_BASELINE, encoding="utf-8")
    rc, out, _ = _run_main([])
    assert rc == 1, f"drift must exit 1, got {rc} (leak)"
    assert "FAIL stdout drift" in out and "`drift_gate`" in out, out
    assert "stdout fingerprint: DRIFT (" in out, "missing DRIFT verdict"


def _check_negative_missing_fixture(root: pathlib.Path) -> None:
    fx = _set_command(root, "missing_gate", HEALTHY_BODY)
    if fx.exists():
        fx.unlink()
    rc, out, _ = _run_main([])
    assert rc == 1, f"missing fixture must exit 1, got {rc} (leak)"
    assert "FAIL missing fixture" in out and "`missing_gate`" in out, out
    assert "--update" in out, "missing-fixture FAIL must point at --update"


def _check_negative_nonzero_command(root: pathlib.Path) -> None:
    # A fixture exists, but the command itself fails: exit code dominates and
    # must be reported before any byte comparison.
    fx = _set_command(root, "nonzero_gate", NONZERO_BODY)
    fx.parent.mkdir(exist_ok=True)
    fx.write_text("anything\n", encoding="utf-8")
    rc, out, _ = _run_main([])
    assert rc == 1, f"non-zero command must exit 1, got {rc} (leak)"
    assert "FAIL command exit 1" in out and "`nonzero_gate`" in out, out


def _check_negative_update_refuses_nonzero(root: pathlib.Path) -> None:
    fx = _set_command(root, "refuse_gate", NONZERO_BODY)
    if fx.exists():
        fx.unlink()
    rc, _out, err = _run_main(["--update"])
    assert rc == 1, f"--update for a failing command must exit 1, got {rc}"
    assert "refusing to update fixture for refuse_gate: command exited 1" in err, err
    assert not fx.exists(), "--update must not write a fixture for a failed command"


def _check_nonflag_root_path_normalized(root: pathlib.Path) -> None:
    # Absolute clone path in stdout must not leak into / mismatch the fixture.
    fx = _set_command(root, "path_gate", PATH_BODY)
    rc_u, _, _ = _run_main(["--update"])
    assert rc_u == 0, f"path-gate --update must exit 0, got {rc_u}"
    baseline = fx.read_text(encoding="utf-8")
    assert "<REPO_ROOT>" in baseline, f"path not normalized: {baseline!r}"
    assert str(root) not in baseline, f"raw temp root leaked into fixture: {baseline!r}"
    rc, out, _ = _run_main([])
    assert rc == 0, f"normalized path must verify stable, got {rc} (false DRIFT)\n{out}"
    assert "stdout fingerprint: stable" in out, out.strip()


def _check_mutation_blind_normalize_hides_drift(root: pathlib.Path) -> None:
    fx = _set_command(root, "mut_gate", HEALTHY_BODY)
    rc_u, _, _ = _run_main(["--update"])
    assert rc_u == 0, "setup --update must succeed"
    fx.write_text(WRONG_BASELINE, encoding="utf-8")

    real_normalize = fp.normalize
    try:
        # Regression: normalize collapses live output to whatever the fixture
        # says, so the strict comparison can never differ -> drift is hidden.
        fp.normalize = lambda text: fx.read_text(encoding="utf-8")  # noqa: E731
        rc_blind, out_blind, _ = _run_main([])
        assert rc_blind == 0, \
            f"blind normalize expected to leak drift as rc 0, got {rc_blind}"
        assert "stdout fingerprint: stable" in out_blind, "blinded run should falsely report stable"
    finally:
        fp.normalize = real_normalize

    rc, out, _ = _run_main([])
    assert rc == 1, f"real normalize must re-catch drift as rc 1, got {rc}"
    assert "stdout fingerprint: DRIFT (" in out, "drift not re-caught after restore"


def main() -> int:
    checks = [
        ("healthy update+verify", _check_healthy),
        ("negative drift", _check_negative_drift),
        ("negative missing fixture", _check_negative_missing_fixture),
        ("negative non-zero command", _check_negative_nonzero_command),
        ("negative --update refuses non-zero", _check_negative_update_refuses_nonzero),
        ("non-flag root-path normalized", _check_nonflag_root_path_normalized),
        ("mutation blind-normalize hides drift", _check_mutation_blind_normalize_hides_drift),
    ]
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        try:
            with _bound(root):
                for label, fn in checks:
                    fn(root)
                    print(f"  ok {label}")
        except AssertionError as exc:
            print(f"{SUCCESS_MARKER.replace('PASS', 'FAIL')}: {exc}")
            return 1
    print(SUCCESS_MARKER)
    print("4 negative, 1 non-flag, 1 healthy, 1 mutation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
