#!/usr/bin/env python3
"""Negative self-test for the ros2-source-map honesty guard (eval-only).

Invoked by the Promptfoo local-script provider. It lives under ``evals/`` on
purpose, like ``fingerprint_check.py`` and the frozen/env/unitree guard
self-tests: it is **not** one of the 13 CI gates, is not enumerated by
``scripts/run_all_gates.py``, and needs no ``.github/workflows/ci.yml`` wiring
(so it is not blocked by the GitHub ``workflow`` token scope).

Why this exists
---------------
``scripts/check_source_map.py`` (wiki3 §13.2) parses
``docs/architecture/ros2-source-map.md`` and fails when the map disappears,
yields no in-repo paths, cites a path that does not exist, or cites an
allowlisted symbol (e.g. ``add_change`` in the vendored Fast-DDS
``WriterHistory.cpp``) that has been removed. The positive eval case (#2) and
the #17 stdout fingerprint only prove the *current, healthy* tree renders
green. They cannot prove the checks still fire after a tampering. If someone
deleted the map, stripped every citation, pointed at a removed file, or
removed a pinned symbol — and the detector had been widened to accept it —
every healthy-tree run (gate, #2, #17) would stay green while the source map
silently stopped describing the vendored code.

The guard's injectable ``render(root=...)`` is driven against minimal
hand-built temp trees (the map fixture is tiny, so unlike the Unitree swap doc
there is no need to copy the real map). It asserts:
  1. four negative scenarios ARE caught (exit 1, no success marker, the right
     FAIL family):
       N1 map deleted (FAIL map missing);
       N2 map present but no in-repo path extractable (FAIL no in-repo paths);
       N3 cited path missing on disk (FAIL missing);
       N4 allowlisted symbol removed from the cited vendor file (FAIL symbol);
  2. one warn-only contract: a stale cited line number where the symbol still
     exists prints WARN stale line but stays exit 0 (the documented
     "stale line numbers warn only" behaviour must not silently harden into a
     FAIL either);
  3. two healthy cases: the real repo ``render()`` and a minimal healthy temp
     tree both exit 0 with the success marker (proves the hand-built fixture
     itself is valid, so the negative cases do not fail for the wrong reason);
  4. one mutation: monkeypatching ``_md_paths.symbol_lines`` to always report a
     hit makes N4 slip (the tampered tree prints ``ok symbol`` and exits 0),
     and restoring it re-catches N4 — proving N4 actually depends on the
     symbol lookup in the detector rather than passing by accident.

Read-only: it creates files only inside ``tempfile`` directories and never
edits the repo. Standard library only. Exit 0 when every expectation holds,
exit 1 (with details) otherwise.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent
ROOT = EVALS_DIR.parent
SCRIPTS = ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS))
import _md_paths  # noqa: E402  (sys.path set just above)
import check_source_map as g  # noqa: E402  (sys.path set just above)

SUCCESS_MARKER = "source map guard selftest: PASS"
HEALTHY_MARKER = "Source map healthy"

# One allowlisted key from SYMBOL_ALLOWLIST, used to build the minimal tree.
WH_REL = Path(
    "vendor/Fast-DDS/src/cpp/rtps/history/WriterHistory.cpp"
)
WH_SYMBOL = "add_change"
MAP_REL = g.MAP_REL

HEALTHY_MAP = f"# minimal source map\n\n`{WH_REL.as_posix()}`\n"
STALE_MAP = f"# minimal source map\n\n`{WH_REL.as_posix()}:999`\n"
MISSING_MAP = "# minimal source map\n\n`vendor/not/there.cpp`\n"
EMPTY_MAP = "# minimal source map\n\nnothing of interest here, prose only\n"
GOOD_WH = "void add_change() {}\n"
BAD_WH = "int unrelated_symbol = 1;\n"


def _write(root: Path, rel: Path, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _build(
    root: Path,
    *,
    map_text: str | None = HEALTHY_MAP,
    wh_text: str = GOOD_WH,
    make_wh: bool = True,
) -> None:
    if map_text is not None:
        _write(root, MAP_REL, map_text)
    if make_wh:
        _write(root, WH_REL, wh_text)


def _check_negatives(failures: list[str]) -> int:
    caught = 0

    def expect(label: str, build_kwargs: dict, must: tuple[str, ...]) -> None:
        nonlocal caught
        with tempfile.TemporaryDirectory(prefix="source_map_neg_") as d:
            tmp = Path(d)
            _build(tmp, **build_kwargs)
            out, code = g.render(root=tmp)
        ok = code == 1 and HEALTHY_MARKER not in out
        ok = ok and all(s in out for s in must)
        if ok:
            caught += 1
        else:
            failures.append(
                f"negative '{label}': not caught as expected "
                f"(code={code}, need={must})"
            )

    # N1: map deleted entirely.
    expect(
        "map missing",
        {"map_text": None, "make_wh": False},
        ("FAIL: map missing",),
    )

    # N2: map present but prose-only, no extractable in-repo path.
    expect(
        "no paths extracted",
        {"map_text": EMPTY_MAP, "make_wh": False},
        ("FAIL: no in-repo paths extracted",),
    )

    # N3: map cites a vendor path that does not exist on disk.
    expect(
        "cited path missing",
        {"map_text": MISSING_MAP, "make_wh": False},
        ("FAIL missing",),
    )

    # N4: cited file exists but the allowlisted symbol has been removed.
    expect(
        "allowlisted symbol gone",
        {"map_text": HEALTHY_MAP, "wh_text": BAD_WH},
        ("FAIL symbol", WH_SYMBOL),
    )

    return caught


def _check_warn_only(failures: list[str]) -> int:
    """A stale cited line number warns but stays exit 0 while the symbol exists."""
    with tempfile.TemporaryDirectory(prefix="source_map_warn_") as d:
        tmp = Path(d)
        _build(tmp, map_text=STALE_MAP, wh_text=GOOD_WH)
        out, code = g.render(root=tmp)
    if code == 0 and "WARN stale line" in out and HEALTHY_MARKER in out:
        return 1
    failures.append(
        "warn-only: stale cited line with a present symbol must warn and "
        f"exit 0 (code={code}, warn={'WARN stale line' in out})"
    )
    return 0


def _check_healthy(failures: list[str]) -> int:
    healthy = 0

    # H1: the real repo renders green (regression guard for this self-test).
    out_real, code_real = g.render()
    if code_real == 0 and HEALTHY_MARKER in out_real:
        healthy += 1
    else:
        failures.append("healthy real repo: expected exit 0 + success marker")

    # H2: a minimal healthy temp tree renders green (proves the hand-built
    # fixture is valid, so the negative cases above do not fail for the wrong
    # reason).
    with tempfile.TemporaryDirectory(prefix="source_map_ok_") as d:
        tmp = Path(d)
        _build(tmp)
        out_copy, code_copy = g.render(root=tmp)
    if code_copy == 0 and HEALTHY_MARKER in out_copy:
        healthy += 1
    else:
        failures.append("healthy temp tree: expected exit 0 + success marker")

    return healthy


def _check_mutation(failures: list[str]) -> int:
    """A symbol lookup that always reports a hit must silence N4, then restore."""
    original = _md_paths.symbol_lines
    try:
        with tempfile.TemporaryDirectory(prefix="source_map_mut_") as d:
            tmp = Path(d)
            _build(tmp, map_text=HEALTHY_MAP, wh_text=BAD_WH)

            _md_paths.symbol_lines = lambda text, symbol: [1]
            out_wide, code_wide = g.render(root=tmp)

            _md_paths.symbol_lines = original
            out_restored, code_restored = g.render(root=tmp)
    finally:
        _md_paths.symbol_lines = original

    widened_silenced = (
        code_wide == 0
        and "FAIL symbol" not in out_wide
        and "ok symbol" in out_wide
    )
    restored_catches = (
        code_restored == 1 and "FAIL symbol" in out_restored
    )
    if widened_silenced and restored_catches:
        return 1
    failures.append(
        "mutation: always-hit symbol_lines did not silence N4 "
        f"(silenced={widened_silenced}) or restore did not re-catch it "
        f"(restored_catches={restored_catches})"
    )
    return 0


def main() -> int:
    failures: list[str] = []

    negative = _check_negatives(failures)
    warn_only = _check_warn_only(failures)
    healthy = _check_healthy(failures)
    mutation = _check_mutation(failures)

    print("# ros2-source-map honesty guard negative self-test")
    print(
        f"- negative scenarios caught: {negative}/4; "
        f"warn-only contract: {warn_only}/1; "
        f"healthy trees green: {healthy}/2; "
        f"mutation behaves: {mutation}/1"
    )

    if failures:
        print("\nFAIL:")
        for item in failures:
            print(f"- {item}")
        print(
            "\nThe source-map guard no longer behaves as specified. "
            f"Expected {SUCCESS_MARKER!r}. Exit 1."
        )
        return 1

    print(f"- **{SUCCESS_MARKER}** (4 negative, 1 warn-only, 2 healthy, 1 mutation)")
    print(
        "\nThe guard catches a deleted/empty map, a missing cited path, and a"
        " removed allowlisted symbol; stale line numbers still warn only;"
        " healthy trees stay green; and an always-hit symbol lookup"
        " demonstrably silences the symbol check. Read-only, tempdir-only."
        " Exit 0."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
