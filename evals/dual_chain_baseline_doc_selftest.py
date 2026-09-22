#!/usr/bin/env python3
"""Negative self-test for the dual-chain baseline *document/pointer* face.

eval-only. Invoked by the Promptfoo local-script provider. Like the other
``evals/*_selftest.py`` scripts it is NOT one of the 13 CI gates, is not
enumerated by ``scripts/run_all_gates.py``, and needs no ci.yml wiring (so it
is not blocked by the GitHub ``workflow`` token scope).

Why this exists
---------------
``scripts/check_dual_chain_baseline.py`` (wiki3 §13(3)) has two faces:

* the **env / shell / wrapper cross-check face** (load.py single source of
  truth vs literal chain_a.sh / chain_b.sh exports vs the thin wrapper, plus
  the chain_b.sh ``unset CYCLONEDDS_URI`` contract). That face already has a
  dedicated negative self-test: ``dual_chain_env_guard_selftest.py`` (#19),
  which deliberately builds a tree *without* the doc files and asserts only
  the five ``FAIL env|chain A|chain B`` line families.

* the **document / pointer face** this script owns: the nine required files
  and their per-file markers, the four contiguous baseline-doc phrases that
  are checked independently of the marker tuple (paused / map verdict /
  no-XML-rewrite / pointer-only), the **booked-percentile anti-fabrication
  regex** that forbids invented p50/p90/p95/p99 tokens, and the contract that
  fastdds.xml / SCOREBOARD are existence-only here (their content freeze is
  the ``boundary`` job, not this gate). #19 explicitly ignores doc failures,
  so until now nothing proved these document checks fail closed.

The harness copies the eleven files the guard actually reads (the nine
``required`` entries plus ``config/env/load.py`` and the thin wrapper) from the
real repo into a temp tree, preserving relative paths, so the env cross-check
face stays green on the pristine copy and only the mutated document drives the
result. It then runs four negative scenarios, two non-flag (existence-only)
scenarios, two healthy scenarios, and one memory-only mutation. Standard
library only; files are created only inside a tempfile and the repo is never
edited. Exit 0 when every expectation holds, exit 1 (with details) otherwise.
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent
ROOT = EVALS_DIR.parent
SCRIPTS = ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS))
import check_dual_chain_baseline as g  # noqa: E402  (sys.path set just above)

SUCCESS_MARKER = "dual-chain baseline doc guard selftest: PASS"

# Every file the guard opens / imports, copied verbatim into the temp tree so
# the env cross-check face is healthy and a document mutation is the only
# variable. XML / SCOREBOARD are existence-only to the guard.
_COPY_RELS = (
    g.BASELINE_REL,
    g.ADR_REL,
    g.CHAIN_A_REL,
    g.CHAIN_B_REL,
    g.R0_REL,
    g.MAP_REL,
    g.SWAP_REL,
    g.XML_REL,
    g.SCOREBOARD_REL,
    g.LOAD_PY_REL,
    g.WRAPPER_REL,
)


def _seed_tree(root: Path, *, edits: dict[Path, "object"] | None = None,
               drop: set[Path] | None = None) -> None:
    """Copy the real files the guard reads into ``root``.

    ``edits`` maps a repo-relative path to a str -> str transform applied to
    the copied text; ``drop`` lists paths that must not exist in the tree.
    """
    edits = edits or {}
    drop = drop or set()
    for rel in _COPY_RELS:
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if rel in drop:
            dst.unlink(missing_ok=True)
            continue
        text = (ROOT / rel).read_text(encoding="utf-8")
        if rel in edits:
            text = edits[rel](text)
        dst.write_text(text, encoding="utf-8")


def _render(root: Path) -> tuple[str, int]:
    return g.render(root=root)


def _has_fail_line(out: str) -> bool:
    """A real rendered failure line, not the fixed 'drop-in FAIL' prose."""
    return any(line.startswith("- **FAIL") for line in out.splitlines())


def main() -> int:
    failures: list[str] = []

    def check(cond: bool, msg: str) -> None:
        if not cond:
            failures.append(msg)

    # ---- healthy -------------------------------------------------------
    # H1: the real repo tree renders exit 0 with both success markers and no
    # rendered failure line.
    real_out, real_code = g.render()
    check(real_code == 0, "H1 real repo must render exit 0")
    check(g.SUCCESS_MARKER in real_out, "H1 missing pointer-only success marker")
    check(g.PAUSED_MARKER in real_out, "H1 missing paused success marker")
    check(not _has_fail_line(real_out), "H1 real repo unexpectedly has a FAIL line")

    # H2: a pristine verbatim copy of every read file is healthy too, proving
    # the fixture is valid (negatives are not failing for an unrelated reason).
    with tempfile.TemporaryDirectory() as td:
        _seed_tree(Path(td))
        out, code = _render(Path(td))
        check(code == 0, "H2 pristine copied tree must render exit 0")
        check(g.SUCCESS_MARKER in out and g.PAUSED_MARKER in out,
              "H2 copied tree missing success markers")
        check(not _has_fail_line(out), "H2 pristine copy unexpectedly has a FAIL line")

    # ---- negative ------------------------------------------------------
    # N1: dropping the contiguous paused phrase (which is NOT part of the
    # _BASELINE_MARKERS tuple) must fail via the dedicated paused check only,
    # proving it is enforced independently of the marker-set scan.
    with tempfile.TemporaryDirectory() as td:
        _seed_tree(Path(td), edits={
            g.BASELINE_REL: lambda t: t.replace(g.PAUSED_MARKER, ""),
        })
        out, code = _render(Path(td))
        check(code == 1, "N1 missing paused phrase must exit 1")
        check("- **FAIL paused:**" in out, "N1 must report FAIL paused")
        check("- **FAIL markers:**" not in out,
              "N1 paused phrase is independent and must not also trip marker scan")
        check("- **FAIL percentiles:**" not in out, "N1 must not trip percentile check")

    # N2: inventing a booked percentile token (p99) must trip the anti-
    # fabrication regex and nothing else.
    with tempfile.TemporaryDirectory() as td:
        _seed_tree(Path(td), edits={
            g.BASELINE_REL: lambda t: t + "\nmeasured p99 = 1.2 ms on the link\n",
        })
        out, code = _render(Path(td))
        check(code == 1, "N2 invented p99 must exit 1")
        check("- **FAIL percentiles:**" in out, "N2 must report FAIL percentiles")
        check("- **FAIL paused:**" not in out, "N2 must not trip paused check")
        check("- **FAIL markers:**" not in out, "N2 must not trip marker scan")

    # N3: dropping an ADR §13(3) marker must fail markers against the ADR file
    # only (the baseline doc stays healthy), proving per-file marker
    # enforcement on the second document.
    with tempfile.TemporaryDirectory() as td:
        _seed_tree(Path(td), edits={
            g.ADR_REL: lambda t: t.replace("不重写 XML", ""),
        })
        out, code = _render(Path(td))
        check(code == 1, "N3 ADR missing marker must exit 1")
        check("- **FAIL markers:**" in out
              and "feishu-middleware-adr.md" in out
              and "不重写 XML" in out,
              "N3 must report the ADR missing 不重写 XML")
        check("feishu-dual-chain-baseline.md` (need" not in out,
              "N3 must not flag the healthy baseline doc")

    # N4: deleting a required doc (the Unitree swap record) must render a
    # missing-file failure.
    with tempfile.TemporaryDirectory() as td:
        _seed_tree(Path(td), drop={g.SWAP_REL})
        out, code = _render(Path(td))
        check(code == 1, "N4 missing swap doc must exit 1")
        check("- **FAIL missing:**" in out
              and "unitree-sdk2-dds-swap.md" in out,
              "N4 must report the swap doc missing")

    # ---- non-flag (existence-only boundary) ---------------------------
    # NF1: an empty SCOREBOARD must stay green here -- this gate never reads
    # SCOREBOARD contents (the boundary job owns the number freeze).
    with tempfile.TemporaryDirectory() as td:
        _seed_tree(Path(td), edits={g.SCOREBOARD_REL: lambda t: ""})
        out, code = _render(Path(td))
        check(code == 0, "NF1 empty SCOREBOARD must stay exit 0 (existence-only)")
        check(not _has_fail_line(out), "NF1 existence-only SCOREBOARD must not FAIL")

    # NF2: arbitrary fastdds.xml content (even a bogus domainId) must stay
    # green -- the XML content freeze is likewise owned by boundary, not here.
    with tempfile.TemporaryDirectory() as td:
        _seed_tree(Path(td), edits={
            g.XML_REL: lambda t: "<profiles><domainId>99</domainId></profiles>\n",
        })
        out, code = _render(Path(td))
        check(code == 0, "NF2 arbitrary XML must stay exit 0 (existence-only)")
        check(not _has_fail_line(out), "NF2 existence-only XML must not FAIL")

    # ---- mutation ------------------------------------------------------
    # A percentile detector that never matches must let N2's invented p99 go
    # unreported (exit 0); restoring the real regex must re-catch it. This
    # proves the anti-fabrication branch is live and the blind stub is
    # distinguishable.
    orig_re = g._PERCENTILE_RE
    blind = re.compile(r"$^")  # never matches
    try:
        with tempfile.TemporaryDirectory() as td:
            _seed_tree(Path(td), edits={
                g.BASELINE_REL: lambda t: t + "\nmeasured p99 = 1.2 ms\n",
            })
            g._PERCENTILE_RE = blind
            blind_out, blind_code = _render(Path(td))
            check(blind_code == 0 and "- **FAIL percentiles:**" not in blind_out,
                  "mutation: blind percentile regex must hide the invented p99")
        with tempfile.TemporaryDirectory() as td:
            _seed_tree(Path(td), edits={
                g.BASELINE_REL: lambda t: t + "\nmeasured p99 = 1.2 ms\n",
            })
            g._PERCENTILE_RE = orig_re
            restored_out, restored_code = _render(Path(td))
            check(restored_code == 1 and "- **FAIL percentiles:**" in restored_out,
                  "mutation: restoring the regex must re-catch the invented p99")
    finally:
        g._PERCENTILE_RE = orig_re

    if failures:
        print("dual-chain baseline doc guard selftest: FAIL")
        for item in failures:
            print(f"- {item}")
        return 1

    print(SUCCESS_MARKER)
    print("4 negative, 2 non-flag, 2 healthy, 1 mutation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
