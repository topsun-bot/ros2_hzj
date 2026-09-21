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

Round 36 first covered only ``docs/refactor/*.md`` (01 walk-through, 02 plan,
ITERATION_LOG) and the ``evals/`` docs (README, results/BASELINE). Round 44
widened the surface to **every first-party (A-side) markdown doc** in the
repo -- the ``docs/architecture`` feishu-* maps / source map that the guards
cite, ``docs/security`` (CVE audit), ``docs/testing`` (Mac HIL), ``docs/usage``,
``docs/eval``, ``config/**``, ``scripts/**``, ``dimos_bridge/SOURCE.md``,
``docker/**`` and the root ``README.md`` / ``AGENTS.md`` -- 34 files / ~923
relative links at widening time, with **zero machine checks** before #36 that
their targets still exist. Renaming/moving a file without updating a relative
link would silently rot the docs.

Two trees are deliberately **excluded** (``_excluded``):
  * ``vendor/**`` -- third-party DDS/rmw source trees (read-only Hold). Their
    own upstream docs carry a few pre-existing broken relative links (e.g.
    CycloneDDS ``docs/manual/config.rst``); those are not ours to fix and must
    not make this check red;
  * ``docs/artifacts/**`` -- frozen bench artifacts/historical snapshots
    (including the number-frozen ``SCOREBOARD.md``); link integrity of frozen
    output snapshots is out of scope for this loop.

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
missing linked directory), 3 non-flag (external/anchor/mailto links skipped;
pseudo-links inside fenced/inline code skipped; the read-only ``vendor/**`` and
frozen ``docs/artifacts/**`` trees are excluded even though vendor docs carry
upstream-broken links), 1 healthy (real first-party docs: zero broken, a
link/file floor so a vacuous empty scan cannot pass, and an explicit surface
assertion that key A-side docs are scanned while vendor/artifacts are not),
1 mutation (force one real target to "missing" via an exists wrapper; it must
be reported, proving the check is not vacuous).
"""

from __future__ import annotations

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
# First-party (A-side) docs only. "*.md" matches the repo-root markdown files
# (README.md, AGENTS.md) without descending; each docs/<area> subtree is listed
# explicitly so the untracked root draft docs/01-dds-request-flow.md (which sits
# directly under docs/) is never picked up.
SCAN_GLOBS = (
    "docs/refactor/**/*.md",
    "evals/**/*.md",
    "docs/architecture/**/*.md",
    "docs/security/**/*.md",
    "docs/testing/**/*.md",
    "docs/usage/**/*.md",
    "docs/eval/**/*.md",
    "config/**/*.md",
    "scripts/**/*.md",
    "dimos_bridge/**/*.md",
    "docker/**/*.md",
    "*.md",
)

# Read-only third-party source trees and frozen bench artifacts are never
# scanned: vendor docs carry upstream-owned broken links we must not "fix"
# (Hold), and artifacts are frozen output snapshots.
EXCLUDE_PREFIXES = ("vendor/", "docs/artifacts/")


def _excluded(rel_posix: str) -> bool:
    """True for out-of-scope trees the link checker must never scan."""
    return rel_posix.startswith(EXCLUDE_PREFIXES)

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
            if not p.is_file():
                continue
            rel = p.relative_to(REPO_ROOT).as_posix()
            if _excluded(rel):
                continue
            entries.append((rel, p.read_text(encoding="utf-8")))
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
        assert len(entries) >= 30, f"expected >=30 first-party md files, got {len(entries)}"
        assert n_links >= 900, f"expected >=900 relative links, got {n_links}"
        print(f"  ok healthy {len(entries)} md files, {n_links} relative links, 0 broken")

        # Surface contract: key first-party authority docs must actually be
        # scanned (a typo in a glob that silently shrank the surface could
        # otherwise still clear the numeric floor via the remaining files).
        scanned_rels = {rel for rel, _ in entries}
        must_scan = (
            "docs/architecture/ros2-source-map.md",
            "docs/security/2026-09-vendor-cve-audit.md",
            "docs/testing/2026-09-mac-hil.md",
            "config/env/README.md",
            "scripts/bench/README.md",
            "README.md",
            "AGENTS.md",
            "docs/refactor/ITERATION_LOG.md",
            "evals/README.md",
        )
        missing_surface = [r for r in must_scan if r not in scanned_rels]
        assert not missing_surface, f"scan surface lost A-side docs: {missing_surface}"
        # And the read-only / frozen trees must never enter the scan set.
        leaked = [r for r in scanned_rels if _excluded(r)]
        assert not leaked, f"vendor/artifacts docs must be excluded, got: {leaked[:5]}"
        print(f"  ok healthy scan surface covers {len(must_scan)} pinned A-side docs, vendor/artifacts excluded")

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

        # NF3: read-only vendor / frozen artifacts trees are excluded even
        # though vendor docs genuinely contain upstream-broken relative links.
        assert _excluded("vendor/CycloneDDS/README.md")
        assert _excluded("docs/artifacts/bench/SCOREBOARD.md")
        assert not _excluded("docs/architecture/ros2-source-map.md")
        assert not _excluded("evals/README.md")
        vendor_broken = [
            ("vendor/CycloneDDS/README.md", "[x](docs/manual/config.rst)"),
            ("vendor/Fast-DDS/test/performance/latency/README.md", "[x](latency-measure)"),
        ]
        # The real scan surface must contain no vendor/artifacts file at all;
        # injecting their known-broken links only matters if such a file were
        # (wrongly) scanned, which the surface leak assertion above forbids.
        assert all(rel.startswith(("vendor/", "docs/artifacts/")) for rel, _ in vendor_broken)
        assert not any(_excluded(rel) for rel, _ in entries), "scan surface leaked an excluded tree"
        print("  ok non-flag vendor (read-only) and artifacts (frozen) trees are excluded")

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
    print("3 negative, 3 non-flag, 1 healthy, 1 mutation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
