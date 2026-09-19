#!/usr/bin/env python3
"""Negative self-test for the dual-chain env cross-check guard (eval-only).

Invoked by the Promptfoo local-script provider. It lives under ``evals/`` on
purpose, like ``fingerprint_check.py`` and ``frozen_guard_selftest.py``: it is
**not** one of the 13 CI gates, is not enumerated by
``scripts/run_all_gates.py``, and needs no ``.github/workflows/ci.yml`` wiring
(so it is not blocked by the GitHub ``workflow`` token scope).

Why this exists
---------------
``scripts/check_dual_chain_baseline.py`` (modernization plan Step 4) does not
only check doc markers: it imports ``config/env/load.py`` as the single
executable source of truth and cross-checks it four ways --

  * env truth  : load.py CHAIN_A/CHAIN_B equal the contracted rmw/domain, the
                 profiles path resolves to config/fastdds.xml, CYCLONEDDS_URI is
                 in CHAIN_B_UNSET, and importing load.py does not mutate
                 os.environ;
  * cross-check A: literal chain_a.sh exports equal load.py CHAIN_A;
  * cross-check B: literal chain_b.sh exports equal load.py CHAIN_B;
  * wrapper    : dimos_bridge/dual_chain_env.py re-exports / chain_*_env()
                 equal load.py;
  * plus chain_b.sh must not export CYCLONEDDS_URI and must unset it.

The positive eval case (#11) only proves the *current* tree is healthy; it
cannot prove these checks still fire. If a comparison were widened or a branch
were broken so a drift went unreported, every positive run (gate, #11, and the
#17 stdout fingerprint) would stay green while the single-source-of-truth
guarantee silently vanished. During iteration 3 this negative behaviour was
verified only with throwaway ``/tmp`` fixtures; this script commits that
evidence as a re-runnable regression.

It builds a minimal env tree (load.py + chain_a.sh + chain_b.sh + wrapper + an
existence-only config/fastdds.xml) inside a ``tempfile`` and drives the guard's
injectable ``render(root=...)``. The doc/marker files are intentionally absent
in the temp tree, so render still exits 1 for missing docs -- that is fine:
assertions look only at the five ``FAIL env|chain A|chain B`` line families and
ignore unrelated doc failures. Six negative scenarios must each produce their
specific FAIL lines (and, where relevant, must NOT trip an unrelated check); a
minimal healthy tree must produce zero env/chain FAIL lines; and the real repo
tree must render exit 0 with all four ``ok env ...`` lines. A memory-only
mutation (the CYCLONEDDS_URI export detector replaced by a never-matching
regex) must make scenario 5 go undetected, proving the test is not vacuous.

Read-only: files are created only inside a ``tempfile`` directory and the repo
is never edited. The one scenario that makes a fake load.py write os.environ is
snapshotted and restored. Standard library only. Exit 0 when every expectation
holds, exit 1 (with details) otherwise.
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent
ROOT = EVALS_DIR.parent
SCRIPTS = ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS))
import check_dual_chain_baseline as g  # noqa: E402  (sys.path set just above)

SUCCESS_MARKER = "dual-chain env guard selftest: PASS"

# The five env/chain FAIL line families owned by the Step 4 cross-checks. Kept
# as exact line prefixes so a missing *file* whose path happens to contain "env"
# (e.g. "- **FAIL missing:** `config/env/load.py`") is never counted here.
ENV_FAIL_PREFIXES = (
    "- **FAIL env truth:",
    "- **FAIL env cross-check:",
    "- **FAIL env wrapper:",
    "- **FAIL chain A:",
    "- **FAIL chain B:",
)

_LOAD_TMPL = (
    "import os\n"
    "from pathlib import Path\n"
    "REPO_ROOT = Path(__file__).resolve().parents[2]\n"
    'CHAIN_A = {{"RMW_IMPLEMENTATION": "rmw_fastrtps_cpp", '
    '"ROS_DOMAIN_ID": "{a}",\n'
    '           "FASTRTPS_DEFAULT_PROFILES_FILE": '
    'str(REPO_ROOT / "config" / "fastdds.xml")}}\n'
    'CHAIN_B = {{"RMW_IMPLEMENTATION": "rmw_cyclonedds_cpp", '
    '"ROS_DOMAIN_ID": "{b}"}}\n'
    'CHAIN_B_UNSET = ("CYCLONEDDS_URI",)\n'
    "{mutate}\n"
)

# Healthy wrapper: mirrors the real dimos_bridge/dual_chain_env.py -- loads the
# temp load.py via importlib and re-exports it, so it always follows load.py.
_WRAP_FOLLOW = (
    "import importlib.util\n"
    "from pathlib import Path\n"
    'p = Path(__file__).resolve().parents[1] / "config" / "env" / "load.py"\n'
    's = importlib.util.spec_from_file_location("wload", p)\n'
    "e = importlib.util.module_from_spec(s); s.loader.exec_module(e)\n"
    "CHAIN_A = e.CHAIN_A; CHAIN_B = e.CHAIN_B\n"
    "def chain_a_env():\n    return dict(CHAIN_A)\n"
    "def chain_b_env():\n    return dict(CHAIN_B)\n"
)

# Forbidden wrapper: hardcodes a drifted constant instead of re-exporting.
_WRAP_FAKE = (
    'CHAIN_A = {"RMW_IMPLEMENTATION": "rmw_fastrtps_cpp", '
    '"ROS_DOMAIN_ID": "99",\n'
    '           "FASTRTPS_DEFAULT_PROFILES_FILE": ""}\n'
    'CHAIN_B = {"RMW_IMPLEMENTATION": "rmw_cyclonedds_cpp", '
    '"ROS_DOMAIN_ID": "0"}\n'
    "def chain_a_env():\n    return dict(CHAIN_A)\n"
    "def chain_b_env():\n    return dict(CHAIN_B)\n"
)

# (label, tree kwargs, fragments that MUST appear in env/chain FAIL lines,
#  fragments that MUST NOT appear there).
NEGATIVE: list[tuple[str, dict, list[str], list[str]]] = [
    (
        "chain A domain drifts 42->43 while chain_a.sh stays 42",
        {"a": "43"},
        ["FAIL env truth:", "chain_a.sh != load.py CHAIN_A"],
        ["chain_b.sh != load.py CHAIN_B", "FAIL env wrapper:"],
    ),
    (
        "chain B domain drifts 0->1 while chain_b.sh stays 0",
        {"b": "1"},
        ["FAIL env truth:", "chain_b.sh != load.py CHAIN_B"],
        ["chain_a.sh != load.py CHAIN_A", "FAIL env wrapper:"],
    ),
    (
        "wrapper hardcodes a drifted re-export",
        {"wrap": "fake"},
        ["FAIL env wrapper:", "re-exports != load.py"],
        ["FAIL env truth:", "FAIL env cross-check:"],
    ),
    (
        "importing load.py mutates os.environ",
        {"mutate": 'os.environ["ROS_DOMAIN_ID"]="7"'},
        ["FAIL env truth:"],
        ["FAIL env cross-check:", "FAIL env wrapper:"],
    ),
    (
        "chain_b.sh exports CYCLONEDDS_URI (even though it also unsets it)",
        {"b_uri_export": True, "b_unset": True},
        ["FAIL chain B:", "helper must not export CYCLONEDDS_URI"],
        ["need anchored unset"],
    ),
    (
        "chain_b.sh omits `unset CYCLONEDDS_URI`",
        {"b_unset": False},
        ["FAIL chain B:", "need anchored unset CYCLONEDDS_URI"],
        ["helper must not export"],
    ),
]

# Fragments the real healthy repo tree must print once render() runs on it.
REAL_OK_FRAGMENTS = (
    "ok env truth:",
    "chain_a.sh exports match load.py CHAIN_A",
    "chain_b.sh exports match load.py CHAIN_B",
    "ok env wrapper:",
)


def _build_tree(
    root: Path,
    *,
    a: str = "42",
    b: str = "0",
    mutate: str = "",
    wrap: str = "follow",
    b_uri_export: bool = False,
    b_unset: bool = True,
) -> None:
    (root / "config" / "env").mkdir(parents=True)
    (root / "dimos_bridge").mkdir(parents=True)
    # Existence-only placeholder; the gate's content freeze is the boundary job.
    (root / "config" / "fastdds.xml").write_text("<profiles/>\n", encoding="utf-8")
    (root / "config" / "env" / "load.py").write_text(
        _LOAD_TMPL.format(a=a, b=b, mutate=mutate), encoding="utf-8"
    )
    (root / "config" / "env" / "chain_a.sh").write_text(
        "export RMW_IMPLEMENTATION=rmw_fastrtps_cpp\n"
        "export ROS_DOMAIN_ID=42\n"
        'export FASTRTPS_DEFAULT_PROFILES_FILE='
        '"${_ROS2_HZJ_ROOT}/config/fastdds.xml"\n',
        encoding="utf-8",
    )
    chain_b = (
        "export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp\n"
        "export ROS_DOMAIN_ID=0\n"
    )
    if b_uri_export:
        chain_b += "export CYCLONEDDS_URI=file:///should-not-be-set.xml\n"
    if b_unset:
        chain_b += "unset CYCLONEDDS_URI\n"
    (root / "config" / "env" / "chain_b.sh").write_text(chain_b, encoding="utf-8")
    (root / "dimos_bridge" / "dual_chain_env.py").write_text(
        _WRAP_FAKE if wrap == "fake" else _WRAP_FOLLOW, encoding="utf-8"
    )


def _env_fail_text(root: Path) -> str:
    """render(root) and return only the env/chain FAIL lines (joined)."""
    snapshot = dict(os.environ)
    try:
        out, _code = g.render(root=root)
    finally:
        # A fake load.py in the mutate scenario writes os.environ; restore.
        os.environ.clear()
        os.environ.update(snapshot)
    lines = [
        ln.strip()
        for ln in out.splitlines()
        if ln.strip().startswith(ENV_FAIL_PREFIXES)
    ]
    return "\n".join(lines)


def _check_negative(failures: list[str]) -> int:
    passed = 0
    for label, kw, must, must_not in NEGATIVE:
        with tempfile.TemporaryDirectory(prefix="env_guard_neg_") as tmp:
            _build_tree(Path(tmp), **kw)
            text = _env_fail_text(Path(tmp))
        problems = [f"missing fragment {frag!r}" for frag in must if frag not in text]
        problems += [
            f"unexpected fragment {frag!r}" for frag in must_not if frag in text
        ]
        if problems:
            failures.append(f"negative '{label}': " + "; ".join(problems))
            continue
        passed += 1
    return passed


def _check_minimal_healthy(failures: list[str]) -> int:
    """A fully-correct minimal env tree must raise ZERO env/chain FAIL lines."""
    with tempfile.TemporaryDirectory(prefix="env_guard_ok_") as tmp:
        text = _env_fail_text(Path(tmp))
    if text:
        failures.append(
            "minimal healthy tree raised unexpected env/chain FAIL lines:\n" + text
        )
        return 0
    return 1


def _check_real_tree(failures: list[str]) -> int:
    out, code = g.render()
    if code != 0:
        failures.append(f"real repo render: expected exit 0, got {code}")
        return 0
    missing = [frag for frag in REAL_OK_FRAGMENTS if frag not in out]
    if missing:
        failures.append(
            "real repo healthy output missing fragments: " + ", ".join(missing)
        )
        return 0
    return 1


def _check_mutation(failures: list[str]) -> int:
    """Widening the CYCLONEDDS_URI export detector must hide scenario 5."""
    original = g._EXPORT_CYCLONE_URI_RE
    g._EXPORT_CYCLONE_URI_RE = re.compile(r"(?!)")  # never matches
    try:
        with tempfile.TemporaryDirectory(prefix="env_guard_mut_") as tmp:
            _build_tree(
                Path(tmp), b_uri_export=True, b_unset=True
            )
            text = _env_fail_text(Path(tmp))
    finally:
        g._EXPORT_CYCLONE_URI_RE = original

    if "helper must not export CYCLONEDDS_URI" in text:
        failures.append(
            "mutation did not disable the CYCLONEDDS_URI export detector; the "
            "scenario-5 assertion would pass even with a dead detector"
        )
        return 0

    # Sanity: with the real detector restored, scenario 5 is caught again.
    with tempfile.TemporaryDirectory(prefix="env_guard_mutrest_") as tmp:
        _build_tree(Path(tmp), b_uri_export=True, b_unset=True)
        restored = _env_fail_text(Path(tmp))
    if "helper must not export CYCLONEDDS_URI" not in restored:
        failures.append("after restoring the detector, scenario 5 was not caught")
        return 0
    return 1


def main() -> int:
    failures: list[str] = []

    negative = _check_negative(failures)
    healthy_minimal = _check_minimal_healthy(failures)
    healthy_real = _check_real_tree(failures)
    healthy = healthy_minimal + healthy_real
    mutation = _check_mutation(failures)

    print("# dual-chain env cross-check guard negative self-test")
    print(
        f"- negative scenarios caught: {negative}/{len(NEGATIVE)}; "
        f"healthy cases clean: {healthy}/2; mutation cases: {mutation}/1"
    )

    if failures:
        print("\nFAIL:")
        for item in failures:
            print(f"- {item}")
        print(
            "\nThe dual-chain env cross-check guard no longer behaves as "
            f"specified. Expected {SUCCESS_MARKER!r}. Exit 1."
        )
        return 1

    print(
        f"- **{SUCCESS_MARKER}** ({len(NEGATIVE)} negative, 2 healthy, "
        "1 mutation)"
    )
    print(
        "\nThe guard catches domain drift in either chain, shell/load.py "
        "cross-check drift, wrapper re-export drift, import-time os.environ "
        "mutation, and chain_b.sh CYCLONEDDS_URI export/missing-unset; stays "
        "silent on a healthy minimal tree and on the real repo; and a widened "
        "detector is proven detectable. Read-only, tempdir-only. Exit 0."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
