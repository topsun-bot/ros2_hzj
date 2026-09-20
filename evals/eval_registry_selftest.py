#!/usr/bin/env python3
"""Registry self-test for the Promptfoo eval suite itself (#35).

Context
-------
#29 (`gate_registry_selftest.py`) pins the *gate runner* registry: the gate
scripts on disk must match `run_all_gates.GATES` in both directions, so an
orphan gate or a GATES row pointing at a deleted script cannot hide behind a
green headline. Its own scope note says it pins the runner registry vs.
``scripts/`` -- it does NOT cover the eval side.

The Promptfoo suite has the symmetric registry surface, previously with zero
machine-checked invariants:

  * disk  : ``evals/*_selftest.py`` (the eval-only negative self-tests) plus
            the fixed strict layer ``evals/fingerprint_check.py``;
  * yaml  : ``evals/promptfooconfig.yaml`` -- one ``script:`` per case;
  * README: ``evals/README.md`` headline seed-case counts.

A regression here is silent but real: adding a self-test without registering it
in the yaml means Promptfoo never runs it (a false-green); a yaml case pointing
at a deleted script only fails at run time; registering a script whose PASS
marker is never asserted lets the case pass without proving the script's
success path (weakened assertions); or the README counts drift from the yaml.

This test reads the REAL repository (like #29) and evaluates pure invariants;
the negative cases inject in-memory mutations (extra/missing registry entries,
drifted counts, a dropped marker assertion) -- no temp files, no repo edits.
The README per-case detail table is intentionally NOT pinned: its early rows do
not share a single machine-stable column format, while the two headline counts
plus the disk<->yaml set equality already cover total and per-self-test
registration without depending on that table's layout.

Scenarios (verified verbatim on the real repo first via probes):
  * 1 healthy : on the real repo, zero registry problems;
  * 3 negative: an on-disk self-test absent from the yaml is reported (orphan);
                a yaml script path absent from disk is reported (missing),
                covering a deleted/renamed target; the README headline seed
                count differing from the yaml case count is reported (drift);
  * 2 non-flag: the fixed strict layer evals/fingerprint_check.py must stay
                registered; every evals self-test plus fingerprint_check must
                have its SUCCESS/STABLE marker asserted as a yaml `value:`
                (no script registered without a success assertion);
  * 1 mutation: deleting one self-test's marker assertion from the yaml text
                must be detected (proves the marker check is not vacuous).
"""

from __future__ import annotations

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
EVALS_DIR = REPO_ROOT / "evals"
YAML_PATH = EVALS_DIR / "promptfooconfig.yaml"
README_PATH = EVALS_DIR / "README.md"

SUCCESS_MARKER = "eval registry selftest: PASS"
FIXED_EVAL_SCRIPTS = ("evals/fingerprint_check.py",)

_SCRIPT_RE = re.compile(r"(?m)^\s*script:\s*(\S+)")
_CASE_RE = re.compile(r"(?m)^\s*-\s*description:")
_MARKER_RE = re.compile(r'(?:SUCCESS_MARKER|STABLE_MARKER)\s*=\s*["\']([^"\']+)["\']')
_README_COUNT_RES = (
    re.compile(r"custom provider \+\s*(\d+)\s*个\s*seed 用例"),
    re.compile(r"seed 用例\*\*（(\d+)\s*个）"),
)


def _marker_of(script_path: pathlib.Path) -> str:
    m = _MARKER_RE.search(script_path.read_text(encoding="utf-8"))
    assert m is not None, f"no SUCCESS/STABLE marker in {script_path.name}"
    return m.group(1)


def evaluate(disk_selftest_names, yaml_text, readme_text, exists):
    """Return a sorted list of registry problems; empty == consistent.

    Pure over its inputs so negative cases can inject mutations without files.
    `exists(rel)` reports whether a yaml-referenced path exists on disk.
    """
    problems = []

    yaml_scripts = _SCRIPT_RE.findall(yaml_text)
    yaml_case_count = len(_CASE_RE.findall(yaml_text))
    yaml_selftest = {
        pathlib.PurePosixPath(s).name
        for s in yaml_scripts
        if s.startswith("evals/") and s.endswith("_selftest.py")
    }
    disk_set = set(disk_selftest_names)

    # 1) disk <-> yaml self-test set, both directions
    for name in sorted(disk_set - yaml_selftest):
        problems.append(f"orphan self-test on disk not registered in yaml: {name}")
    for name in sorted(yaml_selftest - disk_set):
        problems.append(f"yaml references self-test absent on disk: {name}")

    # 2) every yaml-referenced path (scripts/config/evals; first token drops args)
    for rel in yaml_scripts:
        path_token = rel.split()[0]
        if not exists(path_token):
            problems.append(f"yaml script path missing on disk: {path_token}")

    # 3) one script per case
    if len(yaml_scripts) != yaml_case_count:
        problems.append(
            f"yaml script count {len(yaml_scripts)} != case count {yaml_case_count}"
        )

    # 4) fixed strict layer must stay registered
    for fixed in FIXED_EVAL_SCRIPTS:
        if fixed not in yaml_scripts:
            problems.append(f"fixed eval script not registered: {fixed}")

    # 5) every registered on-disk evals self-test + fixed scripts must have its
    #    marker asserted. Only the intersection is read for markers: an orphan
    #    (on disk but not in yaml) is already reported above and must not be
    #    required to carry a yaml assertion; in-memory orphan fixtures are not
    #    real files either.
    for name in sorted(disk_set & yaml_selftest):
        marker = _marker_of(EVALS_DIR / name)
        if marker not in yaml_text:
            problems.append(f"success marker not asserted in yaml for {name}: {marker}")
    for fixed in FIXED_EVAL_SCRIPTS:
        p = REPO_ROOT / fixed
        if p.exists():
            marker = _marker_of(p)
            if marker not in yaml_text:
                problems.append(f"success marker not asserted in yaml for {fixed}: {marker}")

    # 6) README headline counts must equal the yaml case count
    for rx in _README_COUNT_RES:
        m = rx.search(readme_text)
        if not m:
            problems.append(f"README count pattern not found: {rx.pattern}")
        elif int(m.group(1)) != yaml_case_count:
            problems.append(
                f"README seed count {m.group(1)} != yaml case count {yaml_case_count}"
            )

    return sorted(problems)


def _real_inputs():
    yaml_text = YAML_PATH.read_text(encoding="utf-8")
    readme_text = README_PATH.read_text(encoding="utf-8")
    disk = sorted(p.name for p in EVALS_DIR.glob("*_selftest.py"))
    exists = lambda rel: (REPO_ROOT / rel).exists()  # noqa: E731
    return disk, yaml_text, readme_text, exists


def main() -> int:
    try:
        disk, yaml_text, readme_text, exists = _real_inputs()

        # healthy: real repo is consistent
        problems = evaluate(disk, yaml_text, readme_text, exists)
        assert problems == [], "real repo should be consistent: " + "; ".join(problems)
        print("  ok healthy real-repo eval registry is consistent")

        # N1: orphan self-test on disk but not in yaml
        p1 = evaluate(sorted(set(disk) | {"zzz_orphan_selftest.py"}), yaml_text, readme_text, exists)
        assert any("orphan self-test" in x for x in p1), p1
        print("  ok negative orphan on-disk self-test is reported")

        # N2: yaml references a script path that does not exist on disk
        # (add a matching description so the case/script 1:1 invariant stays neutral)
        y_missing = (
            yaml_text
            + "  - description: 'negative fixture missing target'\n"
            + "    vars:\n      script: evals/nonexistent_guard_selftest.py\n"
        )
        p2 = evaluate(disk, y_missing, readme_text, exists)
        assert any("missing on disk" in x for x in p2), p2
        assert not any("script count" in x for x in p2), p2
        print("  ok negative yaml script missing on disk is reported")

        # N3: README headline count drifts from yaml case count (mutate the
        # current headline number, whatever it is, to a deliberately wrong one)
        m_head = _README_COUNT_RES[0].search(readme_text)
        assert m_head, "fixture: README headline count anchor missing"
        cur = m_head.group(1)
        drifted = readme_text.replace(f"+ {cur} 个 seed 用例", "+ 99 个 seed 用例", 1)
        assert drifted != readme_text, "fixture: README headline count not replaced"
        p3 = evaluate(disk, yaml_text, drifted, exists)
        assert any("README seed count 99" in x for x in p3), p3
        print("  ok negative README/yaml count drift is reported")

        # NF1: fixed strict layer fingerprint_check must stay registered
        assert "evals/fingerprint_check.py" in _SCRIPT_RE.findall(yaml_text)
        print("  ok non-flag fixed fingerprint_check.py stays registered")

        # NF2: every evals self-test + fingerprint_check has its marker asserted
        marker_problems = [x for x in problems if "marker not asserted" in x]
        assert marker_problems == [], marker_problems
        assert len(disk) >= 17, f"expected >=17 self-tests, got {len(disk)}"
        print(f"  ok non-flag all {len(disk)} self-tests + fingerprint_check markers asserted")

        # mutation: drop one self-test's PASS marker assertion from the yaml text
        victim = _marker_of(EVALS_DIR / "frozen_guard_selftest.py")
        yaml_mut = yaml_text.replace(f"value: '{victim}'", "value: 'WRONG MARKER'", 1)
        assert yaml_mut != yaml_text, "fixture: victim marker assertion anchor missing"
        pm = evaluate(disk, yaml_mut, readme_text, exists)
        assert any("frozen_guard_selftest.py" in x and "marker not asserted" in x for x in pm), pm
        print("  ok mutation dropped marker assertion is detected (check is not vacuous)")

    except AssertionError as exc:
        print(SUCCESS_MARKER.replace("PASS", "FAIL") + f": {exc}")
        return 1
    print(SUCCESS_MARKER)
    print("3 negative, 2 non-flag, 1 healthy, 1 mutation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
