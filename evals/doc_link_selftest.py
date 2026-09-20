#!/usr/bin/env python3
"""Markdown relative-link integrity self-test for refactor/eval docs (#36).

Context
-------
The CI ``contracts`` job only does an explicit ``test -f`` enumeration of a
fixed allowlist; it does not *parse* markdown links, and it does not cover
``docs/refactor/**`` or ``evals/**``. The ``_md_paths.parse_map`` helper used by
``check_source_map.py`` / ``check_executor_map.py`` parses citations, but only
for two specific architecture maps and it also treats backtick ``path`` tokens
as citations (with an allowlist), which is a different job from plain markdown
link integrity.

So the docs this refactor loop produces every round -- ``docs/refactor/*.md``
(01 walk-through, 02 plan, ITERATION_LOG) and the ``evals/`` docs (README,
results/BASELINE) -- had ~165 relative markdown links with **zero machine
checks** that their targets still exist. Renaming/moving a file without
updating a relative link would silently rot the docs.

This eval-only test scans those markdown files, strips fenced and inline code
(so regex snippets / command samples containing ``](...)`` are not mistaken
for links), and resolves every inline ``[text](target)`` / image link:

  * external / anchor / mailto / web-root links are skipped (not local);
  * a relative target is resolved against the linking file's directory and
    must stay inside the repo root (no ``../../`` escape) AND exist on disk
    (file or directory, trailing slash allowed).

It reads the REAL repo for the healthy case; all negatives inject links in
memory (no temp files, no repo edits).

Scenarios: 3 negative (missing sibling file, ``../`` escape outside the repo,
missing linked directory), 2 non-flag (external/anchor/mailto links skipped;
pseudo-links inside fenced/inline code skipped), 1 healthy (real repo: zero
broken, with a link/file floor so a vacuous empty scan cannot pass),
1 mutation (force one real target to "missing" via an exists wrapper; it must
be reported, proving the check is not vacuous).
"""

from __future__ import annotations

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCAN_GLOBS = ("docs/refactor/**/*.md", "evals/**/*.md")

SUCCESS_MARKER = "doc link selftest: PASS"

_FENCE_RE = re.compile(r"```.*?```", re.S)
_INLINE_CODE_RE = re.compile(r"`+[^`\n]+?`+")
_LINK_RE = re.compile(r"!?\[[^\]]*\]\(\s*([^)\s]+)")
_EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "#", "<")


def strip_code(text: str) -> str:
    """Remove fenced blocks then inline code so pseudo-links there are ignored."""
    return _INLINE_CODE_RE.sub("", _FENCE_RE.sub("", text))


def _is_external(target: str) -> bool:
    return target.startswith(_EXTERNAL_PREFIXES)


def find_broken(entries, root: pathlib.Path, exists=pathlib.Path.exists):
    """Return [(md_rel, target, reason), ...] for broken relative links.

    `entries` is an iterable of (relpath-posix, markdown-text). `exists` takes
    a resolved absolute Path and reports existence (injectable for mutation).
    """
    root = root.resolve()
    broken = []
    for rel, text in entries:
        md_path = root / rel
        body = strip_code(text)
        for m in _LINK_RE.finditer(body):
            target = m.group(1).strip()
            if _is_external(target):
                continue
            path = target.split("#", 1)[0].split("?", 1)[0]
            if not path or path.startswith("/"):
                continue  # pure anchor, or web-root-absolute (not a repo rel link)
            dest = (md_path.parent / path).resolve()
            try:
                dest.relative_to(root)
            except ValueError:
                broken.append((rel, target, "escapes repo root"))
                continue
            if not exists(dest):
                broken.append((rel, target, "missing target"))
    return broken


def _real_entries():
    entries = []
    for pattern in SCAN_GLOBS:
        for p in sorted(REPO_ROOT.glob(pattern)):
            if p.is_file():
                entries.append((p.relative_to(REPO_ROOT).as_posix(), p.read_text(encoding="utf-8")))
    return entries


def _count_relative_links(entries) -> int:
    n = 0
    for _rel, text in entries:
        for m in _LINK_RE.finditer(strip_code(text)):
            t = m.group(1).strip()
            if _is_external(t):
                continue
            if t.split("#", 1)[0].split("?", 1)[0] and not t.startswith("/"):
                n += 1
    return n


def main() -> int:
    try:
        entries = _real_entries()

        # healthy: real repo has zero broken links, with a non-vacuous floor
        broken = find_broken(entries, REPO_ROOT)
        assert broken == [], "real repo should have no broken links: " + repr(broken[:5])
        n_links = _count_relative_links(entries)
        assert len(entries) >= 5, f"expected >=5 scanned md files, got {len(entries)}"
        assert n_links >= 100, f"expected >=100 relative links, got {n_links}"
        print(f"  ok healthy {len(entries)} md files, {n_links} relative links, 0 broken")

        base_rel, base_text = entries[0]

        # N1: link to a missing sibling file
        e1 = entries + [(base_rel, base_text + "\n[x](definitely-missing-round39.md)\n")]
        b1 = find_broken(e1, REPO_ROOT)
        assert any("definitely-missing-round39.md" in t and r == "missing target" for _, t, r in b1), b1
        print("  ok negative missing sibling file is reported")

        # N2: ../ escape outside the repo root
        e2 = entries + [(base_rel, base_text + "\n[x](../../../../nonexistent-round39/x.md)\n")]
        b2 = find_broken(e2, REPO_ROOT)
        assert any(r == "escapes repo root" for _, _, r in b2), b2
        print("  ok negative parent-directory escape is reported")

        # N3: link to a missing directory (trailing slash)
        e3 = entries + [(base_rel, base_text + "\n[x](missing-round39-dir/)\n")]
        b3 = find_broken(e3, REPO_ROOT)
        assert any("missing-round39-dir" in t and r == "missing target" for _, t, r in b3), b3
        print("  ok negative missing linked directory is reported")

        # NF1: external / anchor / mailto links are not checked
        ext = (
            "\n[e](https://example.com/a.md) [a](#section) [m](mailto:x@example.com)\n"
        )
        b_ext = find_broken(entries + [(base_rel, base_text + ext)], REPO_ROOT)
        assert b_ext == [], b_ext
        print("  ok non-flag external/anchor/mailto links are skipped")

        # NF2: pseudo-links inside fenced and inline code are not scanned
        code = (
            "\n```\n[fake](should-not-flag-fenced.md)\n```\n"
            "inline `[fake](should-not-flag-inline.md)` token\n"
        )
        b_code = find_broken(entries + [(base_rel, base_text + code)], REPO_ROOT)
        assert b_code == [], b_code
        print("  ok non-flag pseudo-links in code are ignored")

        # mutation: force one real existing target to be "missing"
        real_broken = find_broken(entries, REPO_ROOT)
        assert real_broken == []
        # pick the first real relative target from the first file that has one
        victim = None
        for rel, text in entries:
            md_path = REPO_ROOT / rel
            for m in _LINK_RE.finditer(strip_code(text)):
                t = m.group(1).strip()
                if _is_external(t):
                    continue
                p = t.split("#", 1)[0].split("?", 1)[0]
                if p and not p.startswith("/"):
                    cand = (md_path.parent / p).resolve()
                    try:
                        cand.relative_to(REPO_ROOT.resolve())
                    except ValueError:
                        continue
                    if cand.exists():
                        victim = cand
                        break
            if victim is not None:
                break
        assert victim is not None, "fixture: no real relative target found to mutate"

        def exists_deny_victim(dest: pathlib.Path) -> bool:
            return False if dest == victim else pathlib.Path.exists(dest)

        bm = find_broken(entries, REPO_ROOT, exists=exists_deny_victim)
        assert any(r == "missing target" for _, _, r in bm), bm
        print("  ok mutation a real target reported missing proves the check is live")

    except AssertionError as exc:
        print(SUCCESS_MARKER.replace("PASS", "FAIL") + f": {exc}")
        return 1
    print(SUCCESS_MARKER)
    print("3 negative, 2 non-flag, 1 healthy, 1 mutation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
