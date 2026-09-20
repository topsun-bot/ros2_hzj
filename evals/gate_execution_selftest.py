#!/usr/bin/env python3
"""Negative self-test for the gate-runner *execution* semantics (eval-only).

Invoked by the Promptfoo local-script provider. It lives under ``evals/`` on
purpose, like ``fingerprint_check.py``, the ``*_guard_selftest.py`` scripts and
``gate_registry_selftest.py``: it is **not** one of the 13 CI gates, is not
enumerated by ``scripts/run_all_gates.py`` itself, and needs no
``.github/workflows/ci.yml`` wiring (so it is not blocked by the missing GitHub
``workflow`` token scope).

Why this exists
---------------
``gate_registry_selftest.py`` (eval #29) pins the runner's **registry** face --
that the on-disk gate set and ``run_all_gates.GATES`` agree (no orphan, no
missing). It never *executes* a gate, so it cannot protect the runner's
**execution** face, which lives in ``run_one`` / ``main``:

  * ``run_one`` returns ``(rc, marker_present, output)``. A gate that exits 0
    but forgets to print its canonical healthy marker must still be caught --
    the runner checks **both** exit code 0 AND the marker substring, so a guard
    that was hollowed out to ``sys.exit(0)`` cannot keep the headline green.
  * A gate that exits non-zero (even if it prints the marker) must fail.
  * A registered script that is absent on disk must be reported as ``127`` /
    ``missing:`` and fail the run instead of being silently skipped.
  * The marker is searched over stdout **and** stderr combined, so a healthy
    marker emitted on stderr is still honoured (and cannot be spoofed by a
    non-zero exit).

If a future change made ``main`` trust the exit code alone (dropping the
``zero-but-missing-marker`` tally), made ``run_one`` always report the marker
present, or treated a missing file as a pass, the whole 13-gate loop could go
green while a guard was silently disabled. This script pins those behaviours on
tempdir fixtures and includes a mutation proving the missing-marker check is
not vacuous.

Scope note: this pins the runner's execution/verdict logic only. It does not
assert the CI ``structure`` 12-vs-13 enumeration (that waits on the
``workflow`` token scope, see eval #29) and does not run any real project gate.

Read-only: fixtures are created only inside a ``tempfile`` directory and
``run_all_gates.REPO_ROOT`` / ``GATES`` / ``run_one`` are monkey-patched and
restored in ``finally`` blocks; the repo is never edited and no production code
is changed. Standard library only. Exit 0 when every expectation holds,
exit 1 (with details) otherwise.
"""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent
ROOT = EVALS_DIR.parent
SCRIPTS = ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS))
import run_all_gates as runner  # noqa: E402  (sys.path set just above)

SUCCESS_MARKER = "gate runner execution selftest: PASS"

# Canonical healthy marker the temp gates are expected to print.
MARK = "EXEC_FIXTURE_HEALTHY"


@contextlib.contextmanager
def _patched_root(root: Path):
    """Point the runner at a temp repo root with a throwaway GATES list."""
    saved_root = runner.REPO_ROOT
    saved_gates = runner.GATES
    runner.REPO_ROOT = root
    runner.GATES = []
    try:
        yield
    finally:
        runner.REPO_ROOT = saved_root
        runner.GATES = saved_gates


def _write_gate(root: Path, name: str, body: str) -> str:
    scripts = root / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    (scripts / name).write_text(body, encoding="utf-8")
    return f"scripts/{name}"


def _run_main() -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = runner.main()
    return rc, buf.getvalue()


def _check_healthy_exit_and_marker(failures: list[str]) -> int:
    """A gate that exits 0 and prints its marker -> run_one ok, main green."""
    with tempfile.TemporaryDirectory(prefix="gate_exec_ok_") as tmp:
        root = Path(tmp)
        with _patched_root(root):
            rel = _write_gate(root, "ok_gate.py", f'print("{MARK}")\n')
            runner.GATES = [(rel, MARK)]
            rc, has_marker, _ = runner.run_one(rel, MARK)
            main_rc, out = _run_main()
    problems = []
    if (rc, has_marker) != (0, True):
        problems.append(f"healthy run_one got rc={rc} marker={has_marker}, want (0, True)")
    if main_rc != 0 or "all gates green" not in out:
        problems.append(f"healthy main got rc={main_rc}, want 0 + green banner")
    if "zero-but-missing-marker: 0" not in out:
        problems.append("healthy run should tally zero-but-missing-marker: 0")
    if problems:
        failures.extend(problems)
        return 0
    return 1


def _check_negative_zero_without_marker(failures: list[str]) -> int:
    """A gate that exits 0 but never prints the marker must FAIL the run."""
    with tempfile.TemporaryDirectory(prefix="gate_exec_nomark_") as tmp:
        root = Path(tmp)
        with _patched_root(root):
            rel = _write_gate(root, "no_marker.py", 'print("something unrelated")\n')
            runner.GATES = [(rel, MARK)]
            rc, has_marker, _ = runner.run_one(rel, MARK)
            main_rc, out = _run_main()
    problems = []
    if (rc, has_marker) != (0, False):
        problems.append(f"no-marker run_one got rc={rc} marker={has_marker}, want (0, False)")
    if main_rc != 1 or "run_all_gates: FAIL" not in out:
        problems.append(f"no-marker main got rc={main_rc}, want 1 + FAIL")
    if "zero-but-missing-marker: 1" not in out:
        problems.append("no-marker run must tally zero-but-missing-marker: 1")
    if problems:
        failures.extend(problems)
        return 0
    return 1


def _check_negative_nonzero_exit(failures: list[str]) -> int:
    """A gate that exits non-zero (marker or not) must FAIL the run."""
    with tempfile.TemporaryDirectory(prefix="gate_exec_nonzero_") as tmp:
        root = Path(tmp)
        with _patched_root(root):
            rel = _write_gate(
                root,
                "bad_gate.py",
                f'import sys; print("{MARK}"); sys.exit(1)\n',
            )
            runner.GATES = [(rel, MARK)]
            rc, has_marker, _ = runner.run_one(rel, MARK)
            main_rc, out = _run_main()
    problems = []
    if rc == 0:
        problems.append(f"non-zero run_one got rc={rc}, want non-zero")
    if not has_marker:
        # Marker present but exit 1: the exit code must still dominate.
        problems.append("non-zero fixture should still expose its marker in output")
    if main_rc != 1 or "run_all_gates: FAIL" not in out:
        problems.append(f"non-zero main got rc={main_rc}, want 1 + FAIL")
    if "non-zero: 1" not in out:
        problems.append("non-zero run must tally non-zero: 1")
    if problems:
        failures.extend(problems)
        return 0
    return 1


def _check_negative_missing_file(failures: list[str]) -> int:
    """A GATES row pointing at an absent script -> run_one 127, main FAIL."""
    rel = "scripts/absent_gate.py"
    with tempfile.TemporaryDirectory(prefix="gate_exec_missing_") as tmp:
        root = Path(tmp)
        with _patched_root(root):
            runner.GATES = [(rel, MARK)]
            rc, has_marker, output = runner.run_one(rel, MARK)
            main_rc, out = _run_main()
    problems = []
    if rc != 127 or has_marker:
        problems.append(f"missing run_one got rc={rc} marker={has_marker}, want (127, False)")
    if f"missing: {rel}" not in output:
        problems.append(f"missing run_one output should name the path; got {output!r}")
    if main_rc != 1 or "run_all_gates: FAIL" not in out:
        problems.append(f"missing main got rc={main_rc}, want 1 + FAIL")
    if problems:
        failures.extend(problems)
        return 0
    return 1


def _check_nonflag_marker_on_stderr(failures: list[str]) -> int:
    """Marker emitted only on stderr, exit 0 -> combined output still passes.

    Pins that run_one searches stdout+stderr combined (no false FAIL), while
    the exit-0 requirement is unchanged.
    """
    with tempfile.TemporaryDirectory(prefix="gate_exec_stderr_") as tmp:
        root = Path(tmp)
        with _patched_root(root):
            rel = _write_gate(
                root,
                "stderr_gate.py",
                f'import sys; print("{MARK}", file=sys.stderr)\n',
            )
            runner.GATES = [(rel, MARK)]
            rc, has_marker, _ = runner.run_one(rel, MARK)
            main_rc, out = _run_main()
    problems = []
    if (rc, has_marker) != (0, True):
        problems.append(f"stderr-marker run_one got rc={rc} marker={has_marker}, want (0, True)")
    if main_rc != 0 or "all gates green" not in out:
        problems.append(f"stderr-marker main got rc={main_rc}, want 0 + green")
    if problems:
        failures.extend(problems)
        return 0
    return 1


def _check_mutation(failures: list[str]) -> int:
    """A run_one that always claims the marker present hides the no-marker gate.

    Equivalent to a future regression where the runner trusts the exit code
    alone and stops checking the marker substring. With the real run_one the
    same gate is caught again afterwards.
    """
    real_run_one = runner.run_one
    with tempfile.TemporaryDirectory(prefix="gate_exec_mut_") as tmp:
        root = Path(tmp)
        with _patched_root(root):
            rel = _write_gate(root, "no_marker.py", 'print("something unrelated")\n')
            runner.GATES = [(rel, MARK)]

            def blind(rel_path: str, marker: str):
                rc, _has, combined = real_run_one(rel_path, marker)
                return rc, True, combined  # always claim the marker is present

            runner.run_one = blind
            try:
                blinded_rc, _ = _run_main()
            finally:
                runner.run_one = real_run_one
            real_rc, _ = _run_main()
    problems = []
    if blinded_rc != 0:
        problems.append(
            "mutation did not blind the missing-marker verdict; the assertion "
            "would pass even if the marker check were dead"
        )
    if real_rc != 1:
        problems.append("after restoring run_one, the no-marker gate was not caught")
    if problems:
        failures.extend(problems)
        return 0
    return 1


def main() -> int:
    failures: list[str] = []

    healthy = _check_healthy_exit_and_marker(failures)
    n_no_marker = _check_negative_zero_without_marker(failures)
    n_nonzero = _check_negative_nonzero_exit(failures)
    n_missing = _check_negative_missing_file(failures)
    negative = n_no_marker + n_nonzero + n_missing
    nonflag = _check_nonflag_marker_on_stderr(failures)
    mutation = _check_mutation(failures)

    print("# gate-runner execution semantics self-test")
    print(
        f"- negative scenarios caught: {negative}/3; non-flag stderr-marker: "
        f"{nonflag}/1; healthy case green: {healthy}/1; mutation cases: {mutation}/1"
    )

    if failures:
        print("\nFAIL:")
        for item in failures:
            print(f"- {item}")
        print(
            "\nThe gate-runner execution verdict no longer matches its contract "
            f"(exit 0 AND marker present; non-zero / missing -> FAIL). Expected "
            f"{SUCCESS_MARKER!r}. Exit 1."
        )
        return 1

    print(
        f"- **{SUCCESS_MARKER}** (3 negative, 1 non-flag, 1 healthy, 1 mutation)"
    )
    print(
        "\nrun_one/main are proven to: pass a gate only when it exits 0 AND "
        "prints its marker over stdout/stderr combined; FAIL on exit-0-without-"
        "marker (zero-but-missing-marker), on non-zero exit, and on a missing "
        "script (127); and a run_one that blindly claims the marker present is "
        "proven to hide a hollowed-out exit-0 gate. Read-only, tempdir-only. "
        "Exit 0."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
