#!/usr/bin/env python3
"""Negative self-test for the Executor/WaitSet map honesty guard (eval-only).

Invoked by the Promptfoo local-script provider. It lives under ``evals/`` on
purpose, like ``fingerprint_check.py`` and the frozen/env/unitree/source-map
guard self-tests: it is **not** one of the 13 CI gates, is not enumerated by
``scripts/run_all_gates.py``, and needs no ``.github/workflows/ci.yml`` wiring
(so it is not blocked by the GitHub ``workflow`` token scope).

Why this exists
---------------
``scripts/check_executor_map.py`` (wiki3 §13 wait→callback identity map) parses
``docs/architecture/feishu-executor-waitset.md`` and fails when a required doc
disappears, a Humble ``rcl/rclcpp/rclpy`` tree appears under ``vendor/``, an
identity marker or Feishu URL is missing, an allowlisted WaitSet/wait/take
symbol file is no longer cited, or (via the shared ``_md_paths`` checks,
already covered by the #21 source-map self-test) a cited path/symbol is gone.
The positive eval case (#5) and the #17 stdout fingerprint only prove the
*current, healthy* tree renders green; they cannot prove the executor-specific
checks still fire after tampering.

This self-test deliberately covers only the branches that are **unique to the
executor guard** — the shared cited-path/symbol/stale-line loop is already
exercised by #21 and must not be duplicated here:
  1. five negative scenarios ARE caught (exit 1, no success marker, the right
     FAIL family):
       N1 a Humble vendor/rcl{,cpp,py} tree appears (FAIL vendored);
       N2 an identity marker is removed from the map (FAIL markers);
       N3 a Feishu URL is removed (FAIL Feishu URL);
       N4 an allowlisted symbol file is no longer cited (FAIL uncited);
       N5 a required doc is missing on disk (FAIL missing);
  2. two parse-guard mechanism assertions for the two ``parse_map`` parameters
     that only this caller uses:
       PG1 ``absent_keys`` keeps ``vendor/rcl`` citations out of the cited set
           (they document an *absent* tree); without it the citation enters the
           set and would be required to exist;
       PG2 ``reject_bare_words`` keeps the prose word `` `dimos_bridge` `` from
           resolving to ``docs/architecture/dimos_bridge``; without the flag it
           is mistaken for a path;
  3. two healthy cases: the real repo ``render()`` and a minimal healthy temp
     tree both exit 0 with the success marker (the minimal tree itself cites
     the absent trees and the bare prose word, so a green render proves both
     parse guards actively prevent false positives on a healthy map);
  4. one mutation: emptying ``ABSENT_VENDOR_TREES`` while all three trees exist
     must silence N1 (the tampered tree exits 0 with no FAIL vendored), and
     restoring the tuple must re-catch it — proving N1 depends on the
     vendored-tree detector rather than passing by accident.

The minimal tree copies the 11 real allowlisted symbol files (so symbol
lookups run against genuine content, as in the Unitree #20 fixture) and hand-
writes a tiny map carrying the 16 identity markers and 3 Feishu URLs.
Read-only against the repo: it creates files only inside ``tempfile``
directories. Standard library only. Exit 0 when every expectation holds,
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
import check_executor_map as g  # noqa: E402  (sys.path set just above)

SUCCESS_MARKER = "executor map guard selftest: PASS"
HEALTHY_MARKER = "Executor map healthy"

MAP_REL = g.MAP_REL
ALLOW = g.SYMBOL_ALLOWLIST
REQUIRED = g.REQUIRED_DOCS
MARKERS = list(g.DOC_MARKERS)
URLS = list(g.FEISHU_URLS)
ABSENT = ("vendor/rcl", "vendor/rclcpp", "vendor/rclpy")
# One allowlisted key dropped in N4 (file stays on disk, only the citation goes).
UNCITED_KEY = "vendor/CycloneDDS/src/core/ddsc/src/dds_read.c"
# One required doc removed in N5 (existence-only placeholder).
MISSING_DOC = Path("scripts/prove_rmw.py")


def _write(root: Path, rel: Path, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _build(
    root: Path,
    *,
    with_markers: bool = True,
    with_urls: bool = True,
    skip_cite: str | None = None,
    remove_doc: Path | None = None,
) -> Path:
    """Populate a minimal healthy executor-map tree under ``root``."""
    # Required docs: placeholders (existence-only), except the map itself.
    for rel in REQUIRED:
        if rel == MAP_REL:
            continue
        if remove_doc is not None and rel == remove_doc:
            continue
        _write(root, rel, "placeholder\n")
    # Real allowlisted symbol files, copied verbatim.
    for key in ALLOW:
        dst = root / key
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / key, dst)

    lines = ["# minimal executor map", ""]
    shown = MARKERS if with_markers else [m for m in MARKERS if m != "§9.4"]
    lines.append("Markers: " + " | ".join(shown))
    for url in URLS:
        if not with_urls and url == URLS[-1]:
            continue
        lines.append(f"see {url}")
    lines.append("")
    lines.append("Humble rclcpp/rclpy 不在 vendor；")
    # Citations of trees that must stay absent (exercised via absent_keys).
    lines.append("本仓没有 `vendor/rcl`、`vendor/rclcpp`、`vendor/rclpy`。")
    # A bare prose word (exercised via reject_bare_words); no slash, no suffix.
    lines.append("桥接在 `dimos_bridge` 包内（裸词，不是路径）。")
    lines.append("")
    for key in ALLOW:
        if skip_cite is not None and key == skip_cite:
            continue
        lines.append(f"- cited `{key}`")
    _write(root, MAP_REL, "\n".join(lines) + "\n")
    return root / MAP_REL


def _check_negatives(failures: list[str]) -> int:
    caught = 0

    def expect(label: str, build_kwargs: dict, mutate, must: tuple[str, ...]) -> None:
        nonlocal caught
        with tempfile.TemporaryDirectory(prefix="executor_neg_") as d:
            tmp = Path(d)
            _build(tmp, **build_kwargs)
            if mutate is not None:
                mutate(tmp)
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

    # N1: Humble client trees appear under vendor/.
    def make_vendored(tmp: Path) -> None:
        for rel in ABSENT:
            (tmp / rel).mkdir(parents=True, exist_ok=True)

    expect(
        "vendored Humble rcl* tree",
        {},
        make_vendored,
        ("FAIL vendored", "vendor/rcl"),
    )

    # N2: an identity marker is gone.
    expect(
        "missing identity marker",
        {"with_markers": False},
        None,
        ("FAIL markers", "§9.4"),
    )

    # N3: a Feishu URL is gone.
    expect(
        "missing Feishu URL",
        {"with_urls": False},
        None,
        ("FAIL Feishu URL", URLS[-1]),
    )

    # N4: an allowlisted file exists but is no longer cited.
    expect(
        "allowlisted key uncited",
        {"skip_cite": UNCITED_KEY},
        None,
        ("FAIL uncited", UNCITED_KEY),
    )

    # N5: a required doc is missing on disk.
    expect(
        "required doc missing",
        {"remove_doc": MISSING_DOC},
        None,
        ("FAIL missing", MISSING_DOC.as_posix()),
    )

    return caught


def _check_parse_guards(failures: list[str]) -> int:
    """The two parse_map parameters unique to the executor caller."""
    ok_count = 0
    with tempfile.TemporaryDirectory(prefix="executor_pg_") as d:
        tmp = Path(d)
        map_path = _build(tmp)
        absent = set(ABSENT)

        # PG1: absent_keys filters citations of trees documented as absent.
        cited_with, _ = _md_paths.parse_map(
            tmp, map_path, absent_keys=absent, reject_bare_words=True
        )
        cited_without, _ = _md_paths.parse_map(
            tmp, map_path, absent_keys=set(), reject_bare_words=True
        )
        keys_with = {p.as_posix() for p in cited_with}
        keys_without = {p.as_posix() for p in cited_without}
        pg1 = "vendor/rcl" not in keys_with and "vendor/rcl" in keys_without

        # PG2: reject_bare_words keeps the prose word from becoming a path.
        cited_reject, _ = _md_paths.parse_map(
            tmp, map_path, absent_keys=set(), reject_bare_words=True
        )
        cited_bare, _ = _md_paths.parse_map(
            tmp, map_path, absent_keys=set(), reject_bare_words=False
        )
        keys_reject = {p.as_posix() for p in cited_reject}
        keys_bare = {p.as_posix() for p in cited_bare}
        bare_resolved = "docs/architecture/dimos_bridge"
        pg2 = bare_resolved not in keys_reject and bare_resolved in keys_bare

    if pg1:
        ok_count += 1
    else:
        failures.append(
            "parse-guard PG1: absent_keys did not keep vendor/rcl out of the "
            "cited set (or the fixture stopped citing it)"
        )
    if pg2:
        ok_count += 1
    else:
        failures.append(
            "parse-guard PG2: reject_bare_words did not reject the bare prose "
            "word `dimos_bridge` (or it stopped resolving without the flag)"
        )
    return ok_count


def _check_healthy(failures: list[str]) -> int:
    healthy = 0

    # H1: the real repo renders green (regression guard for this self-test).
    out_real, code_real = g.render()
    if code_real == 0 and HEALTHY_MARKER in out_real:
        healthy += 1
    else:
        failures.append("healthy real repo: expected exit 0 + success marker")

    # H2: the minimal healthy temp tree renders green. It cites the absent
    # trees and a bare prose word, so green proves both parse guards prevent
    # false positives (otherwise this same tree fails with missing paths).
    with tempfile.TemporaryDirectory(prefix="executor_ok_") as d:
        tmp = Path(d)
        _build(tmp)
        out_copy, code_copy = g.render(root=tmp)
    if code_copy == 0 and HEALTHY_MARKER in out_copy:
        healthy += 1
    else:
        failures.append(
            "healthy temp tree: expected exit 0 + success marker "
            f"(code={code_copy})"
        )

    return healthy


def _check_mutation(failures: list[str]) -> int:
    """Emptying ABSENT_VENDOR_TREES must silence N1, then restore re-catches."""
    original = g.ABSENT_VENDOR_TREES
    try:
        with tempfile.TemporaryDirectory(prefix="executor_mut_") as d:
            tmp = Path(d)
            _build(tmp)
            for rel in ABSENT:
                (tmp / rel).mkdir(parents=True, exist_ok=True)

            g.ABSENT_VENDOR_TREES = ()
            # render() derives absent_keys from this tuple, so the cited
            # vendor/rcl* trees now exist on disk and nothing flags them.
            out_wide, code_wide = g.render(root=tmp)

            g.ABSENT_VENDOR_TREES = original
            out_restored, code_restored = g.render(root=tmp)
    finally:
        g.ABSENT_VENDOR_TREES = original

    widened_silenced = code_wide == 0 and "FAIL vendored" not in out_wide
    restored_catches = code_restored == 1 and "FAIL vendored" in out_restored
    if widened_silenced and restored_catches:
        return 1
    failures.append(
        "mutation: empty ABSENT_VENDOR_TREES did not silence the vendored "
        f"check (silenced={widened_silenced}, code={code_wide}) or restore "
        f"did not re-catch it (restored_catches={restored_catches})"
    )
    return 0


def main() -> int:
    failures: list[str] = []

    negative = _check_negatives(failures)
    parse_guards = _check_parse_guards(failures)
    healthy = _check_healthy(failures)
    mutation = _check_mutation(failures)

    print("# Executor/WaitSet map guard negative self-test")
    print(
        f"- negative scenarios caught: {negative}/5; "
        f"parse guards: {parse_guards}/2; "
        f"healthy trees green: {healthy}/2; "
        f"mutation behaves: {mutation}/1"
    )

    if failures:
        print("\nFAIL:")
        for item in failures:
            print(f"- {item}")
        print(
            "\nThe executor-map guard no longer behaves as specified. "
            f"Expected {SUCCESS_MARKER!r}. Exit 1."
        )
        return 1

    print(
        f"- **{SUCCESS_MARKER}** "
        "(5 negative, 2 parse-guard, 2 healthy, 1 mutation)"
    )
    print(
        "\nThe guard catches a vendored Humble rcl* tree, missing identity "
        "markers/Feishu URLs, uncited allowlisted files and missing required "
        "docs; the executor-only absent_keys and reject_bare_words parse "
        "guards hold; healthy trees stay green; and emptying "
        "ABSENT_VENDOR_TREES demonstrably silences the vendored-tree check. "
        "The shared cited-path/symbol loop is covered by the #21 source-map "
        "self-test, not duplicated here. Read-only, tempdir-only. Exit 0."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
