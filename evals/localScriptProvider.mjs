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

    try {
      const stdout = execFileSync('python3', argv, {
        cwd: repoRoot,
        timeout: 30000,
        encoding: 'utf8',
        // Inherit the operator's env. On this host ROS_* / RMW_* are unset,
        // which is exactly the baseline the gate scripts already expect.
        env: { ...process.env },
      });
      return { output: stdout };
    } catch (err) {
      const stdout = err && err.stdout ? String(err.stdout) : '';
      const stderr = err && err.stderr ? String(err.stderr) : '';
      const code = err && typeof err.status === 'number' ? err.status : 'unknown';
      return {
        output: stdout + (stderr ? '\n' + stderr : ''),
        error: `local-script: ${command} exited with code ${code}: ${err && err.message}`,
      };
    }
  }
}
