#!/usr/bin/env python3
"""Negative/consistency self-test for the gate-runner registry (eval-only).

Invoked by the Promptfoo local-script provider. It lives under ``evals/`` on
purpose, like ``fingerprint_check.py`` and the ``*_guard_selftest.py`` scripts:
it is **not** one of the 13 CI gates, is not enumerated by
``scripts/run_all_gates.py`` itself, and needs no ``.github/workflows/ci.yml``
wiring (so it is not blocked by the missing GitHub ``workflow`` token scope).

Why this exists
---------------
``scripts/run_all_gates.py`` hard-codes ``GATES`` (13 ``(script, marker)``
rows). Running it green proves only that every *registered* script exists,
exits 0, and prints its marker. It cannot detect the symmetric drift that
matters for the 《3》 eval loop:

  * **orphan gate** -- a new ``scripts/check_*.py`` (or one of the two
    non-``check_`` gates ``prove_rmw.py`` / ``print_bench_gates.py``) is added
    on disk but never registered in ``GATES``. The headline score would stay
    "13/13" forever; the new gate simply never runs in the loop. This is the
    same class of miss that left the CI ``structure`` job enumerating only the
    first 12 gates when the 13th (``check_frozen_path_literals.py``) landed.
  * **missing gate** -- a ``GATES`` row points at a script that is gone or
    renamed. ``run_all_gates`` reports that at run time as ``127`` / FAIL, but
    no dedicated regression pins the exact orphan/missing distinction or the
    discovery rule that separates gates from underscore helpers
    (``_repo.py`` / ``_md_paths.py`` / ``_freeze_paths.py``) and the runner
    itself (``run_all_gates.py``).

This script owns a single, explicit discovery rule -- a gate is any top-level
``scripts/*.py`` whose name starts with ``check_``, plus the two fixed names
``prove_rmw.py`` and ``print_bench_gates.py``; underscore-prefixed helpers and
``run_all_gates.py`` are never gates -- and asserts the discovered set is
exactly the registered ``GATES`` set, in both directions, on the real repo and
on tempdir fixtures. A stubbed discoverer that blindly trusts the registry
must hide the orphan scenario (mutation), proving the orphan check is not
vacuous.

Scope note: this pins the **runner** registry vs. the scripts directory. The
separate, known gap that the CI ``structure`` job enumerates only 12 gates is
intentionally NOT asserted here -- wiring the 13th gate into
``.github/workflows/ci.yml`` needs the ``workflow`` token scope (a standalone,
user-approved change), and this script has no business reading CI yaml.

Read-only: fixtures are created only inside a ``tempfile`` directory; the repo
is never edited and no production code is imported for side effects beyond
reading ``run_all_gates.GATES``. Standard library only. Exit 0 when every
expectation holds, exit 1 (with details) otherwise.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent
ROOT = EVALS_DIR.parent
SCRIPTS = ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS))
import run_all_gates as runner  # noqa: E402  (sys.path set just above)

SUCCESS_MARKER = "gate registry selftest: PASS"

# Gate-shape scripts that do NOT use the check_ prefix.
EXTRA_GATES = ("prove_rmw.py", "print_bench_gates.py")
# Never gates: the runner itself and underscore-prefixed shared helpers.
RUNNER_NAME = "run_all_gates.py"

# Explicit contract: the modernization loop currently has exactly 13 runner
# gates. Adding/removing a gate must deliberately update this number together
# with run_all_gates.GATES, which is the synchronization this test enforces.
EXPECTED_GATE_COUNT = 13

# Registered gate base names, taken from the single source of truth.
REGISTERED = frozenset(Path(rel).name for rel, _marker in runner.GATES)


def discover_gate_scripts(scripts_dir: Path) -> set[str]:
    """Return the base names of gate-shape scripts in ``scripts_dir``."""
    found: set[str] = set()
    for path in scripts_dir.glob("*.py"):
        name = path.name
        if name.startswith("_") or name == RUNNER_NAME:
            continue
        if name.startswith("check_") or name in EXTRA_GATES:
            found.add(name)
    return found


def registry_problems(disk: set[str], registered: set[str]) -> tuple[list[str], list[str]]:
    """Return (missing, orphan): registered-but-absent and on-disk-but-unregistered."""
    missing = sorted(registered - disk)
    orphan = sorted(disk - registered)
    return missing, orphan


def _write_scripts(scripts_dir: Path, names: set[str]) -> None:
    scripts_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        (scripts_dir / name).write_text("# temp fixture\n", encoding="utf-8")


def _check_negative_orphan(failures: list[str]) -> int:
    """An on-disk check_*.py absent from GATES must be reported as orphan."""
    with tempfile.TemporaryDirectory(prefix="gate_reg_orphan_") as tmp:
        d = Path(tmp) / "scripts"
        names = set(REGISTERED) | {"check_orphan_gate.py"}
        _write_scripts(d, names)
        disk = discover_gate_scripts(d)
        missing, orphan = registry_problems(disk, REGISTERED)
    if "check_orphan_gate.py" not in orphan:
        failures.append(f"orphan gate not detected; orphan={orphan}")
        return 0
    if missing:
        failures.append(f"orphan scenario unexpectedly reported missing={missing}")
        return 0
    if "check_orphan_gate.py" not in disk:
        failures.append("discoverer did not even see the orphan check_ script")
        return 0
    return 1


def _check_negative_missing(failures: list[str]) -> int:
    """A GATES row whose script is absent must be reported as missing."""
    dropped = "check_frozen_path_literals.py"
    with tempfile.TemporaryDirectory(prefix="gate_reg_missing_") as tmp:
        d = Path(tmp) / "scripts"
        names = set(REGISTERED) - {dropped}
        _write_scripts(d, names)
        disk = discover_gate_scripts(d)
        missing, orphan = registry_problems(disk, REGISTERED)
    if dropped not in missing:
        failures.append(f"missing gate not detected; missing={missing}")
        return 0
    if orphan:
        failures.append(f"missing scenario unexpectedly reported orphan={orphan}")
        return 0
    return 1


def _check_nonflag_helpers(failures: list[str]) -> int:
    """Helpers and the runner must never be mistaken for gates (no false orphan)."""
    helpers = {"_repo.py", "_md_paths.py", "_freeze_paths.py", RUNNER_NAME}
    with tempfile.TemporaryDirectory(prefix="gate_reg_helpers_") as tmp:
        d = Path(tmp) / "scripts"
        _write_scripts(d, set(REGISTERED) | helpers)
        disk = discover_gate_scripts(d)
        missing, orphan = registry_problems(disk, REGISTERED)
    wrongly_seen = sorted(helpers & disk)
    if wrongly_seen:
        failures.append(f"helpers/runner misclassified as gates: {wrongly_seen}")
        return 0
    if missing or orphan:
        failures.append(f"helper tree should be clean; missing={missing} orphan={orphan}")
        return 0
    return 1


def _check_healthy_real(failures: list[str]) -> int:
    """The real repo: discovered set == registered set, count == 13, markers set."""
    disk = discover_gate_scripts(SCRIPTS)
    missing, orphan = registry_problems(disk, REGISTERED)
    problems: list[str] = []
    if len(runner.GATES) != EXPECTED_GATE_COUNT:
        problems.append(
            f"GATES has {len(runner.GATES)} rows, expected {EXPECTED_GATE_COUNT}"
        )
    if missing:
        problems.append(f"real tree missing registered gates: {missing}")
    if orphan:
        problems.append(f"real tree has orphan gate scripts: {orphan}")
    empty_markers = [rel for rel, m in runner.GATES if not str(m).strip()]
    if empty_markers:
        problems.append(f"GATES rows with empty marker: {empty_markers}")
    for fixed in EXTRA_GATES:
        if fixed not in REGISTERED:
            problems.append(f"fixed non-check gate {fixed} not registered")
    if problems:
        failures.extend(problems)
        return 0
    return 1


def _check_healthy_temp(failures: list[str]) -> int:
    """A tempdir containing exactly the 13 registered gates is clean."""
    with tempfile.TemporaryDirectory(prefix="gate_reg_ok_") as tmp:
        d = Path(tmp) / "scripts"
        _write_scripts(d, set(REGISTERED))
        disk = discover_gate_scripts(d)
        missing, orphan = registry_problems(disk, REGISTERED)
    if disk != REGISTERED or missing or orphan:
        failures.append(
            f"clean temp tree not consistent: disk==registered:{disk == REGISTERED} "
            f"missing={missing} orphan={orphan}"
        )
        return 0
    return 1


def _check_mutation(failures: list[str]) -> int:
    """A discoverer that blindly trusts the registry must hide an orphan.

    Equivalent to a future regression where the runner/loop only reads GATES
    and never scans scripts/. With the real discoverer the orphan is caught
    again afterwards.
    """
    global discover_gate_scripts
    real_discover = discover_gate_scripts
    with tempfile.TemporaryDirectory(prefix="gate_reg_mut_") as tmp:
        d = Path(tmp) / "scripts"
        _write_scripts(d, set(REGISTERED) | {"check_orphan_gate.py"})
        # Mutated discoverer: report exactly what is registered, ignore disk.
        discover_gate_scripts = lambda scripts_dir: set(REGISTERED)  # noqa: E731
        try:
            blinded_disk = discover_gate_scripts(d)
            blinded_missing, blinded_orphan = registry_problems(blinded_disk, REGISTERED)
        finally:
            discover_gate_scripts = real_discover
        if blinded_orphan:
            failures.append(
                "mutation did not blind the orphan detector; the assertion "
                "would pass even with a dead discovery scan"
            )
            return 0
        # Restore sanity: the real discoverer catches the same orphan.
        real_disk = real_discover(d)
        _, real_orphan = registry_problems(real_disk, REGISTERED)
    if "check_orphan_gate.py" not in real_orphan:
        failures.append("after restoring the discoverer, the orphan was not caught")
        return 0
    return 1


def main() -> int:
    failures: list[str] = []

    n_orphan = _check_negative_orphan(failures)
    n_missing = _check_negative_missing(failures)
    negative = n_orphan + n_missing
    nonflag = _check_nonflag_helpers(failures)
    h_real = _check_healthy_real(failures)
    h_temp = _check_healthy_temp(failures)
    healthy = h_real + h_temp
    mutation = _check_mutation(failures)

    print("# gate-runner registry consistency self-test")
    print(
        f"- negative scenarios caught: {negative}/2; non-flag helper exclusion: "
        f"{nonflag}/1; healthy cases clean: {healthy}/2; mutation cases: {mutation}/1"
    )

    if failures:
        print("\nFAIL:")
        for item in failures:
            print(f"- {item}")
        print(
            "\nThe gate-runner registry no longer matches the scripts directory "
            f"as specified. Expected {SUCCESS_MARKER!r}. Exit 1."
        )
        return 1

    print(
        f"- **{SUCCESS_MARKER}** (2 negative, 1 non-flag, 2 healthy, 1 mutation)"
    )
    print(
        "\nEvery gate-shape script under scripts/ is registered in "
        "run_all_gates.GATES and vice versa (no orphan, no missing); underscore "
        "helpers and the runner itself are never counted as gates; the gate "
        "count is pinned at 13 with non-empty markers; and a discoverer that "
        "blindly trusts the registry is proven to hide an orphan. Read-only, "
        "tempdir-only. Exit 0."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
