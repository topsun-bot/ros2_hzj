#!/usr/bin/env python3
"""Negative self-test for the runtime-provenance guard (eval-only).

Invoked by the Promptfoo local-script provider. It lives under ``evals/`` on
purpose, like ``fingerprint_check.py`` and the other ``*_guard_selftest.py``
scripts: it is **not** one of the 13 CI gates, is not enumerated by
``scripts/run_all_gates.py``, and needs no ``.github/workflows/ci.yml`` wiring
(so it is not blocked by the GitHub ``workflow`` token scope).

Why this exists
---------------
``scripts/check_runtime_provenance.py`` guards wiki3 §13 (underlay vs overlay
vs vendor snapshot): the Docker image must pin the Humble underlay and every
vendored tree row in ``vendor/VERSIONS.md`` must carry a 40-hex SHA. The
positive eval case (#6) only proves the *current, healthy* tree prints the
success marker (``underlay != vendor snapshot``). It cannot prove the guard's
two unique parsers still fire when they are secretly loosened. If someone
widened them, a Dockerfile pinned to ``rolling`` or a VERSIONS table whose
SHA dropped off the row would keep the gate, #6, and the #17 stdout
fingerprint all green while the provenance record silently rotted — the same
"guard disabled but all green" blind spot the other guard self-tests cover.

Scope is deliberately the guard's **unique** parsing logic, which no earlier
self-test covers:
  * ``_dockerfile_pins_humble`` parses ``ENV ROS_DISTRO`` with three distinct
    failure branches — the directive is missing entirely; it is present but
    its value cannot be parsed; or it pins a non-``humble`` distro (multiple
    ENV lines included);
  * ``_versions_rows`` requires the vendored-tree name AND a 40-hex SHA on the
    SAME table row (``row in line and _SHA_RE.search(line)``); a SHA floating
    on a different line must not satisfy the row.

The plain marker-substring checks (MANIFEST / provenance doc phrases) are
intentionally not re-tested: they are direct ``token in text`` checks with no
parser, the same shape already covered by positive cases.

Fixtures are built by **copying the five real files the guard reads**
(MANIFEST, VERSIONS, Dockerfile, provenance doc, prove_rmw.py) into a temp
tree, then mutating one file at a time and driving the injectable
``render(root=...)``. It asserts:
  1. five negative scenarios ARE caught (exit 1, no success marker, the right
     FAIL family):
       N1 Dockerfile pins ROS_DISTRO=rolling      (FAIL Dockerfile pins …);
       N2 the ENV ROS_DISTRO line is deleted       (FAIL Dockerfile missing …);
       N3 ENV ROS_DISTRO is present but valueless  (FAIL Dockerfile is not
          humble — the present-but-unparsed branch);
       N4 the 40-hex SHA is stripped from the vendor/rmw/ VERSIONS row while
          the row text stays                        (FAIL VERSIONS rows);
       N5 that SHA is moved onto a different line   (FAIL VERSIONS rows —
          proves the same-line constraint, not a mere "a SHA exists" scan);
  2. two healthy cases: the real repo ``render()`` and a pristine copied tree
     both exit 0 with the success marker;
  3. one mutation: widening ``_SHA_RE`` from a 40-hex boundary match to any
     word makes N4 slip through undetected (the row still contains words),
     and restoring the regex catches it again.

Read-only: files are created only inside a ``tempfile`` directory; the repo is
never written. Standard library only. Exit 0 when every expectation holds,
exit 1 (with details) otherwise.
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
import check_runtime_provenance as g  # noqa: E402  (sys.path set just above)

SUCCESS_MARKER = "runtime provenance guard selftest: PASS"

# All five required files are copied verbatim (they carry many markers; a
# hand-written minimal tree would rot and drift from the real record).
CONTENT_RELS = (
    g.MANIFEST_REL,
    g.VERSIONS_REL,
    g.DOCKERFILE_REL,
    g.PROVENANCE_REL,
    g.PROVE_RMW_REL,
)

# The row whose SHA we tamper with in N4 / N5 / the mutation.
RMW_ROW = "vendor/rmw/"


def _mut_docker_rolling(text: str) -> str:
    """N1: pin ROS_DISTRO to rolling."""
    mutated = text.replace("ENV ROS_DISTRO=humble", "ENV ROS_DISTRO=rolling", 1)
    if mutated == text:
        raise RuntimeError("fixture anchor: ENV ROS_DISTRO=humble not found")
    return mutated


def _mut_docker_drop_env(text: str) -> str:
    """N2: delete every ENV ROS_DISTRO line."""
    kept = [
        line
        for line in text.splitlines()
        if not re.match(r"\s*ENV\s+ROS_DISTRO", line)
    ]
    if len(kept) == len(text.splitlines()):
        raise RuntimeError("fixture anchor: no ENV ROS_DISTRO line to delete")
    return "\n".join(kept) + "\n"


def _mut_docker_valueless(text: str) -> str:
    """N3: keep the directive but give it no parseable value."""
    mutated = text.replace("ENV ROS_DISTRO=humble", "ENV ROS_DISTRO", 1)
    if mutated == text:
        raise RuntimeError("fixture anchor: ENV ROS_DISTRO=humble not found")
    return mutated


def _strip_rmw_sha(lines: list[str]) -> tuple[list[str], str]:
    """Replace the 40-hex SHA on the vendor/rmw/ row with NO_SHA; return (lines, sha)."""
    out = list(lines)
    sha = ""
    for i, line in enumerate(out):
        if RMW_ROW in line:
            match = g._SHA_RE.search(line)
            if match:
                sha = match.group(0)
                out[i] = line[: match.start()] + "NO_SHA" + line[match.end() :]
                return out, sha
    raise RuntimeError("fixture anchor: vendor/rmw/ SHA row not found")


def _mut_versions_strip_sha(text: str) -> str:
    """N4: remove the SHA from the vendor/rmw/ row, keep the row."""
    lines, _ = _strip_rmw_sha(text.splitlines())
    return "\n".join(lines) + "\n"


def _mut_versions_move_sha(text: str) -> str:
    """N5: move that SHA onto a separate line (breaks the same-line rule)."""
    lines, sha = _strip_rmw_sha(text.splitlines())
    lines.insert(0, "moved sha " + sha)
    return "\n".join(lines) + "\n"


def _seed_tree(tmp: Path, docker_mut=None, versions_mut=None) -> None:
    """Copy the five real files into the temp tree; mutate as asked."""
    for rel in CONTENT_RELS:
        dst = tmp / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        text = (ROOT / rel).read_text(encoding="utf-8")
        if rel == g.DOCKERFILE_REL and docker_mut is not None:
            text = docker_mut(text)
        if rel == g.VERSIONS_REL and versions_mut is not None:
            text = versions_mut(text)
        dst.write_text(text, encoding="utf-8")


def _render(docker_mut=None, versions_mut=None):
    with tempfile.TemporaryDirectory(prefix="prov_neg_") as d:
        tmp = Path(d)
        _seed_tree(tmp, docker_mut, versions_mut)
        return g.render(root=tmp)


def _check_negatives(failures: list[str]) -> int:
    caught = 0

    def expect(label: str, must: str, docker_mut=None, versions_mut=None) -> None:
        nonlocal caught
        out, code = _render(docker_mut=docker_mut, versions_mut=versions_mut)
        if code == 1 and g.SUCCESS_MARKER not in out and must in out:
            caught += 1
        else:
            failures.append(
                f"negative '{label}': not caught as expected "
                f"(code={code}, need {must!r})"
            )

    expect(
        "Dockerfile pins rolling",
        "FAIL Dockerfile",
        docker_mut=_mut_docker_rolling,
    )
    expect(
        "Dockerfile ENV ROS_DISTRO deleted",
        "FAIL Dockerfile",
        docker_mut=_mut_docker_drop_env,
    )
    expect(
        "Dockerfile ENV ROS_DISTRO valueless",
        "FAIL Dockerfile",
        docker_mut=_mut_docker_valueless,
    )
    expect(
        "VERSIONS vendor/rmw/ row SHA stripped",
        "FAIL VERSIONS rows",
        versions_mut=_mut_versions_strip_sha,
    )
    expect(
        "VERSIONS vendor/rmw/ SHA moved to another line",
        "FAIL VERSIONS rows",
        versions_mut=_mut_versions_move_sha,
    )
    return caught


def _check_healthy(failures: list[str]) -> int:
    healthy = 0

    # H1: the real repo renders green.
    out_real, code_real = g.render()
    if code_real == 0 and g.SUCCESS_MARKER in out_real:
        healthy += 1
    else:
        failures.append("healthy real repo: expected exit 0 + success marker")

    # H2: a pristine copied temp tree renders green.
    out_copy, code_copy = _render()
    if code_copy == 0 and g.SUCCESS_MARKER in out_copy:
        healthy += 1
    else:
        failures.append("healthy copied tree: expected exit 0 + success marker")

    return healthy


def _check_mutation(failures: list[str]) -> int:
    """Widening _SHA_RE to any word must silence N4; restore re-catches it."""
    original = g._SHA_RE
    widened = re.compile(r"\b\w+\b")
    try:
        with tempfile.TemporaryDirectory(prefix="prov_mut_") as d:
            tmp = Path(d)
            _seed_tree(tmp, versions_mut=_mut_versions_strip_sha)

            g._SHA_RE = widened
            out_wide, code_wide = g.render(root=tmp)

            g._SHA_RE = original
            out_restored, code_restored = g.render(root=tmp)
    finally:
        g._SHA_RE = original

    widened_silenced = (
        code_wide == 0
        and g.SUCCESS_MARKER in out_wide
        and "FAIL VERSIONS rows" not in out_wide
    )
    restored_catches = code_restored == 1 and "FAIL VERSIONS rows" in out_restored
    if widened_silenced and restored_catches:
        return 1
    failures.append(
        "mutation: widening _SHA_RE did not silence N4 "
        f"(silenced={widened_silenced}) or restore did not re-catch it "
        f"(restored_catches={restored_catches})"
    )
    return 0


def main() -> int:
    failures: list[str] = []

    negative = _check_negatives(failures)
    healthy = _check_healthy(failures)
    mutation = _check_mutation(failures)

    print("# Runtime-provenance guard negative self-test")
    print(
        f"- negative scenarios caught: {negative}/5; "
        f"healthy trees green: {healthy}/2; "
        f"mutation behaves: {mutation}/1"
    )

    if failures:
        print("\nFAIL:")
        for item in failures:
            print(f"- {item}")
        print(
            "\nThe runtime-provenance guard no longer behaves as specified. "
            f"Expected {SUCCESS_MARKER!r}. Exit 1."
        )
        return 1

    print(f"- **{SUCCESS_MARKER}** (5 negative, 2 healthy, 1 mutation)")
    print(
        "\nThe guard catches a Dockerfile pinning rolling, a missing "
        "ENV ROS_DISTRO directive, a present-but-valueless ENV, and a VERSIONS "
        "row whose 40-hex SHA is stripped or moved off the row; a healthy tree "
        "stays green; and widening the SHA regex demonstrably silences the "
        "VERSIONS-row check. Read-only, tempdir-only. Exit 0."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
