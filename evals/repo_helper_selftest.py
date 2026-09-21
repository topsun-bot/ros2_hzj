#!/usr/bin/env python3
"""Shared gate-helper (`scripts/_repo.py`) contract self-test (#37).

Context
-------
`scripts/_repo.py` is the shared base every gate was refactored onto
(modernization plan §5.3): ``repo_root`` / ``read_utf8`` / ``line_at`` /
``emit_render`` / ``append_bullets`` / ``report_missing_file`` /
``append_failures_block``. The 11 guard selftests (#18-#28) exercise the gates
that *consume* these helpers, and #29 only lists ``_repo.py`` as a non-gate
library for registry purposes -- none of them pin the helper module's own
branching/rendering contracts. A regression in this shared base (e.g. repo_root
falling back to the wrong directory, emit_render swallowing a nonzero code, or
a FAIL block losing its heading) would silently weaken every gate at once.

This eval-only test imports the REAL ``scripts/_repo.py`` and pins its
contracts directly. Filesystem branches use tempdir + chdir with guaranteed
cwd restore; rendering helpers are pure in-memory. It edits nothing in the
repo and is not a gate / not in run_all_gates.GATES / not CI-enumerated.

Scenarios: 3 negative (repo_root with no anchor raises ValueError; repo_root
with no anchor anywhere exits nonzero with the canonical message; the
missing-file + FAIL-block rendering must stay visibly FAILing), 2 non-flag
(empty bullet list is a no-op and emit_render passes code 0 through with the
text; lenient UTF-8 replace and line_at single/last/newline edges),
1 healthy (real repo root resolved from cwd, real files read, first line
indexed), 1 mutation (a same-named anchor in cwd must win over the scripts/
fallback, proving repo_root does not always return the scripts parent).
"""

from __future__ import annotations

import contextlib
import io
import os
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
import _repo  # noqa: E402  (sys.path set just above)

SUCCESS_MARKER = "repo helper selftest: PASS"
ANCHOR = Path("AGENTS.md")


def main() -> int:
    saved_cwd = Path.cwd()
    try:
        try:
            # --- healthy: real repo resolves from cwd, real reads/index work ---
            os.chdir(REPO_ROOT)
            root = _repo.repo_root(ANCHOR)
            assert root == REPO_ROOT.resolve(), root
            assert (root / "scripts" / "_repo.py").is_file()
            agents = _repo.read_utf8(root / ANCHOR)
            assert agents.strip().startswith("# AGENTS"), agents[:20]
            own_src = _repo.read_utf8(SCRIPTS / "_repo.py")
            assert _repo.line_at(own_src, 0) == own_src.splitlines()[0]
            print("  ok healthy real repo root + utf8 read + first-line index")

            # --- N1: no anchor -> ValueError (never a silently wrong root) ---
            try:
                _repo.repo_root()
            except ValueError as exc:
                assert "requires at least one anchor" in str(exc), str(exc)
            else:
                raise AssertionError("repo_root() with no anchor did not raise")
            print("  ok negative missing anchor argument raises ValueError")

            # --- N2: anchor in neither cwd nor scripts-parent -> SystemExit ---
            unique = Path("zzz-no-such-anchor-round40.md")
            with tempfile.TemporaryDirectory() as d:
                os.chdir(d)
                assert not (REPO_ROOT / unique).exists()
                try:
                    _repo.repo_root(unique)
                except SystemExit as exc:
                    assert "cannot find repo root" in str(exc), str(exc)
                    assert exc.code not in (0, None), exc.code
                else:
                    raise AssertionError("repo_root with no anchor did not exit")
            print("  ok negative no-anchor-anywhere exits nonzero with message")

            # --- N3: failure rendering must stay visibly FAILing ---
            failures: list[str] = []
            lines: list[str] = []
            _repo.report_missing_file(failures, lines, "x.md")
            assert failures == ["missing file `x.md`"], failures
            assert lines == ["- **FAIL missing:** `x.md`"], lines
            block: list[str] = []
            _repo.append_failures_block(block, ["f1", "f2"])
            assert block == ["FAIL:", "- f1", "- f2", ""], block
            assert block[0] == "FAIL:" and block[-1] == ""
            print("  ok negative missing-file + FAIL-block render verbatim")

            # --- NF1: empty bullets no-op; emit_render passes code 0 + text ---
            empty: list[str] = []
            _repo.append_bullets(empty, [])
            assert empty == []
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code0 = _repo.emit_render(("HEALTHY-TEXT", 0))
            assert code0 == 0 and buf.getvalue() == "HEALTHY-TEXT", (code0, buf.getvalue())
            print("  ok non-flag empty bullets no-op, emit_render code0 passthrough")

            # --- NF2: lenient utf8 + line_at edges ---
            with tempfile.NamedTemporaryFile(delete=False) as fh:
                fh.write(b"abc\xffdef")
                bad = Path(fh.name)
            decoded = _repo.read_utf8(bad)
            assert "\ufffd" in decoded, decoded
            sample = "abc\ndef\nghi"
            assert _repo.line_at(sample, 0) == "abc"
            assert _repo.line_at(sample, 5) == "def"
            assert _repo.line_at(sample, 9) == "ghi"
            assert _repo.line_at(sample, 3) == "abc"  # newline index -> prior line
            assert _repo.line_at("abc", 1) == "abc"  # single line, no trailing nl
            print("  ok non-flag lenient utf8 replace and line_at edges")

            # --- mutation: same-named anchor in cwd must beat scripts fallback ---
            with tempfile.TemporaryDirectory() as d:
                td = Path(d)
                (td / ANCHOR).write_text("decoy\n", encoding="utf-8")
                os.chdir(td)
                picked = _repo.repo_root(ANCHOR)
                assert picked == td.resolve(), picked
                assert picked != REPO_ROOT.resolve()
            print("  ok mutation cwd anchor wins over scripts-parent fallback")

        finally:
            os.chdir(saved_cwd)

    except AssertionError as exc:
        os.chdir(saved_cwd)
        print(SUCCESS_MARKER.replace("PASS", "FAIL") + f": {exc}")
        return 1
    print(SUCCESS_MARKER)
    print("3 negative, 2 non-flag, 1 healthy, 1 mutation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
