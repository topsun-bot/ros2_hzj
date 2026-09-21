#!/usr/bin/env python3
"""Negative/contract self-test for the promptfoo local-script provider (#33).

Context
-------
`evals/localScriptProvider.mjs` is the custom promptfoo provider that backs
every eval case (#12-#32): it splits the prompt on whitespace into argv and
runs them with python3, returning stdout as `output`; a non-zero exit must set
`error` so promptfoo marks the case failed. All of the negative self-tests
(#18-#32) rely on that last behavior -- a guard/tool that exits 1 only turns
red in promptfoo because the provider propagates the failure as `error`.

That contract itself had no executable regression. If the provider were
hollowed out -- an empty/whitespace prompt silently succeeding, a non-zero
exit being swallowed (no `error`), a missing script reported as success, or
stderr from a successful command leaking into `output` (which would corrupt
the `contains` assertions and stdout fingerprints) -- the whole negative-eval
suite could lose its teeth while still printing green.

The provider is a Node ESM module that hardcodes `python3`, so it cannot be
invoked directly by the python3-based provider. This script (pure standard
library) writes a small Node harness into a tempdir; the harness imports the
real provider via an absolute file:// URL, creates throwaway python fixtures
(also in the tempdir), exercises every branch, and additionally defines a
"blind" provider that swallows non-zero exits for the mutation check. It emits
one JSON document between sentinels on stdout; this script parses and asserts
it. Nothing in the repo is edited and no fixture is created in-tree. Not a CI
gate (not in run_all_gates.GATES, not enumerated by CI structure, no ci.yml
wiring). Requires `node`, which promptfoo itself requires.

Scenarios (real behavior first captured verbatim via a /tmp node probe,
node v22):
  * 3 negative: an empty prompt must return an `empty prompt` error with empty
    output; a command exiting 1 must return `error` containing
    "exited with code 1" and output carrying BOTH stdout and stderr; a missing
    script (python3 exits 2) must return `error` containing "exited with code
    2", not success;
  * 2 non-flag: a whitespace-only prompt must hit the same empty-prompt error
    (no whitespace bypass); a command that exits 0 but writes to stderr must
    yield NO error and an output containing stdout ONLY (stderr must not leak
    into `output` and perturb contains/fingerprint assertions);
  * 1 healthy: id() == "local-script" and an exit-0 command with a CLI arg
    (`config/env/load.py print-a`) returns no error with the Chain A contract
    on stdout, proving argv whitespace-splitting and cwd=repoRoot;
  * 1 mutation: a blind provider whose catch returns no error reports an
    exit-1 command as success (the check observes that miss), while the real
    provider reports the error -- proving this test distinguishes a provider
    that swallows failures.

Round-43 timeout-budget hardening (the provider previously used a fixed 30s
``execFileSync`` timeout; under heavy host load the 15-process fingerprint case
could exceed it and be killed, surfacing as a provider-level [ERROR] with 0
assertion failures):
  * 1 extra negative: with LOCAL_SCRIPT_TIMEOUT_MS=250 a script that sleeps
    past the budget must return an `error` labeled "code timeout" (node kills
    it with ETIMEDOUT / SIGTERM), distinct from an active non-zero exit; after
    the override is deleted a fast command succeeds again (env restored);
  * 1 timeout-budget contract (static): the default DEFAULT_TIMEOUT_MS is at
    least 60s (no regression to the too-tight 30s), the LOCAL_SCRIPT_TIMEOUT_MS
    override is wired, and the ETIMEDOUT/SIGTERM timeout classification exists.
    A non-numeric override falls back to the default.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PROVIDER_PATH = REPO_ROOT / "evals" / "localScriptProvider.mjs"

SUCCESS_MARKER = "local-script provider selftest: PASS"

# Node harness: imports the real provider, runs every branch against tempdir
# python fixtures, builds a blind (failure-swallowing) provider for the
# mutation check, and prints one JSON document between sentinels.
_HARNESS = r"""
import { pathToFileURL } from 'node:url';
import path from 'node:path';
import os from 'node:os';
import fs from 'node:fs';

const provPath = process.argv[2];
const mod = await import(pathToFileURL(provPath).href);
const provider = new mod.default({});

const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'hzj-prov-selftest-'));
const failPy = path.join(dir, 'fail.py');
fs.writeFileSync(failPy, "import sys;sys.stdout.write('OUT-LEAD\\n');sys.stderr.write('ERR-DETAIL\\n');sys.exit(1)\n");
const okStderrPy = path.join(dir, 'okstderr.py');
fs.writeFileSync(okStderrPy, "import sys;sys.stdout.write('CLEAN-OUT\\n');sys.stderr.write('NOISE-STDERR\\n');sys.exit(0)\n");
const missingPy = path.join(dir, 'does_not_exist.py');
const slowPy = path.join(dir, 'slow.py');
fs.writeFileSync(slowPy, "import time;time.sleep(1.2)\n");

const run = async (prompt) => {
  const r = await provider.callApi(prompt);
  return { hasError: !!(r.error), output: (r.output === undefined ? null : r.output), error: r.error ? String(r.error) : null };
};

const results = {
  id: provider.id(),
  empty: await run(''),
  whitespace: await run('   \t '),
  healthy: await run('config/env/load.py print-a'),
  exit1: await run(failPy),
  missing: await run(missingPy),
  okStderr: await run(okStderrPy),
};

// Blind provider: update-shaped but the catch deliberately returns no error,
// reproducing a provider that swallows non-zero exits.
class BlindProvider {
  async callApi(prompt) {
    const cp = await import('node:child_process');
    const here = path.dirname(new URL(pathToFileURL(provPath).href).pathname);
    const repoRoot = path.resolve(here, '..');
    const argv = String(prompt || '').trim().split(/\s+/).filter(Boolean);
    try {
      const stdout = cp.execFileSync('python3', argv, { cwd: repoRoot, timeout: 30000, encoding: 'utf8', env: { ...process.env } });
      return { output: stdout };
    } catch (e) {
      return { output: (e && e.stdout) ? String(e.stdout) : '' }; // no error -> miss
    }
  }
}
const blind = new BlindProvider();
const blindRes = await blind.callApi(failPy);
results.blindExit1 = { hasError: !!(blindRes.error), output: blindRes.output };
results.realExit1HasError = results.exit1.hasError;

// Timeout branch (run last): shrink the budget via env so a slow child is
// killed fast, then restore the env so the override cannot leak. node kills
// an over-budget child with ETIMEDOUT / SIGTERM and no numeric status.
process.env.LOCAL_SCRIPT_TIMEOUT_MS = '250';
results.timeout = await run(slowPy);
delete process.env.LOCAL_SCRIPT_TIMEOUT_MS;
results.envRestored = !('LOCAL_SCRIPT_TIMEOUT_MS' in process.env);
results.afterOverrideFast = await run(okStderrPy);

process.stdout.write('__JSON_BEGIN__\n' + JSON.stringify(results) + '\n__JSON_END__\n');
"""


def _run_harness() -> dict:
    node = shutil.which("node")
    if not node:
        raise AssertionError(
            "node not found on PATH; the local-script provider and promptfoo require node"
        )
    with tempfile.TemporaryDirectory(prefix="hzj-prov-selftest-") as tmp:
        harness = pathlib.Path(tmp) / "harness.mjs"
        harness.write_text(_HARNESS, encoding="utf-8")
        proc = subprocess.run(
            [node, str(harness), str(PROVIDER_PATH)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
    if proc.returncode != 0:
        raise AssertionError(f"node harness exited {proc.returncode}\n{proc.stderr}")
    out = proc.stdout
    begin, end = out.find("__JSON_BEGIN__"), out.find("__JSON_END__")
    assert begin != -1 and end != -1 and end > begin, f"no JSON sentinels in harness output:\n{out}"
    return json.loads(out[begin + len("__JSON_BEGIN__"):end].strip())


def _check_healthy(r: dict) -> None:
    assert r["id"] == "local-script", r["id"]
    h = r["healthy"]
    assert h["hasError"] is False, h
    assert "RMW_IMPLEMENTATION=rmw_fastrtps_cpp" in h["output"], h["output"]
    assert "ROS_DOMAIN_ID=42" in h["output"], h["output"]  # argv split + cwd=repoRoot


def _check_negative_empty(r: dict) -> None:
    e = r["empty"]
    assert e["hasError"] is True, "empty prompt must be an error"
    assert "empty prompt" in (e["error"] or ""), e["error"]
    assert e["output"] == "", "empty prompt output must be the empty string"


def _check_negative_exit1_propagates(r: dict) -> None:
    x = r["exit1"]
    assert x["hasError"] is True, "non-zero exit must set error (negative-eval foundation)"
    assert "exited with code 1" in (x["error"] or ""), x["error"]
    assert "OUT-LEAD" in (x["output"] or ""), x["output"]
    assert "ERR-DETAIL" in (x["output"] or ""), "stderr must be surfaced in output on failure"


def _check_negative_missing_script(r: dict) -> None:
    m = r["missing"]
    assert m["hasError"] is True, "a missing script (python3 exit 2) must be an error"
    assert "exited with code 2" in (m["error"] or ""), m["error"]


def _check_nonflag_whitespace(r: dict) -> None:
    w = r["whitespace"]
    assert w["hasError"] is True, "whitespace-only prompt must not bypass the empty check"
    assert "empty prompt" in (w["error"] or ""), w["error"]


def _check_nonflag_success_stdout_only(r: dict) -> None:
    s = r["okStderr"]
    assert s["hasError"] is False, "exit 0 must not be an error"
    assert "CLEAN-OUT" in (s["output"] or ""), s["output"]
    assert "NOISE-STDERR" not in (s["output"] or ""), \
        "on success, output must be stdout only; stderr must not leak into contains/fingerprint input"


def _check_mutation_blind_swallows(r: dict) -> None:
    assert r["blindExit1"]["hasError"] is False, \
        "sanity: a provider that swallows non-zero exits must report the exit-1 case as no-error"
    assert "OUT-LEAD" in (r["blindExit1"]["output"] or "")
    assert r["realExit1HasError"] is True, \
        "the real provider must report the same exit-1 command as an error"


def _check_negative_timeout(r: dict) -> None:
    x = r["timeout"]
    assert x["hasError"] is True, "an over-budget (killed) command must set error"
    err = x["error"] or ""
    assert "code timeout" in err, f"timeout must be labeled code timeout, got: {err}"
    assert "ETIMEDOUT" in err or "SIGTERM" in err, err
    assert "after 250ms" in err, f"error should state the applied budget, got: {err}"
    # An active exit-1 is still classified as code 1 (timeout hardening must
    # not relabel/soften a real non-zero exit).
    assert "exited with code 1" in (r["exit1"]["error"] or ""), r["exit1"]
    assert r["envRestored"] is True, "LOCAL_SCRIPT_TIMEOUT_MS override must be removed after test"
    after = r["afterOverrideFast"]
    assert after["hasError"] is False and "CLEAN-OUT" in (after["output"] or ""),         "after deleting the override a fast command must succeed on the default budget"


def _check_timeout_budget_contract(_r: dict | None = None) -> None:
    src = PROVIDER_PATH.read_text(encoding="utf-8")
    m = re.search(r"DEFAULT_TIMEOUT_MS\s*=\s*(\d+)", src)
    assert m, "provider must define a named DEFAULT_TIMEOUT_MS constant"
    default_ms = int(m.group(1))
    assert default_ms >= 60000, (
        f"default per-script timeout {default_ms}ms regressed below 60s; the 15-process "
        "fingerprint case needs headroom under host load (was 30s, round 41 flake)"
    )
    assert "LOCAL_SCRIPT_TIMEOUT_MS" in src, "timeout budget must be env-overridable"
    assert "ETIMEDOUT" in src and "SIGTERM" in src, "timeout classification markers missing"
    # Non-numeric / non-positive override must not silently zero the budget.
    assert "Number.isFinite" in src and "> 0" in src, "override validation missing"


def main() -> int:
    try:
        r = _run_harness()
        checks = [
            ("healthy id + exit-0 command with arg", _check_healthy),
            ("negative empty prompt errors", _check_negative_empty),
            ("negative exit-1 propagates error + stdout/stderr", _check_negative_exit1_propagates),
            ("negative missing script errors (code 2)", _check_negative_missing_script),
            ("non-flag whitespace-only still errors", _check_nonflag_whitespace),
            ("non-flag success output is stdout-only", _check_nonflag_success_stdout_only),
            ("mutation blind provider swallows exit-1 vs real reports", _check_mutation_blind_swallows),
            ("negative over-budget command reports code timeout, env restores", _check_negative_timeout),
            ("timeout-budget contract: default >=60s, env override wired", _check_timeout_budget_contract),
        ]
        for label, fn in checks:
            fn(r)
            print(f"  ok {label}")
    except AssertionError as exc:
        print(f"{SUCCESS_MARKER.replace('PASS', 'FAIL')}: {exc}")
        return 1
    print(SUCCESS_MARKER)
    print("4 negative, 2 non-flag, 1 healthy, 1 mutation, 1 timeout-budget contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
