#!/usr/bin/env python3
"""`scripts/_md_paths.check_cited_paths` existence/symbol render contract (#39).

Context
-------
#38 (`md_paths_parser_selftest.py`) pins the *parsing* half of the shared
`scripts/_md_paths.py` helper (path recognition + citation extraction). This
test pins the other public function, `check_cited_paths`, which turns the
parsed ``{path: cited lines}`` map into the existence + allowlisted-symbol
verdict that both source-map guards render.

The two guard selftests only drive this function indirectly through the
guard's ``render()`` black box: #21 (source_map_guard) covers the four main
verdicts (missing path -> FAIL, allowlisted symbol gone -> FAIL, fully
disjoint stale line -> WARN-only, healthy -> exit 0) and one symbol_lines
mutation; #22 (executor_map_guard) pins the parse_map parameters. The
function's finer-grained contracts had no direct assertions:

- a cited **directory** counts as an on-disk path and *skips* symbol checks
  even when the allowlist names a symbol for it (no read of a dir, no FAIL);
- a file with no allowlist entry counts as a path but never checks symbols;
- the stale-line warning uses set ``isdisjoint``: a cited line set that
  *partially* intersects the real symbol lines is OK (only a fully disjoint
  non-empty cited set warns) -- a first-line comparison would false-positive;
- a symbol found on N>1 lines renders ``at L<first> (+N-1)``;
- the returned counters count files+dirs for paths (missing excluded) and
  count present symbols (gone excluded; a stale-but-present symbol still
  counts), and failures/warnings are mutated in place.

Eval-only, pure stdlib, files only inside a TemporaryDirectory; not a gate,
not in run_all_gates.GATES, not CI-enumerated.

Scenarios: 3 negative (missing path must FAIL and not count; gone allowlisted
symbol must FAIL and not count; a cited directory must never trigger a symbol
check/FAIL even if the allowlist names one), 2 non-flag (a fully-disjoint
stale line warns but stays non-failing and still counts the present symbol;
counter/render semantics for multi-hit ``(+N)``, cited-line rendering and
allowlist-less files), 1 healthy (the real source map: no failures, every
cited path on disk), 1 mutation (a partially-intersecting cited set must NOT
warn, pinning the set-isdisjoint semantics against a first-line regression).
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
import _md_paths as mp  # noqa: E402  (sys.path set just above)

SUCCESS_MARKER = "cited paths selftest: PASS"
SOURCE_MAP = Path("docs/architecture/ros2-source-map.md")


def main() -> int:
    failures: list[str] = []

    def check(label: str, cond: bool) -> None:
        if not cond:
            failures.append(label)
        print(f"  {'ok' if cond else 'FAIL'} {label}")

    with tempfile.TemporaryDirectory(prefix="cited_paths_selftest_") as d:
        root = Path(d).resolve()
        (root / "a_dir").mkdir()
        (root / "plain.py").write_text("x = 1\n", encoding="utf-8")
        (root / "hit.cpp").write_text("a\nfoo\nb\n", encoding="utf-8")        # foo L2
        (root / "stale.cpp").write_text("a\nb\nc\nd\nfoo\n", encoding="utf-8")  # foo L5
        (root / "gone.cpp").write_text("nothing here\n", encoding="utf-8")
        (root / "multi.py").write_text("foo\nb\nfoo\n", encoding="utf-8")     # foo L1,L3
        (root / "partial.cpp").write_text(
            "x\nfoo\nb\nc\nd\ne\nf\ng\nfoo\n", encoding="utf-8"
        )                                                                     # foo L2,L9

        # --- N1: missing path FAILs and is not counted as on-disk ---
        f1: list[str] = []
        cited1 = {Path("missing/x.cpp"): set(), Path("plain.py"): set()}
        _, op1, so1 = mp.check_cited_paths(root, cited1, {}, f1, [])
        check("missing path -> failure", any("missing path `missing/x.cpp`" in x for x in f1))
        check("missing path excluded from ok_paths", op1 == 1)
        check("missing path yields no symbol ok", so1 == 0)
        print("  ok negative missing path fails and is not counted")

        # --- N2: gone allowlisted symbol FAILs and is not counted ---
        f2: list[str] = []
        cited2 = {Path("gone.cpp"): set(), Path("hit.cpp"): {2}}
        allow2 = {"gone.cpp": ("bar",), "hit.cpp": ("foo",)}
        _, op2, so2 = mp.check_cited_paths(root, cited2, allow2, f2, [])
        check("gone symbol -> failure", any("symbol `bar` gone from `gone.cpp`" in x for x in f2))
        check("gone symbol excluded from symbol_ok", so2 == 1)  # only hit.cpp foo
        check("both present files count as paths", op2 == 2)
        print("  ok negative gone symbol fails and is not counted")

        # --- N3: a cited directory skips symbol checks even when allowlisted ---
        f3: list[str] = []
        cited3 = {Path("a_dir"): set()}
        allow3 = {"a_dir": ("whatever_symbol",)}
        lines3, op3, so3 = mp.check_cited_paths(root, cited3, allow3, f3, [])
        rendered3 = "\n".join(lines3)
        check("directory renders ok dir", "**ok dir:** `a_dir`" in rendered3)
        check("directory symbol not checked (no failure)", f3 == [])
        check("directory counts as path but not symbol", op3 == 1 and so3 == 0)
        print("  ok negative cited directory never triggers a symbol FAIL")

        # --- NF1: fully-disjoint stale line warns, stays non-failing, counts ---
        f4: list[str] = []
        w4: list[str] = []
        cited4 = {Path("stale.cpp"): {1}}
        allow4 = {"stale.cpp": ("foo",)}
        _, op4, so4 = mp.check_cited_paths(root, cited4, allow4, f4, w4)
        check("stale disjoint -> warning", any("stale.cpp" in x and "stale" in x for x in w4))
        check("stale disjoint -> no failure", f4 == [])
        check("present-but-stale symbol still counts", so4 == 1 and op4 == 1)
        print("  ok non-flag stale line warns but does not fail")

        # --- NF2: counters + multi-hit (+N) + cited-line + no-allowlist skip ---
        f5: list[str] = []
        cited5 = {
            Path("a_dir"): set(),
            Path("plain.py"): set(),
            Path("multi.py"): set(),
        }
        allow5 = {"multi.py": ("foo",)}
        lines5, op5, so5 = mp.check_cited_paths(root, cited5, allow5, f5, [])
        rendered5 = "\n".join(lines5)
        check("paths count file+dir (3)", op5 == 3)
        check("only allowlisted multi.py symbol counted", so5 == 1)
        check("allowlist-less plain.py has no symbol subline",
              "plain.py" in rendered5 and "ok symbol" not in
              "\n".join(l for l in lines5 if "plain.py" in l))
        check("multi-hit renders (+N)", "**ok symbol:** `foo` at L1 (+1)" in rendered5)
        cited_line_render, _, _ = mp.check_cited_paths(
            root, {Path("hit.cpp"): {2, 9}}, {"hit.cpp": ("foo",)}, [], []
        )
        check("cited lines render (cited L2, L9)",
              any("(cited L2, L9)" in l for l in cited_line_render))
        check("NF2 no failures", f5 == [])
        print("  ok non-flag counters, (+N) and cited-line rendering")

        # --- healthy: real source map, every cited path present, no failures ---
        real_map = REPO_ROOT / SOURCE_MAP
        real_cited, _ = mp.parse_map(REPO_ROOT, real_map)
        # Import the real guard's allowlist to exercise the genuine symbol set.
        sys.path.insert(0, str(SCRIPTS))
        import check_source_map as csm  # noqa: E402
        fh: list[str] = []
        wh: list[str] = []
        _, op_h, so_h = mp.check_cited_paths(
            REPO_ROOT, real_cited, csm.SYMBOL_ALLOWLIST, fh, wh
        )
        check("real source map has cited paths", len(real_cited) > 0)
        check("real source map has no failures", fh == [])
        check("every real cited path is on disk", op_h == len(real_cited))
        check("real allowlist yields symbol hits", so_h >= 1)
        print("  ok healthy real source map paths/symbols verify")

        # --- mutation: partial intersect must NOT warn (set-isdisjoint semantics) ---
        wm: list[str] = []
        fm: list[str] = []
        cited_m = {Path("partial.cpp"): {1, 2}}   # L2 intersects real hits {2,9}
        allow_m = {"partial.cpp": ("foo",)}
        _, _, so_m = mp.check_cited_paths(root, cited_m, allow_m, fm, wm)
        check("partial intersect -> no stale warning",
              not any("partial.cpp" in x for x in wm))
        check("partial intersect -> symbol ok", so_m == 1 and fm == [])
        print("  ok mutation partial-intersect cited set is not a stale warning")

    if failures:
        print(SUCCESS_MARKER.replace("PASS", "FAIL") + f": {failures}")
        return 1
    print(SUCCESS_MARKER)
    print("3 negative, 2 non-flag, 1 healthy, 1 mutation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
