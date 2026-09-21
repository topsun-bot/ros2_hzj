#!/usr/bin/env python3
"""Shared markdown source-map parser (`scripts/_md_paths.py`) contract selftest (#38).

Context
-------
`scripts/_md_paths.py` is the shared parser extracted verbatim from
check_source_map.py / check_executor_map.py (modernization plan Step 3):
path recognition (``looks_like_repo_path``), citation normalization
(``to_repo_rel``), markdown citation extraction (``parse_map``) and identifier
lookup (``ident_re`` / ``symbol_lines``). The two guard selftests only cover
slices of it indirectly: #22 (executor_map_guard) pins the two ``parse_map``
caller parameters (``absent_keys`` / ``reject_bare_words``) and #21
(source_map_guard) monkeypatches ``symbol_lines`` for one mutation. The
parser's own fine-grained contracts -- repository-root escape (depth
sensitive), fragment/``<>``/space stripping, non-path rejection, identifier
word-boundary + cache, 1-based symbol lines, and parse_map's line-number /
unique-suffix / ambiguous / fenced-code handling -- had no direct assertions.

This eval-only test imports the REAL ``scripts/_md_paths.py`` and pins those
contracts directly on minimal temp trees (it never writes in the repo, and is
not a gate / not in run_all_gates.GATES / not CI-enumerated). The two caller
parameters already pinned by #22 are only lightly re-touched here, not
duplicated.

Scenarios: 3 negative (a citation that resolves outside the repo root, or an
external/absolute target, must yield None; non-path tokens (ellipsis / URL /
absolute / prefix-less) must be rejected; an ambiguous filename:line cite
matching >1 cited paths must emit an ambiguous note and not be silently
attributed), 2 non-flag (fragment / angle / space stripping and a legal-depth
relative path plus the bare-word switch; identifier word boundary, regex cache
identity and 1-based symbol lines), 1 healthy (the real source map parses with
cited paths, no ambiguous notes, and at least one cited target on disk),
1 mutation (a link inside a fenced code block must be excluded while an
identical link outside the fence is still cited).
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
import _md_paths as mp  # noqa: E402  (sys.path set just above)

SUCCESS_MARKER = "md paths parser selftest: PASS"
SOURCE_MAP = Path("docs/architecture/ros2-source-map.md")


def main() -> int:
    failures: list[str] = []

    def check(label: str, cond: bool) -> None:
        if not cond:
            failures.append(label)
        print(f"  {'ok' if cond else 'FAIL'} {label}")

    with tempfile.TemporaryDirectory(prefix="md_paths_selftest_") as d:
        root = Path(d).resolve()
        arch = root / "docs" / "architecture"
        arch.mkdir(parents=True, exist_ok=True)
        map_path = arch / "map.md"

        # --- N1: root escape and external/absolute targets yield None ---
        check("escape ../../../etc/passwd -> None",
              mp.to_repo_rel(root, map_path, "../../../etc/passwd") is None)
        check("escape ../../../outside/x.md -> None",
              mp.to_repo_rel(root, map_path, "../../../outside/x.md") is None)
        check("external https -> None",
              mp.to_repo_rel(root, map_path, "https://e.com/a.md") is None)
        check("absolute /etc/passwd -> None",
              mp.to_repo_rel(root, map_path, "/etc/passwd") is None)
        print("  ok negative root-escape and external/absolute rejected")

        # --- N2: non-path tokens rejected ---
        check("looks_like ellipsis '...'", not mp.looks_like_repo_path("..."))
        check("looks_like embedded ellipsis", not mp.looks_like_repo_path("docs/.../x.md"))
        check("looks_like url", not mp.looks_like_repo_path("https://e.com/a.md"))
        check("looks_like absolute", not mp.looks_like_repo_path("/etc/passwd"))
        check("looks_like prefix-less foo/bar.py", not mp.looks_like_repo_path("foo/bar.py"))
        check("looks_like accepts scripts/", mp.looks_like_repo_path("scripts/x.py"))
        check("looks_like accepts ./docs/", mp.looks_like_repo_path("./docs/a.md"))
        check("to_repo_rel embedded ellipsis -> None",
              mp.to_repo_rel(root, map_path, "docs/.../x.md") is None)
        print("  ok negative non-path tokens rejected")

        # --- N3: ambiguous filename:line cite -> note, not attributed ---
        (root / "scripts").mkdir(exist_ok=True)
        (root / "docs").mkdir(exist_ok=True)
        amb = arch / "amb.md"
        amb.write_text(
            "# amb\n"
            "`scripts/WriterHistory.cpp:1`\n"
            "`docs/WriterHistory.cpp:2`\n"
            "see WriterHistory.cpp:9\n",
            encoding="utf-8",
        )
        cited_amb, notes = mp.parse_map(root, amb)
        same = [p for p in cited_amb if p.name == "WriterHistory.cpp"]
        check("ambiguous yields note",
              any("ambiguous line cite WriterHistory.cpp:9" in n for n in notes))
        check("ambiguous keeps the two cited paths", len(same) == 2)
        check("ambiguous line 9 not attributed",
              all(9 not in cited_amb[p] for p in same))
        print("  ok negative ambiguous cite reported, not silently attributed")

        # --- NF1: stripping, legal-depth relative, bare-word switch ---
        check("fragment stripped",
              mp.to_repo_rel(root, map_path, "docs/x.md#sec") == Path("docs/x.md"))
        check("angle brackets stripped",
              mp.to_repo_rel(root, map_path, "<docs/x.md>") == Path("docs/x.md"))
        check("space suffix truncated",
              mp.to_repo_rel(root, map_path, "docs/x.md extra") == Path("docs/x.md"))
        check("legal-depth ../../etc/passwd stays in root",
              mp.to_repo_rel(root, map_path, "../../etc/passwd") == Path("etc/passwd"))
        check("bare word rejected when reject_bare_words=True",
              mp.to_repo_rel(root, map_path, "dimos_bridge", True) is None)
        check("bare word resolves sibling when flag False",
              mp.to_repo_rel(root, map_path, "dimos_bridge", False)
              == Path("docs/architecture/dimos_bridge"))
        print("  ok non-flag stripping / legal depth / bare-word switch")

        # --- NF2: identifier word boundary, cache identity, 1-based lines ---
        pat = mp.ident_re("foo")
        check("ident no substring match (foobar)", not pat.search("foobar"))
        check("ident matches at dash boundary (x-foo-y)", bool(pat.search("x-foo-y")))
        check("ident regex cached (same object)", mp.ident_re("foo") is pat)
        check("symbol_lines 1-based", mp.symbol_lines("a\nfoo\nb", "foo") == [2])
        print("  ok non-flag identifier boundary/cache and 1-based lines")

        # --- healthy: real source map parses cleanly ---
        real_map = REPO_ROOT / SOURCE_MAP
        real_cited, real_notes = mp.parse_map(REPO_ROOT, real_map)
        check("real source map has cited paths", len(real_cited) > 0)
        check("real source map has no ambiguous note",
              not any("ambiguous" in n for n in real_notes))
        check("real source map cites at least one on-disk target",
              any((REPO_ROOT / p).exists() for p in real_cited))
        print("  ok healthy real source map parses with on-disk targets")

        # --- mutation: fenced-code links excluded, outside-fence kept ---
        fenced = arch / "fenced.md"
        fenced.write_text(
            "# fenced\n"
            "```\n[z](scripts/fenced.cpp)\n```\n"
            "[o](scripts/open.cpp)\n",
            encoding="utf-8",
        )
        cited_f, _ = mp.parse_map(root, fenced)
        check("fenced-code link excluded", Path("scripts/fenced.cpp") not in cited_f)
        check("outside-fence link cited", Path("scripts/open.cpp") in cited_f)
        print("  ok mutation fenced links excluded while live links cited")

    if failures:
        print(SUCCESS_MARKER.replace("PASS", "FAIL") + f": {failures}")
        return 1
    print(SUCCESS_MARKER)
    print("3 negative, 2 non-flag, 1 healthy, 1 mutation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
