#!/usr/bin/env python3
"""Negative/contract self-test for ``config/env/load.py`` (eval #32, eval-only).

Context
-------
``config/env/load.py`` is the single source of truth for the dual-chain
environment contract (Chain A = rmw_fastrtps_cpp / domain 42 / fastdds.xml;
Chain B = rmw_cyclonedds_cpp / domain 0 with ``CYCLONEDDS_URI`` unset). The
existing eval #19 (``dual_chain_env_guard_selftest.py``) only proves that the
*guard* ``check_dual_chain_env.py`` detects tampered shell fixtures; it never
pins what the env source-of-truth tool itself must do. The Mac HIL note records
print/import behavior as prose, not as an executable regression.

If ``load.py`` were hollowed out -- ``describe`` silently accepting an unknown
chain, ``apply`` writing values but never popping ``CYCLONEDDS_URI`` (so an
external Cyclone URI would silently pollute Chain B), the CLI accepting an
unknown subcommand as success, the shell export emitting unescaped quotes, or
importing the module mutating ``os.environ`` -- the dual-chain contract would
drift while the gates (which mostly assert the guard and the shell wrappers)
could stay green.

This script pins the source-of-truth tool itself. It is eval-only, pure
standard library, and never edits the repo: in-process ``apply`` runs snapshot
and restore ``os.environ`` (and the imported function) on exit, while
import-purity and CLI checks run in fresh subprocesses. It is not a CI gate
(not in ``run_all_gates.GATES``, not enumerated by CI structure, no ci.yml
wiring).

Scenarios (real behavior first captured verbatim via a /tmp probe):
  * 3 negative: ``describe`` with an unknown chain must raise
    ``ValueError: unknown chain: ...``; an unknown CLI subcommand must exit 2
    (argparse choices), not succeed; ``apply`` for Chain B must *remove* a
    pre-existing ``CYCLONEDDS_URI`` (an unset that is skipped would leak an
    external Cyclone config into Chain B);
  * 2 non-flag: ``export_shell`` must single-quote/escape a value containing a
    quote and spaces so a POSIX shell round-trips it byte-for-byte (no false /
    broken export), and merely importing the module must leave ``os.environ``
    unchanged (import purity; no implicit apply);
  * 1 healthy: ``describe`` returns the exact Chain A/B contract (rmw, domain,
    fastdds.xml absolute path) and all six CLI subcommands exit 0 with their
    expected output;
  * 1 mutation: an ``apply`` stub that updates values but drops the ``unset``
    pop leaks ``CYCLONEDDS_URI`` under Chain B (the check must observe that
    leak); restoring the real ``apply`` removes it again.
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
LOAD_PATH = REPO_ROOT / "config" / "env" / "load.py"

SUCCESS_MARKER = "dual-chain env load selftest: PASS"

_ENV_KEYS = (
    "RMW_IMPLEMENTATION",
    "ROS_DOMAIN_ID",
    "FASTRTPS_DEFAULT_PROFILES_FILE",
    "CYCLONEDDS_URI",
)


def _load_module():
    spec = importlib.util.spec_from_file_location("hzj_env_load_selftest", LOAD_PATH)
    assert spec and spec.loader, "cannot load load.py"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # importing must not apply() anything
    return mod


load = _load_module()


def _cli(*args: str) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(LOAD_PATH), *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout or "", proc.stderr or ""


class _EnvSnapshot:
    def __enter__(self):
        self._env = dict(os.environ)
        self._apply = load.apply
        return self

    def __exit__(self, *exc):
        load.apply = self._apply
        for key in _ENV_KEYS:
            if key in self._env:
                os.environ[key] = self._env[key]
            else:
                os.environ.pop(key, None)
        return False


def _check_healthy() -> None:
    a = load.describe("a")
    b = load.describe("b")
    assert a == {
        "RMW_IMPLEMENTATION": "rmw_fastrtps_cpp",
        "ROS_DOMAIN_ID": "42",
        "FASTRTPS_DEFAULT_PROFILES_FILE": str(REPO_ROOT / "config" / "fastdds.xml"),
    }, a
    assert b == {
        "RMW_IMPLEMENTATION": "rmw_cyclonedds_cpp",
        "ROS_DOMAIN_ID": "0",
    }, b
    assert load.CHAIN_B_UNSET == ("CYCLONEDDS_URI",), load.CHAIN_B_UNSET
    xml = pathlib.Path(a["FASTRTPS_DEFAULT_PROFILES_FILE"])
    assert xml.name == "fastdds.xml" and xml.is_file(), xml

    rc_pa, out_pa, _ = _cli("print-a")
    assert rc_pa == 0 and "RMW_IMPLEMENTATION=rmw_fastrtps_cpp" in out_pa
    assert "ROS_DOMAIN_ID=42" in out_pa and out_pa.count("\n") == 3, out_pa
    rc_pb, out_pb, _ = _cli("print-b")
    assert rc_pb == 0 and "RMW_IMPLEMENTATION=rmw_cyclonedds_cpp" in out_pb
    assert "ROS_DOMAIN_ID=0" in out_pb and "FASTRTPS" not in out_pb, out_pb

    rc_ea, out_ea, _ = _cli("export-a")
    assert rc_ea == 0 and "export RMW_IMPLEMENTATION='rmw_fastrtps_cpp'" in out_ea
    assert "export FASTRTPS_DEFAULT_PROFILES_FILE='" in out_ea
    assert "config/fastdds.xml" in out_ea, out_ea
    rc_eb, out_eb, _ = _cli("export-b")
    assert rc_eb == 0 and "unset CYCLONEDDS_URI" in out_eb
    assert "export ROS_DOMAIN_ID='0'" in out_eb and "FASTRTPS" not in out_eb, out_eb

    for sub in ("apply-a", "apply-b"):
        rc, out, _ = _cli(sub)
        assert rc == 0 and f"applied chain {sub[-1]} to current process only" in out, (sub, out)


def _check_negative_unknown_chain() -> None:
    try:
        load.describe("z")
    except ValueError as exc:
        assert "unknown chain: z" in str(exc), str(exc)
        return
    raise AssertionError("describe('z') must raise ValueError, not silently return")


def _check_negative_bad_subcommand() -> None:
    rc, _out, err = _cli("bogus")
    assert rc == 2, f"unknown subcommand must exit 2 (argparse choices), got {rc}"
    assert "invalid choice" in err or "usage:" in err, err


def _check_negative_apply_b_pops_uri() -> None:
    with _EnvSnapshot():
        os.environ["CYCLONEDDS_URI"] = "file:///must-not-leak-into-chain-b"
        load.apply(load.CHAIN_B, unset=load.CHAIN_B_UNSET)
        assert "CYCLONEDDS_URI" not in os.environ, "Chain B apply must unset CYCLONEDDS_URI"
        assert os.environ.get("RMW_IMPLEMENTATION") == "rmw_cyclonedds_cpp"
        assert os.environ.get("ROS_DOMAIN_ID") == "0"
        assert "FASTRTPS_DEFAULT_PROFILES_FILE" not in os.environ, \
            "Chain B must not carry the FastDDS profiles file"


def _check_nonflag_shell_escape_roundtrip() -> None:
    # A value with a single quote and spaces must be quoted/escaped so a POSIX
    # shell recovers it byte-for-byte (the dual-chain paths have no quotes, but
    # the escaper must still be correct rather than blindly wrapped).
    tricky = "a'b c"
    rendered = load.export_shell({"HZJ_ROUNDTRIP": tricky})
    assert load._sh_single(tricky) == "'a'\"'\"'b c'", load._sh_single(tricky)
    assert "export HZJ_ROUNDTRIP='a'\"'\"'b c'" in rendered, rendered
    proc = subprocess.run(
        ["sh", "-c", rendered + "\nprintf '%s' \"$HZJ_ROUNDTRIP\""],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == tricky, repr(proc.stdout)


def _check_nonflag_import_purity() -> None:
    # Fresh interpreter: importing load.py must not add/change/remove any env.
    code = (
        "import os,sys;"
        "before=dict(os.environ);"
        "sys.path.insert(0,'config/env');"
        "import load;"
        "after=dict(os.environ);"
        "print('PURE' if before==after else 'MUTATED')"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code], cwd=str(REPO_ROOT),
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "PURE", f"import mutated os.environ: {proc.stdout}{proc.stderr}"


def _check_mutation_apply_without_unset_leaks() -> None:
    with _EnvSnapshot():
        os.environ["CYCLONEDDS_URI"] = "file:///mutation-leak"
        real_apply = load.apply

        def blind_apply(values, *, unset=()):  # regression: update but never pop
            os.environ.update(values)

        load.apply = blind_apply
        load.apply(load.CHAIN_B, unset=load.CHAIN_B_UNSET)
        assert os.environ.get("CYCLONEDDS_URI") == "file:///mutation-leak", \
            "sanity: an apply that skips the unset pop must leak the URI"

        load.apply = real_apply
        load.apply(load.CHAIN_B, unset=load.CHAIN_B_UNSET)
        assert "CYCLONEDDS_URI" not in os.environ, \
            "real apply must re-catch the leak by popping CYCLONEDDS_URI"


def main() -> int:
    checks = [
        ("healthy describe + six CLI subcommands", _check_healthy),
        ("negative describe unknown chain raises", _check_negative_unknown_chain),
        ("negative unknown CLI subcommand exits 2", _check_negative_bad_subcommand),
        ("negative Chain B apply unsets CYCLONEDDS_URI", _check_negative_apply_b_pops_uri),
        ("non-flag shell escape round-trips", _check_nonflag_shell_escape_roundtrip),
        ("non-flag import leaves os.environ pure", _check_nonflag_import_purity),
        ("mutation apply-without-unset leaks then re-caught", _check_mutation_apply_without_unset_leaks),
    ]
    try:
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
