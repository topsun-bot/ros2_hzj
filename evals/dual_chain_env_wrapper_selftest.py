#!/usr/bin/env python3
"""Contract/negative self-test for the dual-chain env thin wrapper (#34).

Context
-------
`dimos_bridge/dual_chain_env.py` is the thin DimOS-facing wrapper around the
single dual-chain env source of truth, `config/env/load.py` (#32 pins load.py
itself; #19 pins the guard that reads the shell scripts). The wrapper must only
re-export via importlib -- it must not copy the constants -- and its
`apply_chain_b` must forward `unset=CHAIN_B_UNSET` so a pre-existing
`CYCLONEDDS_URI` (external Cyclone config) is removed when aligning to Chain B.

That wrapper layer had no executable regression. A regression here is silent
but real: copying a constant means the wrapper can drift from load.py; dropping
the `unset=` argument leaks a stale Cyclone URI into Chain B; importing the
wrapper could mutate `os.environ`; or a missing load.py could be swallowed.

Pure standard library; in-process `apply_*` calls are wrapped in an environment
snapshot that is always restored; import-purity and the missing-source failure
run in isolated subprocesses; the broken-wrapper fixture is written to a
tempdir (the repo is never edited, no in-tree fixture). Not a CI gate (not in
run_all_gates.GATES, not enumerated by CI structure, no ci.yml wiring).

Scenarios (real behavior first captured verbatim via /tmp probes):
  * 1 healthy: CHAIN_A/CHAIN_B are the SAME objects as the wrapper's loaded
    source (`is`, re-export not copy); chain_a_env()/chain_b_env() equal the
    source constants (describe delegation); `_ENV_PY` resolves to the repo
    config/env/load.py and exists; `__all__` is exactly the six exported names;
  * 3 negative: importing the wrapper in a clean subprocess must not change
    RMW_IMPLEMENTATION / ROS_DOMAIN_ID / FASTRTPS_DEFAULT_PROFILES_FILE /
    CYCLONEDDS_URI (module-level purity); apply_chain_b must remove a preset
    CYCLONEDDS_URI (unset forwarded); a wrapper-shaped module whose load.py is
    missing must fail to import (FileNotFoundError), never silently succeed;
  * 2 non-flag: apply_chain_a sets the Chain A triple (rmw_fastrtps_cpp /
    domain 42 / fastdds.xml); chain_a_env() returns a fresh dict each call that
    is not the module constant (callers mutating it must not corrupt source);
  * 1 mutation: a blind delegation `load.apply(CHAIN_B)` without `unset` leaks
    the preset CYCLONEDDS_URI (the check observes the leak), while the real
    wrapper.apply_chain_b removes it -- distinguishing a wrapper that forgets
    to forward unset.
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
WRAPPER_PATH = REPO_ROOT / "dimos_bridge" / "dual_chain_env.py"
LOAD_PATH = REPO_ROOT / "config" / "env" / "load.py"

SUCCESS_MARKER = "dual-chain env wrapper selftest: PASS"
_ENV_KEYS = (
    "RMW_IMPLEMENTATION",
    "ROS_DOMAIN_ID",
    "FASTRTPS_DEFAULT_PROFILES_FILE",
    "CYCLONEDDS_URI",
)
_EXPECTED_ALL = {
    "CHAIN_A",
    "CHAIN_B",
    "apply_chain_a",
    "apply_chain_b",
    "chain_a_env",
    "chain_b_env",
}


class _EnvSnapshot:
    def __init__(self) -> None:
        self.saved = {k: os.environ.get(k) for k in _ENV_KEYS}

    def restore(self) -> None:
        for k, v in self.saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _load_wrapper():
    spec = importlib.util.spec_from_file_location(
        "hzj_dual_chain_env_wrapper_selftest", WRAPPER_PATH
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _check_healthy(w) -> None:
    # re-export, not copy: same dict objects as the wrapper's loaded source
    assert w.CHAIN_A is w._env.CHAIN_A, "CHAIN_A must be re-exported, not copied"
    assert w.CHAIN_B is w._env.CHAIN_B, "CHAIN_B must be re-exported, not copied"
    assert w.CHAIN_A == w._env.CHAIN_A and w.CHAIN_B == w._env.CHAIN_B
    # describe delegation values
    assert w.chain_a_env() == w._env.CHAIN_A
    assert w.chain_b_env() == w._env.CHAIN_B
    assert w.chain_a_env()["RMW_IMPLEMENTATION"] == "rmw_fastrtps_cpp"
    assert w.chain_b_env()["RMW_IMPLEMENTATION"] == "rmw_cyclonedds_cpp"
    # source path resolves to the repo single source of truth
    assert pathlib.Path(w._ENV_PY).resolve() == LOAD_PATH.resolve()
    assert pathlib.Path(w._ENV_PY).exists()
    # exact public surface
    assert set(w.__all__) == _EXPECTED_ALL, w.__all__


def _check_negative_import_pure() -> None:
    code = (
        "import importlib.util,os;"
        f"spec=importlib.util.spec_from_file_location('w',r'{WRAPPER_PATH}');"
        "before={k:os.environ.get(k) for k in "
        "('RMW_IMPLEMENTATION','ROS_DOMAIN_ID','FASTRTPS_DEFAULT_PROFILES_FILE','CYCLONEDDS_URI')};"
        "m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);"
        "after={k:os.environ.get(k) for k in before};"
        "assert before==after, (before,after);print('PURE')"
    )
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert r.returncode == 0 and "PURE" in r.stdout, r.stderr


def _check_negative_chain_b_unset(w) -> None:
    snap = _EnvSnapshot()
    try:
        os.environ["CYCLONEDDS_URI"] = "file:///external-cyclone-must-be-removed"
        w.apply_chain_b()
        assert "CYCLONEDDS_URI" not in os.environ, \
            "apply_chain_b must forward unset and remove a preset CYCLONEDDS_URI"
        assert os.environ.get("RMW_IMPLEMENTATION") == "rmw_cyclonedds_cpp"
        assert os.environ.get("ROS_DOMAIN_ID") == "0"
    finally:
        snap.restore()


def _check_negative_missing_source_fails() -> None:
    with tempfile.TemporaryDirectory(prefix="hzj-wrap-selftest-") as d:
        bad = pathlib.Path(d) / "bad_wrapper.py"
        bad.write_text(
            "import importlib.util\n"
            "from pathlib import Path\n"
            f"p = Path({str(d)!r}) / 'no_such_load.py'\n"
            "spec = importlib.util.spec_from_file_location('x', p)\n"
            "if spec is None or spec.loader is None:\n"
            "    raise ImportError(f'cannot load env helper at {p}')\n"
            "m = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(m)\n",
            encoding="utf-8",
        )
        r = subprocess.run([sys.executable, str(bad)], capture_output=True, text=True)
        assert r.returncode != 0, "a wrapper missing its load.py must fail to import"
        assert "No such file" in r.stderr or "FileNotFoundError" in r.stderr, r.stderr


def _check_nonflag_chain_a(w) -> None:
    snap = _EnvSnapshot()
    try:
        w.apply_chain_a()
        assert os.environ.get("RMW_IMPLEMENTATION") == "rmw_fastrtps_cpp"
        assert os.environ.get("ROS_DOMAIN_ID") == "42"
        assert os.path.basename(os.environ.get("FASTRTPS_DEFAULT_PROFILES_FILE", "")) == "fastdds.xml"
    finally:
        snap.restore()


def _check_nonflag_fresh_describe(w) -> None:
    a1, a2 = w.chain_a_env(), w.chain_a_env()
    assert a1 is not w.CHAIN_A, "describe must not return the shared constant"
    assert a1 is not a2, "describe must return a fresh dict per call"
    assert a1 == w.CHAIN_A  # equal but independent -> caller mutation cannot corrupt source


def _check_mutation_blind_forgets_unset(w) -> None:
    snap = _EnvSnapshot()
    try:
        os.environ["CYCLONEDDS_URI"] = "file:///external-cyclone-must-be-removed"
        # blind delegation: apply(CHAIN_B) without unset (the regression shape)
        w._env.apply(w._env.CHAIN_B)
        assert os.environ.get("CYCLONEDDS_URI") == "file:///external-cyclone-must-be-removed", \
            "sanity: a wrapper that forgets unset must leak the URI"
        # real wrapper forwards unset and removes it
        w.apply_chain_b()
        assert "CYCLONEDDS_URI" not in os.environ
    finally:
        snap.restore()


def main() -> int:
    try:
        w = _load_wrapper()
        checks = [
            ("healthy re-export identity / delegation / __all__ / path", lambda: _check_healthy(w)),
            ("negative import wrapper leaves os.environ unchanged", _check_negative_import_pure),
            ("negative apply_chain_b removes preset CYCLONEDDS_URI", lambda: _check_negative_chain_b_unset(w)),
            ("negative missing load.py fails wrapper import", _check_negative_missing_source_fails),
            ("non-flag apply_chain_a sets Chain A triple", lambda: _check_nonflag_chain_a(w)),
            ("non-flag describe returns fresh independent dict", lambda: _check_nonflag_fresh_describe(w)),
            ("mutation blind delegation leaks URI vs wrapper removes", lambda: _check_mutation_blind_forgets_unset(w)),
        ]
        for label, fn in checks:
            fn()
            print(f"  ok {label}")
    except AssertionError as exc:
        print(f"{SUCCESS_MARKER.replace('PASS', 'FAIL')}: {exc}")
        return 1
    print(SUCCESS_MARKER)
    print("3 negative, 2 non-flag, 1 healthy, 1 mutation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
