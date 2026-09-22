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
  so until now nothing proved these document checks fail closed. Of the
  baseline marker tuple, its three core safety words -- ``Hold``,
  ``STATUS: blocked`` (blocked honesty), ``只读`` (the fastdds.xml read-only
  contract) -- now have removal negatives N7/N8/N9 too, since N1 only covers
  the paused phrase and N2/N5/N6 only add percentile tokens. The Unitree swap
  record keeps N4 for the whole file missing and adds N10/N11/N12 for a
  present-but-stripped swap doc (drop-in FAIL / bundled 0.10.2 / vendor
  11.0.1). N13 covers the R0 freeze doc losing Hold while present, and
  N14/N15 cover the source map losing vendor / 不是复现 while present.
  N16/N17/N18 cover the ADR losing FastDDS + Cyclone / SCOREBOARD / the
  baseline back-pointer while present.
  N19/N20 cover the baseline losing Not Feishu field proof / 派生自 while
  present. The map /
  rewrite / pointer phrase checks reuse strings already in the marker tuple
  and so are always accompanied by a FAIL markers line (they cannot fire
  independently like the paused phrase); they get no separate negative.

The harness copies the eleven files the guard actually reads (the nine
``required`` entries plus ``config/env/load.py`` and the thin wrapper) from the
real repo into a temp tree, preserving relative paths, so the env cross-check
face stays green on the pristine copy and only the mutated document drives the
result. It then runs twenty negative scenarios, three non-flag (existence-only /
policy-word) scenarios, two healthy scenarios, and one memory-only mutation. Standard
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

    # N5: a bare p99 placed directly next to a CJK character (no ASCII
    # whitespace boundary) must still trip the regex -- the ASCII character
    # class lookaround is deliberately designed so a phrase like 链A的p99
    # cannot slip past the booked-percentile ban.
    with tempfile.TemporaryDirectory() as td:
        _seed_tree(Path(td), edits={
            g.BASELINE_REL: lambda t: t + "\n链A的p99约1.2ms，仅占位。\n",
        })
        out, code = _render(Path(td))
        check(code == 1, "N5 CJK-adjacent p99 must exit 1")
        check("- **FAIL percentiles:**" in out,
              "N5 ASCII lookaround must catch p99 next to a CJK character")
        check("- **FAIL paused:**" not in out and "- **FAIL markers:**" not in out,
              "N5 must trip only the percentile check")

    # N6: a different booked quantile (p95, not p99) must trip the same regex,
    # proving the character class covers p50/p90/p95/p99 rather than p99 alone.
    with tempfile.TemporaryDirectory() as td:
        _seed_tree(Path(td), edits={
            g.BASELINE_REL: lambda t: t + "\nmeasured p95 = 0.4 ms\n",
        })
        out, code = _render(Path(td))
        check(code == 1, "N6 bare p95 must exit 1")
        check("- **FAIL percentiles:**" in out,
              "N6 the regex must cover p95, not only p99")
        check("- **FAIL paused:**" not in out and "- **FAIL markers:**" not in out,
              "N6 must trip only the percentile check")

    # N7/N8/N9: three core safety markers ride the baseline marker tuple but
    # had no removal negative -- the Hold boundary (Hold, 6 occurrences), the
    # blocked-status honesty phrase (STATUS: blocked, 7), and the fastdds.xml
    # read-only contract (只读, 5). N1 only covers the paused phrase (which is
    # NOT in the tuple) and N2/N5/N6 only add percentile tokens; nothing
    # removed a core tuple marker, so a future edit that dropped one of these
    # words would weaken the baseline document face while the existing
    # negatives stayed green. Keeping the file present but stripping the word
    # must fail markers and name it, trip no other check, and not collaterally
    # fail a sibling file. Probed on the real guard in a temp tree.
    for label, word in (
        ("N7 baseline drops Hold marker", "Hold"),
        ("N8 baseline drops STATUS: blocked marker", "STATUS: blocked"),
        ("N9 baseline drops read-only marker", "只读"),
    ):
        with tempfile.TemporaryDirectory() as td:
            _seed_tree(Path(td), edits={
                g.BASELINE_REL: (lambda t, w=word: t.replace(w, "")),
            })
            out, code = _render(Path(td))
        check(code == 1, f"{label} must exit 1")
        check("- **FAIL markers:**" in out
              and "feishu-dual-chain-baseline.md" in out
              and f"need {word}" in out,
              f"{label} must report the baseline missing {word}")
        check("- **FAIL paused:**" not in out
              and "- **FAIL percentiles:**" not in out
              and "- **FAIL map:**" not in out
              and "- **FAIL rewrite:**" not in out
              and "- **FAIL pointer:**" not in out,
              f"{label} must trip only the marker scan")
        check("feishu-middleware-adr.md" in out,
              f"{label} must not collaterally fail a sibling file")

    # N10/N11/N12: the Unitree swap doc stays present but loses one of its
    # three content markers -- drop-in FAIL (the drop-in failure verdict,
    # 3 occurrences), bundled 0.10.2 (23), or vendor 11.0.1 (24). N4 only
    # covered the whole swap file vanishing (FAIL missing); it did not cover
    # a present-but-weakened swap record, so an edit that kept the file shell
    # while deleting a version/verdict marker would weaken the Unitree
    # 0.10.2-vs-11.0.1 evidence while the existing negatives stayed green.
    # Stripping one word must fail markers and name it against the swap file
    # only, trip no other check, and leave the baseline doc healthy. Probed
    # on the real guard in a temp tree.
    for label, word in (
        ("N10 swap doc drops drop-in FAIL verdict", "drop-in FAIL"),
        ("N11 swap doc drops bundled 0.10.2", "0.10.2"),
        ("N12 swap doc drops vendor 11.0.1", "11.0.1"),
    ):
        with tempfile.TemporaryDirectory() as td:
            _seed_tree(Path(td), edits={
                g.SWAP_REL: (lambda t, w=word: t.replace(w, "")),
            })
            out, code = _render(Path(td))
        check(code == 1, f"{label} must exit 1")
        check("- **FAIL markers:**" in out
              and "unitree-sdk2-dds-swap.md" in out
              and f"need {word}" in out,
              f"{label} must report the swap doc missing {word}")
        check("feishu-dual-chain-baseline.md` (need" not in out,
              f"{label} must not flag the healthy baseline doc")
        check("- **FAIL paused:**" not in out
              and "- **FAIL percentiles:**" not in out
              and "- **FAIL missing:**" not in out,
              f"{label} must trip only the marker scan")

    # N13/N14/N15: the R0 freeze record and the source map stay present but
    # lose a content marker. The R0 freeze doc carries Hold (3 occurrences);
    # the source map carries vendor (72) and the not-a-reproduction verdict
    # 不是复现 (1). N1 covered only the paused phrase, N4 only the swap file
    # missing, and N7-N12 only baseline/swap markers -- there was no
    # present-but-weakened negative for R0 or the map, so keeping either
    # file shell while deleting its Hold / vendor / not-a-reproduction
    # marker would weaken the freeze or source-map evidence while the
    # existing negatives stayed green. Stripping one word must fail markers
    # and name it against that file only, trip no other check, and leave the
    # baseline doc healthy. Probed on the real guard in a temp tree.
    for label, rel, fname, word in (
        ("N13 R0 freeze doc drops Hold", g.R0_REL,
         "ros2-dds-r0-interface-freeze.md", "Hold"),
        ("N14 source map drops vendor", g.MAP_REL,
         "ros2-source-map.md", "vendor"),
        ("N15 source map drops not-a-reproduction verdict", g.MAP_REL,
         "ros2-source-map.md", "不是复现"),
    ):
        with tempfile.TemporaryDirectory() as td:
            _seed_tree(Path(td), edits={
                rel: (lambda t, w=word: t.replace(w, "")),
            })
            out, code = _render(Path(td))
        check(code == 1, f"{label} must exit 1")
        check("- **FAIL markers:**" in out
              and fname in out
              and f"need {word}" in out,
              f"{label} must report the file missing {word}")
        check("feishu-dual-chain-baseline.md` (need" not in out,
              f"{label} must not flag the healthy baseline doc")
        check("- **FAIL paused:**" not in out
              and "- **FAIL percentiles:**" not in out
              and "- **FAIL missing:**" not in out
              and "- **FAIL map:**" not in out,
              f"{label} must trip only the marker scan")

    # N16/N17/N18: the middleware ADR stays present but loses one of its
    # remaining content markers -- FastDDS + Cyclone (the dual-chain scope,
    # 2 occurrences), SCOREBOARD (4), or the back-pointer to the baseline
    # doc feishu-dual-chain-baseline.md (6). N3 covered the ADR losing 不重写
    # XML only; it did not cover the ADR losing its dual-chain scope, its
    # SCOREBOARD pointer, or its baseline back-pointer while present, so
    # keeping the ADR shell while deleting one would weaken the ADR record
    # while the existing negatives stayed green. Stripping one word must
    # fail markers and name it against the ADR only, trip no other check,
    # and leave the baseline doc healthy. Probed on the real guard in a
    # temp tree.
    for label, word in (
        ("N16 ADR drops FastDDS + Cyclone scope", "FastDDS + Cyclone"),
        ("N17 ADR drops SCOREBOARD pointer", "SCOREBOARD"),
        ("N18 ADR drops baseline back-pointer", "feishu-dual-chain-baseline.md"),
    ):
        with tempfile.TemporaryDirectory() as td:
            _seed_tree(Path(td), edits={
                g.ADR_REL: (lambda t, w=word: t.replace(w, "")),
            })
            out, code = _render(Path(td))
        check(code == 1, f"{label} must exit 1")
        check("- **FAIL markers:**" in out
              and "feishu-middleware-adr.md" in out
              and f"need {word}" in out,
              f"{label} must report the ADR missing {word}")
        check("feishu-dual-chain-baseline.md` (need" not in out,
              f"{label} must not flag the healthy baseline doc")
        check("- **FAIL paused:**" not in out
              and "- **FAIL percentiles:**" not in out
              and "- **FAIL missing:**" not in out
              and "- **FAIL rewrite:**" not in out,
              f"{label} must trip only the marker scan")

    # N19/N20: the baseline doc stays present but loses one of its honesty
    # markers -- Not Feishu field proof (the explicit caveat that the
    # baseline is not a Feishu field proof, 1 occurrence) or 派生自 (the
    # derivation wording, 3 occurrences). N7-N9 covered the baseline losing
    # Hold / STATUS: blocked / 只读 only; they did not cover the baseline
    # losing its field-proof caveat or its derivation wording while present,
    # so keeping the baseline shell while deleting one would weaken the
    # honesty record while the existing negatives stayed green. Stripping
    # one word must fail markers and name it against the baseline only,
    # trip no other check, and leave the ADR healthy. Probed on the real
    # guard in a temp tree.
    for label, word in (
        ("N19 baseline drops Not Feishu field proof caveat", "Not Feishu field proof"),
        ("N20 baseline drops derivation wording", "派生自"),
    ):
        with tempfile.TemporaryDirectory() as td:
            _seed_tree(Path(td), edits={
                g.BASELINE_REL: (lambda t, w=word: t.replace(w, "")),
            })
            out, code = _render(Path(td))
        check(code == 1, f"{label} must exit 1")
        check("- **FAIL markers:**" in out
              and "feishu-dual-chain-baseline.md" in out
              and f"need {word}" in out,
              f"{label} must report the baseline missing {word}")
        check("feishu-middleware-adr.md` (need" not in out,
              f"{label} must not flag the healthy ADR")
        check("- **FAIL paused:**" not in out
              and "- **FAIL percentiles:**" not in out
              and "- **FAIL missing:**" not in out
              and "- **FAIL map:**" not in out
              and "- **FAIL rewrite:**" not in out,
              f"{label} must trip only the marker scan")

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

    # NF3: the policy word for quantiles (分位数) with no bare pNN digit token
    # must stay green. The ban targets fabricated p50/p90/p95/p99 numbers, not
    # the Chinese policy term; this pins the two-way contract so tightening the
    # regex to forbid 分位数 would be caught.
    with tempfile.TemporaryDirectory() as td:
        _seed_tree(Path(td), edits={
            g.BASELINE_REL: lambda t: t
            + "\n预订链路分位数待 Humble 主机实测后回填，本文不写预订数字。\n",
        })
        out, code = _render(Path(td))
        check(code == 0, "NF3 policy word 分位数 without pNN must stay exit 0")
        check("- **FAIL percentiles:**" not in out and not _has_fail_line(out),
              "NF3 the policy word 分位数 must not trip the percentile ban")

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
    print("20 negative, 3 non-flag, 2 healthy, 1 mutation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
