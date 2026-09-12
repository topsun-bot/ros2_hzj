#!/usr/bin/env python3
"""Assert Executor/WaitSet/callback map still points at real files (wiki3 §13).

Vanilla box (no ROS): exit 0 when the map is healthy.
Parses only docs/architecture/feishu-executor-waitset.md — not the rest of docs/.
No extra dependencies. Style follows scripts/check_source_map.py / prove_rmw.py.

Stale line numbers: WARN + exit 0 if the symbol still exists.
Missing file, missing allowlisted symbol, missing marker/URL,
or a vendored rcl/rclcpp/rclpy tree: FAIL (exit 1).

Does not invent latencies, percentiles, or risk scores.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys


MAP_REL = Path("docs/architecture/feishu-executor-waitset.md")

REQUIRED_DOCS = (
    MAP_REL,
    Path("docs/architecture/ros2-source-map.md"),
    Path("docs/architecture/feishu-middleware-adr.md"),
    Path("docs/architecture/latency-attribution.md"),
    Path("scripts/prove_rmw.py"),
    Path("scripts/check_source_map.py"),
)

# Identity claims — not latency. Exact substrings the map must keep.
DOC_MARKERS = (
    "WaitSet",
    "rmw_wait",
    "rmw_take",
    "Humble",
    "rclcpp",
    "rclpy",
    "不在 vendor",
    "Not Feishu field proof",
    "rmw_fastrtps_cpp",
    "域 **42**",
    "域 **0**",
    "dds_waitset",
    "on_data_available",
    "SingleThreadedExecutor",
    "§9.4",
)

FEISHU_URLS = (
    "https://topsunhzj.feishu.cn/wiki/N0Xaw1vsdiXRD4km9Jvc8kHynBf",
    "https://topsunhzj.feishu.cn/wiki/XKDbw7blLieO4ykCRgLcUCJKnXe",
    "https://topsunhzj.feishu.cn/docx/SrokdQU4DovvdAxutNDcXByMn5e",
)

# Humble client libraries must stay out of vendor/.
ABSENT_VENDOR_TREES = (
    Path("vendor/rcl"),
    Path("vendor/rclcpp"),
    Path("vendor/rclpy"),
)

# Well-known wait/take/callback symbols. Checked only if that file is cited.
SYMBOL_ALLOWLIST: dict[str, tuple[str, ...]] = {
    "vendor/rmw/rmw/include/rmw/rmw.h": ("rmw_wait", "rmw_take"),
    "vendor/rmw_fastrtps/rmw_fastrtps_cpp/src/rmw_wait.cpp": ("rmw_wait",),
    "vendor/rmw_fastrtps/rmw_fastrtps_shared_cpp/src/rmw_wait.cpp": (
        "__rmw_wait",
        "get_first_untaken_info",
    ),
    "vendor/rmw_fastrtps/rmw_fastrtps_shared_cpp/src/rmw_take.cpp": ("__rmw_take",),
    "vendor/Fast-DDS/src/cpp/fastdds/core/condition/WaitSet.cpp": ("WaitSet::wait",),
    "vendor/Fast-DDS/src/cpp/fastdds/core/condition/WaitSetImpl.cpp": (
        "WaitSetImpl::wait",
    ),
    "vendor/rmw_cyclonedds/rmw_cyclonedds_cpp/src/rmw_node.cpp": (
        "rmw_wait",
        "dds_waitset_attach",
        "rmw_take",
    ),
    "vendor/CycloneDDS/src/core/ddsc/src/dds_waitset.c": (
        "dds_waitset_attach",
        "dds_waitset_wait",
    ),
    "vendor/CycloneDDS/src/core/ddsc/src/dds_read.c": ("dds_take",),
    "dimos_bridge/dimos/protocol/pubsub/impl/ddspubsub.py": ("on_data_available",),
    "dimos_bridge/dimos/protocol/pubsub/impl/rospubsub.py": (
        "SingleThreadedExecutor",
    ),
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
        dest = map_path.parent / target
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
        m = re.search(r":(\d+)$", target)
        if m and re.search(r"\.\w+:\d+$", target):
            line = int(m.group(1))
            target = target[: m.start()]
        add(_to_repo_rel(root, map_path, target), line)

    for match in _TICK_PATH_RE.finditer(body):
        raw, line_s = match.group(1), match.group(2)
        add(_to_repo_rel(root, map_path, raw), int(line_s) if line_s else None)

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
        "# check_executor_map (wiki3 §13 wait→callback)",
        "",
        f"- **map:** `{MAP_REL}`",
        "",
    ]
    failures: list[str] = []
    warnings: list[str] = []

    for rel in REQUIRED_DOCS:
        path = root / rel
        key = rel.as_posix()
        if path.is_file():
            lines.append(f"- **ok file:** `{key}`")
        else:
            failures.append(f"missing file `{key}`")
            lines.append(f"- **FAIL missing:** `{key}`")

    for rel in ABSENT_VENDOR_TREES:
        path = root / rel
        key = rel.as_posix()
        if path.exists():
            failures.append(f"Humble client tree must not be vendored: `{key}`")
            lines.append(f"- **FAIL vendored:** `{key}`")
        else:
            lines.append(f"- **ok absent:** `{key}` (Humble rcl* not in vendor)")

    if not map_path.is_file():
        lines.append("")
        lines.append("FAIL: executor map missing")
        lines.append("")
        return "\n".join(lines), 1

    text = _read(map_path)
    missing_markers = [m for m in DOC_MARKERS if m not in text]
    if missing_markers:
        joined = ", ".join(missing_markers)
        failures.append(f"map missing marker(s): {joined}")
        lines.append(f"- **FAIL markers:** `{MAP_REL}` (need {joined})")
    else:
        lines.append(f"- **ok markers:** {len(DOC_MARKERS)} identity strings")

    missing_urls = [u for u in FEISHU_URLS if u not in text]
    if missing_urls:
        failures.append("map missing Feishu URL(s)")
        for url in missing_urls:
            lines.append(f"- **FAIL Feishu URL:** `{url}`")
    else:
        lines.append(f"- **ok Feishu URLs:** {len(FEISHU_URLS)}")

    cited, notes = _parse_map(root, map_path)
    warnings.extend(notes)
    if not cited:
        failures.append("no in-repo paths extracted from the executor map")
        lines.append("- **FAIL:** no in-repo paths extracted")

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
        file_text = _read(abs_path)
        cited_lines = cited[rel]
        for symbol in allowlisted:
            hits = _symbol_lines(file_text, symbol)
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

    # Allowlisted files that the map must cite (not just exist on disk).
    cited_keys = {p.as_posix() for p in cited}
    for key in SYMBOL_ALLOWLIST:
        if key not in cited_keys:
            failures.append(f"map does not cite `{key}`")
            lines.append(f"- **FAIL uncited:** `{key}`")

    lines.append("")
    lines.append(f"- **cited paths:** {len(cited)}")
    lines.append(f"- **paths on disk:** {ok_paths}")
    lines.append(f"- **allowlisted symbols ok:** {symbol_ok}")
    lines.append(f"- **warnings:** {len(warnings)}")
    lines.append("- **WaitSet -> callback: mapped**")
    lines.append("")

    if warnings:
        lines.append("Warnings (exit 0 unless a FAIL remains):")
        for item in warnings:
            lines.append(f"- {item}")
        lines.append("")

    lines.extend(
        [
            "Filesystem + identity markers only. This is **not** a latency",
            "measurement, not a percentile, and not Feishu field proof.",
            "Humble rclcpp/rclpy stay out of vendor/. Exit 0 when the map is healthy.",
            "",
        ]
    )

    if failures:
        lines.append("FAIL:")
        for item in failures:
            lines.append(f"- {item}")
        lines.append("")
        lines.append(
            "File, marker, Feishu URL, or allowlisted symbol is gone — or a "
            "Humble rcl* tree appeared under vendor/. Fix the map (docs-only) "
            "or restore the citation. Exit 1."
        )
        lines.append("")
        return "\n".join(lines), 1

    lines.append(
        "Executor map healthy: cited in-repo paths exist, allowlisted "
        "WaitSet/wait/take symbols still appear, Humble rcl* is not vendored. "
        "Stale line numbers warn only. Exit 0."
    )
    lines.append("")
    return "\n".join(lines), 0


def main() -> int:
    text, code = render()
    sys.stdout.write(text)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
