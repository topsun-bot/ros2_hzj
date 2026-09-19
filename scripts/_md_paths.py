#!/usr/bin/env python3
"""Shared markdown source-map parsing for gate scripts.

Helpers extracted verbatim from check_source_map.py and
check_executor_map.py (modernization plan Step 3): repository-path
recognition, citation extraction from markdown, identifier lookup and
the cited-path / allowlisted-symbol render loop.

Underscore prefix: helper module, not itself a CI gate. Do not add it to
the command list in docs/architecture/ci-cd-gates.md or run_all_gates.py.

Two behavioural differences between the two callers are kept explicit:

- ``reject_bare_words`` (executor map only): a prose word such as
  ``dimos_bridge`` with no slash and no suffix is not a path citation.
- ``absent_keys`` (executor map only): paths cited as *absent*
  (e.g. vendor/rcl) must not be required to exist.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys
from _repo import read_utf8


REPO_PREFIXES = (
    "vendor/",
    "scripts/",
    "docker/",
    "docs/",
    "config/",
    "dimos_bridge/",
)

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
TICK_PATH_RE = re.compile(
    r"`("
    r"(?:\.\./)*(?:vendor|scripts|docker|docs|config|dimos_bridge)"
    r"(?:/[\w.+-]+)*"
    r"/?"
    r")(?::(\d+))?`"
)
FILE_LINE_RE = re.compile(
    r"(?P<name>[\w./+-]+\.(?:cpp|cc|h|hpp|c|md|py|xml)):(?P<line>\d+)"
)

_IDENT_RE_CACHE: dict[str, "re.Pattern[str]"] = {}


def repo_root(map_rel: Path) -> Path:
    """Locate the repository root anchored on a required markdown map."""
    cwd = Path.cwd()
    if (cwd / map_rel).is_file():
        return cwd.resolve()
    here = Path(__file__).resolve().parent
    candidate = here.parent
    if (candidate / map_rel).is_file():
        return candidate
    sys.exit(f"cannot find {map_rel} from cwd={cwd} or {candidate}")


def ident_re(symbol: str) -> "re.Pattern[str]":
    cached = _IDENT_RE_CACHE.get(symbol)
    if cached is None:
        cached = re.compile(r"(?<![\w])" + re.escape(symbol) + r"(?![\w])")
        _IDENT_RE_CACHE[symbol] = cached
    return cached


def symbol_lines(text: str, symbol: str) -> list[int]:
    pat = ident_re(symbol)
    return [i for i, line in enumerate(text.splitlines(), 1) if pat.search(line)]


def looks_like_repo_path(raw: str) -> bool:
    if not raw or "..." in raw:
        return False
    if raw.startswith(("http://", "https://", "mailto:", "<", "/")):
        return False
    stripped = raw.lstrip("./")
    return stripped.startswith(REPO_PREFIXES) or any(
        raw.startswith(p) for p in REPO_PREFIXES
    )


def to_repo_rel(
    root: Path,
    map_path: Path,
    raw: str,
    reject_bare_words: bool = False,
) -> Path | None:
    target = raw.split("#", 1)[0].strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    if " " in target:
        target = target.split(" ", 1)[0]
    if not target or "..." in target:
        return None
    if target.startswith(("http://", "https://", "mailto:", "<", "/")):
        return None
    # Prose like `dimos_bridge` is not a path citation (executor map only).
    if reject_bare_words and (
        not target.startswith(".")
        and not looks_like_repo_path(target)
        and "/" not in target
        and not Path(target).suffix
    ):
        return None
    if target.startswith("."):
        dest = map_path.parent / target
    elif looks_like_repo_path(target):
        dest = root / target
    else:
        dest = map_path.parent / target
    try:
        dest = dest.resolve()
        rel = dest.relative_to(root.resolve())
    except (OSError, ValueError):
        return None
    if not rel.parts or str(rel).startswith(".."):
        return None
    return rel


def parse_map(
    root: Path,
    map_path: Path,
    absent_keys: set[str] | None = None,
    reject_bare_words: bool = False,
) -> tuple[dict[Path, set[int]], list[str]]:
    """Return {repo-rel path: cited line numbers} and parse notes."""
    text = map_path.read_text(encoding="utf-8")
    body = FENCE_RE.sub("", text)
    cited: dict[Path, set[int]] = {}
    notes: list[str] = []
    absent = absent_keys or set()

    def add(rel: Path | None, line: int | None = None) -> None:
        if rel is None:
            return
        # Paths cited as absent are not required to exist.
        if rel.as_posix() in absent:
            return
        cited.setdefault(rel, set())
        if line is not None and line > 0:
            cited[rel].add(line)

    for raw in LINK_RE.findall(body):
        target = raw.strip()
        line: int | None = None
        # ](path/file.cpp:123) — rare, but keep line numbers checkable.
        m = re.search(r":(\d+)$", target)
        if m and re.search(r"\.\w+:\d+$", target):
            line = int(m.group(1))
            target = target[: m.start()]
        add(to_repo_rel(root, map_path, target, reject_bare_words), line)

    for match in TICK_PATH_RE.finditer(body):
        raw, line_s = match.group(1), match.group(2)
        add(
            to_repo_rel(root, map_path, raw, reject_bare_words),
            int(line_s) if line_s else None,
        )

    # Filename:line leftovers (e.g. WriterHistory.cpp:208) mapped by suffix.
    for match in FILE_LINE_RE.finditer(body):
        name = match.group("name")
        line = int(match.group("line"))
        rel = (
            to_repo_rel(root, map_path, name, reject_bare_words)
            if looks_like_repo_path(name)
            else None
        )
        if rel is None:
            suffix = name.split("/")[-1]
            hits = [p for p in cited if p.name == suffix]
            if len(hits) == 1:
                rel = hits[0]
            elif len(hits) > 1:
                notes.append(
                    f"ambiguous line cite {name}:{line} matches {len(hits)} cited paths"
                )
                continue
            else:
                continue
        add(rel, line)

    return cited, notes


def check_cited_paths(
    root: Path,
    cited: dict[Path, set[int]],
    symbol_allowlist: dict[str, tuple[str, ...]],
    failures: list[str],
    warnings: list[str],
) -> tuple[list[str], int, int]:
    """Render existence + allowlisted-symbol checks for cited paths.

    Mutates ``failures`` / ``warnings`` in place (callers own the
    cumulative counts and the trailing Warnings section). Returns
    (rendered lines, paths-on-disk count, ok-symbol count).
    """
    lines: list[str] = []
    ok_paths = 0
    symbol_ok = 0

    for rel in sorted(cited, key=lambda p: str(p)):
        abs_path = root / rel
        key = rel.as_posix()
        if abs_path.is_file() or abs_path.is_dir():
            ok_paths += 1
            kind = "dir" if abs_path.is_dir() else "file"
            extra = ""
            line_nos = sorted(cited[rel])
            if line_nos:
                extra = f" (cited L{', L'.join(str(n) for n in line_nos)})"
            lines.append(f"- **ok {kind}:** `{key}`{extra}")
        else:
            failures.append(f"missing path `{key}`")
            lines.append(f"- **FAIL missing:** `{key}`")
            continue

        if not abs_path.is_file():
            continue
        allowlisted = symbol_allowlist.get(key)
        if not allowlisted:
            continue
        text = read_utf8(abs_path)
        cited_lines = cited[rel]
        for symbol in allowlisted:
            hits = symbol_lines(text, symbol)
            if not hits:
                failures.append(f"symbol `{symbol}` gone from `{key}`")
                lines.append(f"  - **FAIL symbol:** `{symbol}` not in `{key}`")
                continue
            symbol_ok += 1
            where = hits[0] if len(hits) == 1 else f"{hits[0]} (+{len(hits) - 1})"
            if cited_lines and cited_lines.isdisjoint(hits):
                cited_s = ", ".join(f"L{n}" for n in sorted(cited_lines))
                msg = (
                    f"`{key}` {cited_s} is stale for `{symbol}` "
                    f"(found L{hits[0]}); symbol exists"
                )
                warnings.append(msg)
                lines.append(f"  - **WARN stale line:** `{symbol}` at L{where}")
            else:
                lines.append(f"  - **ok symbol:** `{symbol}` at L{where}")

    return lines, ok_paths, symbol_ok
