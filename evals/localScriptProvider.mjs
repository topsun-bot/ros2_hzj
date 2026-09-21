// evals/localScriptProvider.mjs
//
// Custom promptfoo provider, named "local-script".
//
// This repository is a ROS 2 / DDS middleware workspace. The DDS layer has
// no "prompt" concept, so we map the LLM-eval abstraction onto the repo's
// existing gate scripts: the promptfoo "prompt" is, by convention, a path
// (relative to the repo root) to one of the scripts under scripts/, optionally
// followed by whitespace-separated CLI arguments, e.g.
// `config/env/load.py print-a` or `scripts/prove_rmw.py`. We split the prompt
// on whitespace into argv and execute it with python3, capture
// stdout/stderr/exit code, and hand stdout back as the provider "output".
//
// promptfoo loads custom providers by `new Module(config)`, so the default
// export is a class (not a plain object) exposing id() + callApi().
//
// Semantics:
//   * exit code 0   -> no `error` returned; promptfoo treats the case as
//     provider-success. The `contains` assertion in the config then checks
//     the stdout marker (e.g. "Risk matrix healthy").
//   * exit code != 0 -> `error` is set; promptfoo marks the case failed
//     regardless of assertions. stdout+stderr are still returned as
//     `output` so the failure is visible.
//
// No LLM API is called. No network. No secrets.

import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, '..');

// Wall-clock budget for one script. The strictest case is
// `evals/fingerprint_check.py`, which serially spawns the 13 gates plus the
// two `load.py print-*` subcommands (15 python processes). On a host under
// heavy concurrent load (promptfoo concurrency=4 plus other work, observed
// loadavg ~35) that can take longer than the previous fixed 30s, at which
// point node killed an otherwise-correct check and promptfoo recorded a
// provider-level `[ERROR]` with 0 assertion failures. 120s gives a 4x margin
// without weakening any assertion: a real non-zero exit or stdout drift still
// fails exactly as before. Overridable for CI / fast timeout tests via
// LOCAL_SCRIPT_TIMEOUT_MS (positive integer ms).
const DEFAULT_TIMEOUT_MS = 120000;

function resolveTimeoutMs() {
  const raw = Number(process.env.LOCAL_SCRIPT_TIMEOUT_MS);
  return Number.isFinite(raw) && raw > 0 ? Math.floor(raw) : DEFAULT_TIMEOUT_MS;
}

export default class LocalScriptProvider {
  constructor(config = {}) {
    this.config = config;
  }

  id() {
    return 'local-script';
  }

  async callApi(prompt) {
    const command = String(prompt || '').trim();
    // First whitespace-delimited token is the script path; any following
    // tokens are CLI arguments (e.g. `config/env/load.py print-a`).
    const argv = command.split(/\s+/).filter(Boolean);
    if (argv.length === 0) {
      return {
        output: '',
        error: 'local-script: empty prompt (expected a script path, optionally with args)',
      };
    }

    const timeoutMs = resolveTimeoutMs();
    try {
      const stdout = execFileSync('python3', argv, {
        cwd: repoRoot,
        timeout: timeoutMs,
        encoding: 'utf8',
        // Inherit the operator's env. On this host ROS_* / RMW_* are unset,
        // which is exactly the baseline the gate scripts already expect.
        env: { ...process.env },
      });
      return { output: stdout };
    } catch (err) {
      const stdout = err && err.stdout ? String(err.stdout) : '';
      const stderr = err && err.stderr ? String(err.stderr) : '';
      // node kills an over-budget child with signal SIGTERM and code
      // ETIMEDOUT and no numeric exit status; distinguish that from a script
      // that actively exits non-zero so the failure reason is not mislabeled.
      const timedOut =
        !!err && (err.code === 'ETIMEDOUT' || err.signal === 'SIGTERM');
      const code =
        err && typeof err.status === 'number'
          ? err.status
          : timedOut
            ? 'timeout'
            : 'unknown';
      const when = timedOut ? ` after ${timeoutMs}ms` : '';
      return {
        output: stdout + (stderr ? '\n' + stderr : ''),
        error: `local-script: ${command} exited with code ${code}${when}: ${
          err && err.message
        }`,
      };
    }
  }
}
