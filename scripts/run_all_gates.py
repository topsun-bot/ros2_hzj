#!/usr/bin/env python3
"""Run every project gate script and print a summary table.

This is a **runner**, not a new gate: it shells out to the existing
``scripts/check_*.py`` / ``scripts/prove_rmw.py`` / ``scripts/print_bench_gates.py``
one by one and records exit code + the canonical success marker each script
prints. It does not re-implement any check logic.

Why this exists
---------------
The 13 gates were historically run by hand, one ``python3 scripts/<name>.py``
at a time. That makes the 《3》 eval loop (run all gates after every change)
awkward and easy to forget one. This runner gives one command:

    python3 scripts/run_all_gates.py

Behavior contract
-----------------
- Exit 0 iff every listed script exits 0.
- Exit 1 iff any script exits non-zero.
- Prints a markdown table with columns: script, exit, marker-present.
- Does NOT modify any file, does NOT touch config/fastdds.xml or SCOREBOARD.md.
- Does NOT bootstrap a ROS runtime. On a vanilla Mac (no /opt/ros) most
  gates are filesystem/string checks and still exit 0 by design.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# (script path relative to repo root, success substring)
# The substring is the line each gate prints on success; the runner checks
# both exit code 0 AND substring present, so a script that accidentally
# exits 0 without printing its marker is still reported as suspicious.
GATES: list[tuple[str, str]] = [
    ("scripts/prove_rmw.py", "Exit 0"),
    ("scripts/print_bench_gates.py", "Bench gates healthy"),
    ("scripts/check_source_map.py", "Source map healthy"),
    ("scripts/check_risk_matrix.py", "Risk matrix healthy"),
    ("scripts/check_executor_map.py", "Executor map healthy"),
    ("scripts/check_runtime_provenance.py", "Runtime provenance healthy"),
    ("scripts/check_unitree_cyclone_swap.py", "Unitree Cyclone swap record healthy"),
    ("scripts/check_three_chain_repro.py", "Three-chain reproduce record healthy"),
    ("scripts/check_sink_layers.py", "Sink-layer record healthy"),
    ("scripts/check_dual_chain_baseline.py", "Dual-chain baseline healthy"),
    ("scripts/check_dod_evidence.py", "Product DoD evidence healthy"),
    ("scripts/check_cega_bridge_hold.py", "Cega / Bridge Hold healthy"),
]


def run_one(rel: str, marker: str) -> tuple[int, bool, str]:
    path = REPO_ROOT / rel
    if not path.exists():
        return 127, False, f"missing: {rel}"
    proc = subprocess.run(
        [sys.executable, str(path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    combined = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, (marker in combined), combined


def main() -> int:
    print(f"# run_all_gates @ {REPO_ROOT.name}\n")
    print("| script | exit | marker |")
    print("| --- | --- | --- |")
    failures = 0
    missing_marker = 0
    for rel, marker in GATES:
        rc, has_marker, _ = run_one(rel, marker)
        rc_str = "0" if rc == 0 else str(rc)
        marker_str = "ok" if has_marker else "MISSING"
        print(f"| `{rel}` | {rc_str} | {marker_str} |")
        if rc != 0:
            failures += 1
        elif not has_marker:
            missing_marker += 1
    total = len(GATES)
    healthy = total - failures
    print(f"\n- gates: {total}")
    print(f"- exit-0: {healthy}")
    print(f"- non-zero: {failures}")
    print(f"- zero-but-missing-marker: {missing_marker}")
    print()
    if failures or missing_marker:
        print("run_all_gates: FAIL")
        return 1
    print("run_all_gates: all gates green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
