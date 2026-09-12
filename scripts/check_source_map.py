#!/usr/bin/env python3
"""Assert ros2-source-map.md still points at real in-tree files (wiki3 §13.2).

Vanilla box (no ROS): exit 0 when the map is healthy.
Parses only docs/architecture/ros2-source-map.md — not the rest of docs/.
No extra dependencies. Style follows scripts/prove_rmw.py.

Stale line numbers: WARN + exit 0 if the symbol still exists.
Missing file or missing allowlisted symbol: FAIL (exit 1).
"""

from __future__ import annotations

from pathlib import Path
import re
import sys


MAP_REL = Path("docs/architecture/ros2-source-map.md")

# Well-known symbols the map is about. Checked only if that file is cited.
SYMBOL_ALLOWLIST: dict[str, tuple[str, ...]] = {
    "vendor/Fast-DDS/src/cpp/rtps/history/WriterHistory.cpp": ("add_change",),
    "vendor/Fast-DDS/src/cpp/rtps/reader/StatefulReader.cpp": (
        "process_data_msg",
        "change_received",
    ),
    "vendor/Fast-DDS/src/cpp/rtps/history/ReaderHistory.cpp": (
        "received_change",
        "add_change",
    ),
    "vendor/Fast-DDS/src/cpp/fastdds/publisher/DataWriterHistory.cpp": (
        "add_pub_change",
    ),
    "vendor/rmw/rmw/include/rmw/rmw.h": (
        "rmw_publish",
        "rmw_wait",
        "rmw_take",
        "rmw_get_implementation_identifier",
    ),
    "vendor/rmw_implementation/rmw_implementation/src/functions.cpp": (
        "load_library",
    ),
    "vendor/rmw_fastrtps/rmw_fastrtps_cpp/src/identifier.cpp": (
        "rmw_fastrtps_cpp",
    ),
    "vendor/rmw_fastrtps/rmw_fastrtps_shared_cpp/src/rmw_publish.cpp": (
        "__rmw_publish",
    ),
    "vendor/rmw_cyclonedds/rmw_cyclonedds_cpp/src/rmw_node.cpp": (
        "eclipse_cyclonedds_identifier",
    ),
    "vendor/CycloneDDS/src/core/ddsi/src/ddsi_whc.c": ("ddsi_whc_insert",),
}

_REPO_PREFIXES = (
    "vendor/",
    "scripts/",
    "docker/",
    "docs/",
    "config/",
    "dimos_bridge/",
)

_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_TICK_PATH_RE = re.compile(
    r"`("
    r"(?:\.\./)*(?:vendor|scripts|docker|docs|config|dimos_bridge)"
    r"(?:/[\w.+-]+)*"
    r"/?"
    r")(?::(\d+))?`"
)
_FILE_LINE_RE = re.compile(
    r"(?P<name>[\w./+-]+\.(?:cpp|cc|h|hpp|c|md|py|xml)):(?P<line>\d+)"
)
_IDENT_RE_CACHE: dict[str, re.Pattern[str]] = {}


def _repo_root() -> Path:
    cwd = Path.cwd()
    if (cwd / MAP_REL).is_file():
        return cwd.resolve()
    here = Path(__file__).resolve().parent
    candidate = here.parent
    if (candidate / MAP_REL).is_file():
        return candidate
    sys.exit(f"cannot find {MAP_REL} from cwd={cwd} or {candidate}")


def _ident_re(symbol: str) -> re.Pattern[str]:
    cached = _IDENT_RE_CACHE.get(symbol)
    if cached is None:
        cached = re.compile(r"(?<![\w])" + re.escape(symbol) + r"(?![\w])")
        _IDENT_RE_CACHE[symbol] = cached
    return cached


def _symbol_lines(text: str, symbol: str) -> list[int]:
    pat = _ident_re(symbol)
    return [i for i, line in enumerate(text.splitlines(), 1) if pat.search(line)]


def _looks_like_repo_path(raw: str) -> bool:
    if not raw or "..." in raw:
        return False
    if raw.startswith(("http://", "https://", "mailto:", "<", "/")):
        return False
    stripped = raw.lstrip("./")
    return stripped.startswith(_REPO_PREFIXES) or any(
        raw.startswith(p) for p in _REPO_PREFIXES
    )


def _to_repo_rel(root: Path, map_path: Path, raw: str) -> Path | None:
    target = raw.split("#", 1)[0].strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    if " " in target:
        target = target.split(" ", 1)[0]
    if not target or "..." in target:
        return None
    if target.startswith(("http://", "https://", "mailto:", "<", "/")):
        return None
    if target.startswith("."):
        dest = (map_path.parent / target)
    elif _looks_like_repo_path(target):
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


def _parse_map(root: Path, map_path: Path) -> tuple[dict[Path, set[int]], list[str]]:
    """Return {repo-rel path: cited line numbers} and parse notes."""
    text = map_path.read_text(encoding="utf-8")
    body = _FENCE_RE.sub("", text)
    cited: dict[Path, set[int]] = {}
    notes: list[str] = []

    def add(rel: Path | None, line: int | None = None) -> None:
        if rel is None:
            return
        cited.setdefault(rel, set())
        if line is not None and line > 0:
            cited[rel].add(line)

    for raw in _LINK_RE.findall(body):
        target = raw.strip()
        line = None
        # ](path/file.cpp:123) — rare, but keep line numbers checkable.
        m = re.search(r":(\d+)$", target)
        if m and re.search(r"\.\w+:\d+$", target):
            line = int(m.group(1))
            target = target[: m.start()]
        add(_to_repo_rel(root, map_path, target), line)

    for match in _TICK_PATH_RE.finditer(body):
        raw, line_s = match.group(1), match.group(2)
        add(_to_repo_rel(root, map_path, raw), int(line_s) if line_s else None)

    # Filename:line leftovers (e.g. WriterHistory.cpp:208) mapped by suffix.
    for match in _FILE_LINE_RE.finditer(body):
        name = match.group("name")
        line = int(match.group("line"))
        rel = _to_repo_rel(root, map_path, name) if _looks_like_repo_path(name) else None
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


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def render(root: Path | None = None) -> tuple[str, int]:
    root = (root or _repo_root()).resolve()
    map_path = root / MAP_REL
    lines = [
        "# check_source_map (wiki3 §13.2)",
        "",
        f"- **map:** `{MAP_REL}`",
        "",
    ]
    if not map_path.is_file():
        lines.append(f"FAIL: map missing: `{MAP_REL}`")
        lines.append("")
        return "\n".join(lines), 1

    cited, notes = _parse_map(root, map_path)
    if not cited:
        lines.append("FAIL: no in-repo paths extracted from the source map")
        lines.append("")
        return "\n".join(lines), 1

    failures: list[str] = []
    warnings: list[str] = []
    warnings.extend(notes)
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
        allowlisted = SYMBOL_ALLOWLIST.get(key)
        if not allowlisted:
            continue
        text = _read(abs_path)
        cited_lines = cited[rel]
        for symbol in allowlisted:
            hits = _symbol_lines(text, symbol)
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

    lines.append("")
    lines.append(f"- **cited paths:** {len(cited)}")
    lines.append(f"- **paths on disk:** {ok_paths}")
    lines.append(f"- **allowlisted symbols ok:** {symbol_ok}")
    lines.append(f"- **warnings:** {len(warnings)}")
    lines.append("")

    if warnings:
        lines.append("Warnings (exit 0 unless a FAIL remains):")
        for item in warnings:
            lines.append(f"- {item}")
        lines.append("")

    if failures:
        lines.append("FAIL:")
        for item in failures:
            lines.append(f"- {item}")
        lines.append("")
        lines.append(
            "File or allowlisted symbol is gone. Fix the map path "
            "(docs-only) or restore the citation. Exit 1."
        )
        lines.append("")
        return "\n".join(lines), 1

    lines.append(
        "Source map healthy: cited in-repo paths exist and allowlisted "
        "symbols still appear. Stale line numbers warn only. Exit 0."
    )
    lines.append("")
    return "\n".join(lines), 0


def main() -> int:
    text, code = render()
    sys.stdout.write(text)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
