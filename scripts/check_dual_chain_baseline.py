#!/usr/bin/env python3
"""Assert Feishu wiki3 §13(3) dual-chain baseline pointer docs stay honest.

Vanilla box (no ROS): exit 0 when the baseline doc + dual-chain contract
scripts + ADR §13(3) pointer markers are present.
Missing file or expected marker: FAIL (exit 1).
On success print a line containing exactly:
  dual-chain baseline: pointer only (no XML rewrite)
and a line containing exactly:
  same-topology XML tuning is paused
On failure do not print those success markers (including in ok/FAIL
diagnostics).

Does not invent booked percentile tokens (p50 / p90 / p95 / p99 or
"Nth percentile"), including labels next to Chinese text. Policy
words such as 分位数 are allowed.
Does not prove fastdds.xml / SCOREBOARD contents are unchanged —
those files are existence-only here; the `boundary` job owns the freeze.
chain_b.sh must `unset CYCLONEDDS_URI` (same as load.py CHAIN_B_UNSET)
and must not `export CYCLONEDDS_URI=`.
config/env/load.py is the single executable source of truth: this gate
imports it and cross-checks its CHAIN_A/CHAIN_B values against the literal
shell export copies and the dimos_bridge/dual_chain_env.py thin wrapper,
and asserts importing load.py / the wrapper does not mutate os.environ.
Style follows scripts/check_unitree_cyclone_swap.py / check_risk_matrix.py.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import re

from _freeze_paths import (
    FASTDDS_XML_REL as XML_REL,
    SCOREBOARD_EXISTENCE_NOTE,
    SCOREBOARD_REL,
    XML_EXISTENCE_NOTE,
)
from _repo import emit_render, repo_root, read_utf8


BASELINE_REL = Path("docs/architecture/feishu-dual-chain-baseline.md")
ADR_REL = Path("docs/architecture/feishu-middleware-adr.md")
CHAIN_A_REL = Path("config/env/chain_a.sh")
CHAIN_B_REL = Path("config/env/chain_b.sh")
R0_REL = Path("docs/architecture/ros2-dds-r0-interface-freeze.md")
MAP_REL = Path("docs/architecture/ros2-source-map.md")
SWAP_REL = Path("docs/architecture/unitree-sdk2-dds-swap.md")

SUCCESS_MARKER = "dual-chain baseline: pointer only (no XML rewrite)"
PAUSED_MARKER = "same-topology XML tuning is paused"
MAP_VERDICT = "map≠reproduce"
NO_REWRITE = "no XML rewrite"

# Contiguous phrases so a lone "pointer" / "blocked" / "Hold" cannot
# keep this gate green. Paused success phrase is checked separately so
# a FAIL report does not echo it. Not scores, not percentiles.
_BASELINE_MARKERS = (
    "§13",
    "rmw_fastrtps_cpp",
    "ROS_DOMAIN_ID=42",
    "chain_a.sh",
    "fastdds.xml",
    "只读",
    "rmw_cyclonedds_cpp",
    "域 0",
    "chain_b.sh",
    "CYCLONEDDS_URI",
    "SCOREBOARD",
    "pointer only",
    NO_REWRITE,
    "STATUS: blocked",
    "cross-host",
    "three-chain",
    MAP_VERDICT,
    "drop-in FAIL",
    "0.10.2",
    "11.0.1",
    "派生自",
    "Not Feishu field proof",
    "《3》",
    "《4》",
    "《5》",
    "《6》",
    "Hold",
)

# ADR §13(3) must keep the no-rewrite contract and point at this cut.
_ADR_MARKERS = (
    "FastDDS + Cyclone",
    "不重写 XML",
    "SCOREBOARD",
    "feishu-dual-chain-baseline.md",
)

_EXPORT_CHAIN_A = (
    re.compile(r"(?m)^\s*export\s+RMW_IMPLEMENTATION=rmw_fastrtps_cpp\s*$"),
    re.compile(r"(?m)^\s*export\s+ROS_DOMAIN_ID=42\s*$"),
    re.compile(
        r"(?m)^\s*export\s+FASTRTPS_DEFAULT_PROFILES_FILE=.*config/fastdds\.xml"
    ),
)
_EXPORT_CHAIN_B = (
    re.compile(r"(?m)^\s*export\s+RMW_IMPLEMENTATION=rmw_cyclonedds_cpp\s*$"),
    re.compile(r"(?m)^\s*export\s+ROS_DOMAIN_ID=0\s*$"),
)

# Booked tokens only. ASCII lookarounds so 链A的p99=… still matches;
# Python \b treats CJK as word chars. Policy words (分位数) are OK.
_PERCENTILE_RE = re.compile(
    r"(?i)(?:(?<![A-Za-z0-9_])p(?:50|90|95|99(?:\.\d+)?)(?![A-Za-z0-9_.])|"
    r"(?:50|90|95|99)(?:st|nd|rd|th)\s+percentile)"
)
_EXPORT_CYCLONE_URI_RE = re.compile(
    r"(?m)^\s*export\s+CYCLONEDDS_URI\s*="
)
_UNSET_CYCLONE_URI_RE = re.compile(r"(?m)^\s*unset\s+CYCLONEDDS_URI\s*$")

# Single executable source of truth for the dual-chain env contract
# (modernization plan Step 4). chain_a.sh / chain_b.sh carry literal
# export copies (anchored above and by the boundary job) and
# dimos_bridge/dual_chain_env.py is an importlib thin wrapper; this gate
# cross-checks that all three still agree with load.py, and that merely
# importing load.py does not write os.environ.
LOAD_PY_REL = Path("config/env/load.py")
WRAPPER_REL = Path("dimos_bridge/dual_chain_env.py")
_EXPECTED_CHAIN_A = {
    "RMW_IMPLEMENTATION": "rmw_fastrtps_cpp",
    "ROS_DOMAIN_ID": "42",
}
_EXPECTED_CHAIN_B = {
    "RMW_IMPLEMENTATION": "rmw_cyclonedds_cpp",
    "ROS_DOMAIN_ID": "0",
}
_ENV_WATCH_KEYS = (
    "RMW_IMPLEMENTATION",
    "ROS_DOMAIN_ID",
    "FASTRTPS_DEFAULT_PROFILES_FILE",
    "CYCLONEDDS_URI",
)
_SHELL_EXPORT_RE = re.compile(r"(?m)^\s*export\s+([A-Za-z_]\w*)=(.*?)\s*$")


def _missing_exports(text: str, patterns: tuple[re.Pattern[str], ...]) -> list[str]:
    missing: list[str] = []
    for pattern in patterns:
        if pattern.search(text) is None:
            missing.append(pattern.pattern)
    return missing


def _load_py_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module at {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _shell_exports(text: str) -> dict[str, str]:
    """Parse literal `export KEY=VALUE` lines; strip one quoting layer."""
    exports: dict[str, str] = {}
    for match in _SHELL_EXPORT_RE.finditer(text):
        value = match.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        exports[match.group(1)] = value
    return exports


# Contract keys compared verbatim between the literal shell `export` copies
# and load.py. FASTRTPS_DEFAULT_PROFILES_FILE is chain-A-only and compared as
# a resolved path, so it stays out of this shared key tuple.
_SHELL_CROSS_KEYS = ("RMW_IMPLEMENTATION", "ROS_DOMAIN_ID")


def _shell_key_drifts(
    shell_exports: dict[str, str],
    chain: dict[str, str],
    keys: tuple[str, ...] = _SHELL_CROSS_KEYS,
) -> list[str]:
    """Report contract keys whose literal shell value differs from load.py."""
    return [
        f"{key}: shell={shell_exports.get(key)!r} load.py={chain.get(key)!r}"
        for key in keys
        if shell_exports.get(key) != chain.get(key)
    ]


def render(root: Path | None = None) -> tuple[str, int]:
    root = (root or repo_root(BASELINE_REL, ADR_REL)).resolve()
    lines = [
        "# check_dual_chain_baseline (wiki3 §13(3) FastDDS + Cyclone)",
        "",
    ]
    failures: list[str] = []

    # XML / SCOREBOARD: existence only. Content freeze is the `boundary` job.
    required = (
        (BASELINE_REL, _BASELINE_MARKERS, "dual-chain contracts + Hold + pointer-only"),
        (ADR_REL, _ADR_MARKERS, "§13(3) row pointer; no XML rewrite"),
        (CHAIN_A_REL, (), "opened; export assignments checked separately"),
        (CHAIN_B_REL, (), "opened; export assignments + no URI export"),
        (R0_REL, ("Hold",), "dual-chain R0 freeze exists"),
        (MAP_REL, ("vendor", "不是复现"), "three-chain map exists (not a reproduce)"),
        (SWAP_REL, ("drop-in FAIL", "0.10.2", "11.0.1"), "Unitree 0.10.2 vs vendor 11.0.1"),
        (XML_REL, (), XML_EXISTENCE_NOTE),
        (SCOREBOARD_REL, (), SCOREBOARD_EXISTENCE_NOTE),
    )
    existence_only = {XML_REL, SCOREBOARD_REL}
    texts: dict[Path, str] = {}
    for rel, markers, hint in required:
        path = root / rel
        key = rel.as_posix()
        if not path.is_file():
            failures.append(f"missing file `{key}`")
            lines.append(f"- **FAIL missing:** `{key}`")
            continue
        # XML / SCOREBOARD stay existence-only: their contents are never read
        # here (the boundary job owns the content freeze), so they skip marker
        # checks and fall through to the single ok-file render below.
        if rel not in existence_only:
            text = read_utf8(path)
            texts[rel] = text
            missing_markers = [m for m in markers if m not in text]
            if missing_markers:
                joined = ", ".join(missing_markers)
                failures.append(f"`{key}` missing marker(s): {joined}")
                lines.append(f"- **FAIL markers:** `{key}` (need {joined})")
                continue
        extra = f" ({hint})" if hint else ""
        lines.append(f"- **ok file:** `{key}`{extra}")

    baseline_text = texts.get(BASELINE_REL)
    if baseline_text is not None:
        if PAUSED_MARKER in baseline_text:
            lines.append("- **ok paused phrase:** present in baseline doc")
        else:
            failures.append("baseline doc missing contiguous same-topology paused phrase")
            lines.append("- **FAIL paused:** need same-topology paused phrase")
        if MAP_VERDICT in baseline_text:
            lines.append("- **ok three-chain phrase:** present")
        else:
            failures.append("baseline doc missing contiguous three-chain map verdict")
            lines.append("- **FAIL map:** need three-chain map verdict")
        if NO_REWRITE in baseline_text:
            lines.append("- **ok no-rewrite phrase:** present")
        else:
            failures.append("baseline doc missing contiguous no-XML-rewrite phrase")
            lines.append("- **FAIL rewrite:** need no-XML-rewrite phrase")
        if "pointer only" in baseline_text:
            lines.append("- **ok SCOREBOARD phrase:** pointer-only present")
        else:
            failures.append("baseline doc missing SCOREBOARD pointer-only phrase")
            lines.append("- **FAIL pointer:** need pointer-only phrase")
        invented = _PERCENTILE_RE.findall(baseline_text)
        if invented:
            failures.append(
                "baseline doc invents booked percentile token(s): "
                + ", ".join(sorted(set(invented)))
            )
            lines.append("- **FAIL percentiles:** do not invent booked pNN tokens")
        else:
            lines.append("- **ok no invented booked percentile tokens**")

    chain_a_text = texts.get(CHAIN_A_REL)
    if chain_a_text is not None:
        missing_a = _missing_exports(chain_a_text, _EXPORT_CHAIN_A)
        if missing_a:
            failures.append("chain_a.sh missing anchored export assignment(s)")
            lines.append("- **FAIL chain A:** need anchored export assignments")
        else:
            lines.append("- **ok chain A:** anchored export assignments")

    chain_b_text = texts.get(CHAIN_B_REL)
    if chain_b_text is not None:
        missing_b = _missing_exports(chain_b_text, _EXPORT_CHAIN_B)
        if missing_b:
            failures.append("chain_b.sh missing anchored export assignment(s)")
            lines.append("- **FAIL chain B:** need anchored export assignments")
        else:
            lines.append("- **ok chain B:** anchored export assignments")
        if _EXPORT_CYCLONE_URI_RE.search(chain_b_text):
            failures.append("chain_b.sh exports CYCLONEDDS_URI (helper must not set it)")
            lines.append("- **FAIL chain B:** helper must not export CYCLONEDDS_URI")
        elif _UNSET_CYCLONE_URI_RE.search(chain_b_text) is None:
            failures.append("chain_b.sh missing anchored unset CYCLONEDDS_URI")
            lines.append("- **FAIL chain B:** need anchored unset CYCLONEDDS_URI")
        else:
            lines.append(
                "- **ok chain B:** helper unsets CYCLONEDDS_URI "
                "(aligns with load.py CHAIN_B_UNSET)"
            )

    # Single source of truth (modernization plan Step 4): load.py values
    # must equal the literal shell export copies and the thin wrapper's
    # re-exports; importing either module must not mutate os.environ.
    load_path = root / LOAD_PY_REL
    wrapper_path = root / WRAPPER_REL
    if not load_path.is_file():
        failures.append(f"missing file `{LOAD_PY_REL.as_posix()}`")
        lines.append(f"- **FAIL missing:** `{LOAD_PY_REL.as_posix()}`")
    else:
        before = {k: os.environ.get(k) for k in _ENV_WATCH_KEYS}
        try:
            env_mod = _load_py_module("ros2_hzj_env_load_gate", load_path)
        except Exception as exc:  # gate must report, not crash
            failures.append(f"cannot import load.py: {exc}")
            lines.append("- **FAIL env truth:** cannot import config/env/load.py")
            env_mod = None
        wmod = None
        if env_mod is not None:
            if not wrapper_path.is_file():
                failures.append(f"missing file `{WRAPPER_REL.as_posix()}`")
                lines.append(f"- **FAIL missing:** `{WRAPPER_REL.as_posix()}`")
            else:
                try:
                    wmod = _load_py_module("ros2_hzj_env_wrapper_gate", wrapper_path)
                except Exception as exc:  # gate must report, not crash
                    failures.append(f"cannot import dual_chain_env.py: {exc}")
                    lines.append(
                        "- **FAIL env wrapper:** cannot import "
                        "dimos_bridge/dual_chain_env.py"
                    )
        after = {k: os.environ.get(k) for k in _ENV_WATCH_KEYS}

        chain_a = dict(getattr(env_mod, "CHAIN_A", {})) if env_mod else {}
        chain_b = dict(getattr(env_mod, "CHAIN_B", {})) if env_mod else {}
        b_unset = tuple(getattr(env_mod, "CHAIN_B_UNSET", ())) if env_mod else ()

        if env_mod is not None:
            truth_bad: list[str] = []
            for key, want in _EXPECTED_CHAIN_A.items():
                if chain_a.get(key) != want:
                    truth_bad.append(
                        f"CHAIN_A[{key}]={chain_a.get(key)!r} (want {want!r})"
                    )
            for key, want in _EXPECTED_CHAIN_B.items():
                if chain_b.get(key) != want:
                    truth_bad.append(
                        f"CHAIN_B[{key}]={chain_b.get(key)!r} (want {want!r})"
                    )
            profiles = chain_a.get("FASTRTPS_DEFAULT_PROFILES_FILE", "")
            if not profiles.endswith(XML_REL.as_posix()) or not Path(
                profiles
            ).is_file():
                truth_bad.append(
                    "CHAIN_A profiles file does not resolve to config/fastdds.xml"
                )
            if "CYCLONEDDS_URI" not in b_unset:
                truth_bad.append("CHAIN_B_UNSET missing CYCLONEDDS_URI")
            if before != after:
                changed = [k for k in _ENV_WATCH_KEYS if before[k] != after[k]]
                truth_bad.append(
                    "import mutated os.environ: " + ", ".join(changed)
                )
            if truth_bad:
                failures.append("load.py env contract drift: " + "; ".join(truth_bad))
                lines.append(
                    "- **FAIL env truth:** load.py drifted from the dual-chain "
                    "contract or import mutated os.environ"
                )
            else:
                lines.append(
                    "- **ok env truth:** load.py chain A rmw_fastrtps_cpp/42 + "
                    "config/fastdds.xml; chain B rmw_cyclonedds_cpp/0; "
                    "CYCLONEDDS_URI in CHAIN_B_UNSET; import leaves os.environ "
                    "unchanged"
                )

        if env_mod is not None and chain_a_text is not None:
            sh_a = _shell_exports(chain_a_text)
            a_bad = _shell_key_drifts(sh_a, chain_a)
            sh_profiles = sh_a.get(
                "FASTRTPS_DEFAULT_PROFILES_FILE", ""
            ).replace("${_ROS2_HZJ_ROOT}", str(root))
            if Path(sh_profiles) != Path(
                chain_a.get("FASTRTPS_DEFAULT_PROFILES_FILE", "")
            ):
                a_bad.append("FASTRTPS_DEFAULT_PROFILES_FILE path mismatch")
            if a_bad:
                failures.append(
                    "chain_a.sh / load.py CHAIN_A drift: " + "; ".join(a_bad)
                )
                lines.append(
                    "- **FAIL env cross-check:** chain_a.sh != load.py CHAIN_A"
                )
            else:
                lines.append(
                    "- **ok env cross-check:** chain_a.sh exports match "
                    "load.py CHAIN_A"
                )

        if env_mod is not None and chain_b_text is not None:
            sh_b = _shell_exports(chain_b_text)
            b_bad = _shell_key_drifts(sh_b, chain_b)
            if b_bad:
                failures.append(
                    "chain_b.sh / load.py CHAIN_B drift: " + "; ".join(b_bad)
                )
                lines.append(
                    "- **FAIL env cross-check:** chain_b.sh != load.py CHAIN_B"
                )
            else:
                lines.append(
                    "- **ok env cross-check:** chain_b.sh exports match "
                    "load.py CHAIN_B"
                )

        if env_mod is not None and wmod is not None:
            wrapper_ok = (
                dict(getattr(wmod, "CHAIN_A", {})) == chain_a
                and dict(getattr(wmod, "CHAIN_B", {})) == chain_b
                and wmod.chain_a_env() == dict(chain_a)
                and wmod.chain_b_env() == dict(chain_b)
            )
            if wrapper_ok:
                lines.append(
                    "- **ok env wrapper:** dimos_bridge/dual_chain_env.py "
                    "re-exports match load.py"
                )
            else:
                failures.append("dual_chain_env.py wrapper drifted from load.py")
                lines.append(
                    "- **FAIL env wrapper:** re-exports != load.py"
                )

    lines.append("")
    lines.extend(
        [
            "Filesystem + contract / Hold markers only. This is **not** a",
            "latency measurement, not a booked-percentile reprint, and not",
            "Feishu field proof. SCOREBOARD is the current-best pointer;",
            "this script does not copy its numbers. fastdds.xml /",
            "SCOREBOARD are existence-only in this script; the boundary",
            "job owns the content freeze. Cross-host stays blocked.",
            "three-chain stays map-only. Unitree 0.10.2 vs vendor 11.0.1",
            "stays drop-in FAIL. 《3》–《6》 stay Hold. This cut does not",
            "rewrite XML. chain_b.sh unsets CYCLONEDDS_URI.",
            "",
        ]
    )

    if failures:
        lines.append("FAIL:")
        for item in failures:
            lines.append(f"- {item}")
        lines.append("")
        lines.append(
            "Required dual-chain baseline pointer, contract marker, "
            "no-XML-rewrite phrase, SCOREBOARD pointer-only, cross-host "
            "blocked, or 《3》–《6》 Hold marker is gone. Restore the "
            "docs (no XML) or the marker. Exit 1."
        )
        lines.append("")
        return "\n".join(lines), 1

    lines.append(f"- **{SUCCESS_MARKER}**")
    lines.append(f"- **{PAUSED_MARKER}**")
    lines.append("")
    lines.append(
        "Dual-chain baseline healthy: chain A/B contracts exist, this cut "
        "does not rewrite XML, SCOREBOARD stays pointer-only, cross-host "
        "is blocked, and 《3》–《6》 stay Hold. Exit 0."
    )
    lines.append("")
    return "\n".join(lines), 0


def main() -> int:
    return emit_render(render())


if __name__ == "__main__":
    raise SystemExit(main())
