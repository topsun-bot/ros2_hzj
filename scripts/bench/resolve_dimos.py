#!/usr/bin/env python3
"""Locate a DimOS tree that can import ddspubsub / the pytest bench.

Vendored ``dimos_bridge`` keeps ImportError stubs for logging_config, Image,
LCM, etc. Official ``pytest -m tool -k dds`` therefore needs a read-only
``topsun_dimos`` checkout (not a submodule; not pushed).
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

PINNED_SHA = "a5259958db23c8ea6648544ed138eab19726ce93"
UPSTREAM = "https://github.com/topsun-bot/topsun_dimos"


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    return here.parents[2]


def _can_import_dds(root: Path) -> tuple[bool, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    code = (
        "from dimos.protocol.pubsub.impl.ddspubsub import DDS; "  # noqa: E501
        "from dimos.protocol.service.ddsservice import DDSConfig; "
        "print('ok', DDSConfig.model_fields['domain_id'].default)"
    )
    try:
        proc = subprocess.run(
            [sys.executable, "-c", code],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except OSError as exc:
        return False, f"spawn failed: {exc}"
    if proc.returncode == 0 and "ok" in proc.stdout:
        return True, proc.stdout.strip()
    err = (proc.stderr or proc.stdout or "import failed").strip().splitlines()
    return False, err[-1] if err else "import failed"


def _git_sha(root: Path) -> str | None:
    git_dir = root / ".git"
    if not git_dir.exists():
        return None
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
        ).strip()
    except subprocess.CalledProcessError:
        return None


def _clone(dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if (dest / "dimos" / "protocol" / "pubsub" / "impl" / "ddspubsub.py").is_file():
        return dest
    subprocess.check_call(
        ["git", "clone", "--depth", "1", UPSTREAM, str(dest)],
    )
    return dest


def resolve(*, clone: bool = True) -> dict[str, object]:
    repo = _repo_root()
    bridge = repo / "dimos_bridge"
    candidates: list[tuple[str, Path]] = []

    env_root = os.environ.get("TOPSUN_DIMOS", "").strip()
    if env_root:
        candidates.append(("TOPSUN_DIMOS", Path(env_root).expanduser().resolve()))
    candidates.append(("tmp_checkout", Path("/tmp/topsun_dimos")))
    candidates.append(("vendored_bridge", bridge))

    tried: list[dict[str, str]] = []
    for label, path in candidates:
        if not (path / "dimos").is_dir():
            tried.append({"label": label, "path": str(path), "status": "missing"})
            continue
        ok, detail = _can_import_dds(path)
        entry = {"label": label, "path": str(path), "status": "ok" if ok else "import_error", "detail": detail}
        if label == "tmp_checkout" or label == "TOPSUN_DIMOS":
            sha = _git_sha(path)
            if sha:
                entry["git_sha"] = sha
        tried.append(entry)
        if ok:
            source = (
                "temporary topsun_dimos checkout"
                if label != "vendored_bridge"
                else "vendored dimos_bridge"
            )
            return {
                "ok": True,
                "root": str(path),
                "source": source,
                "label": label,
                "git_sha": _git_sha(path),
                "tried": tried,
                "pinned_sha": PINNED_SHA,
            }

    if clone:
        dest = Path("/tmp/topsun_dimos")
        try:
            _clone(dest)
        except subprocess.CalledProcessError as exc:
            return {
                "ok": False,
                "error": f"git clone failed: {exc}",
                "tried": tried,
                "pinned_sha": PINNED_SHA,
            }
        ok, detail = _can_import_dds(dest)
        if ok:
            return {
                "ok": True,
                "root": str(dest),
                "source": "temporary topsun_dimos checkout",
                "label": "tmp_checkout",
                "git_sha": _git_sha(dest),
                "tried": tried,
                "pinned_sha": PINNED_SHA,
            }
        return {
            "ok": False,
            "error": f"checkout imported poorly: {detail}",
            "tried": tried,
            "pinned_sha": PINNED_SHA,
        }

    return {
        "ok": False,
        "error": "no importable DimOS tree (set TOPSUN_DIMOS or allow clone)",
        "tried": tried,
        "pinned_sha": PINNED_SHA,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print JSON on stdout")
    parser.add_argument("--no-clone", action="store_true")
    args = parser.parse_args()
    result = resolve(clone=not args.no_clone)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result.get("ok"):
            print(result["root"])
        else:
            print(result.get("error", "resolve failed"), file=sys.stderr)
            return 1
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
