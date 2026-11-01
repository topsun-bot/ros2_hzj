<!--
SPDX-License-Identifier: Apache-2.0
Adapted from anthropics/oncall-kit (Apache-2.0)
https://github.com/anthropics/oncall-kit
https://claude.com/blog/ai-ci-cd-on-call
-->

# STACK.md: capability map

Generated: 2026-11-01 · Channel: none (docs-only seed) · Probed by: Grok Bot CICD seed (no Claude Tag / oncall-setup)

| Capability | Bound to | Probe result | Notes |
|---|---|---|---|
| `code` | GitHub `topsun-bot/*` | read PRs, Actions YAML, CODEOWNERS | **This repo (`ros2_hzj`):** merge gate is [`.github/workflows/ci.yml`](/.github/workflows/ci.yml) (`structure` / `contracts` / `boundary`) plus local `python3 scripts/run_all_gates.py`. Same org pattern on priority repos in [ONCALL.md](/docs/ci-oncall/ONCALL.md). |
| `metrics` | none | gap | No Datadog / Grafana / Prometheus org-wide. Do not invent dashboards. |
| `logs` | GitHub Actions run logs (primary) | read job logs + annotations on the failing run | Job log URL is the evidence link. No central log store. |
| `pager` | TBD / GitHub notify | not tested | Repository or org notification on failed `main` runs. No PagerDuty. |
| `alert-channels` | none | gap | No org-wide CI alert Slack channel yet. |
| `incidents` | GitHub issues, optional Slack `🔴 INC:` thread | read + comment when asked | Human declares; see [ONCALL.md](/docs/ci-oncall/ONCALL.md) |
| `deploys` | GHCR tag workflows / `release.yml` where present | read workflow runs | **Not in this repo.** `ros2_hzj` has only [`.github/workflows/ci.yml`](/.github/workflows/ci.yml). `topsun_dimos` may have `docker-build.yml` / `release.yml`; look for those basenames only when they exist. Do not invent them here. |
| `flags` | n/a | n/a | Most robot / CI repos have no feature-flag service. Treat workflow `if:` and environment gates as config, not flags. |

## This repo (`ros2_hzj`)

- GitHub Actions gate: [`.github/workflows/ci.yml`](/.github/workflows/ci.yml) — jobs **structure**, **contracts**, **boundary**. See [ci-cd-gates.md](/docs/architecture/ci-cd-gates.md).
- Local operator equivalent: `python3 scripts/run_all_gates.py` (includes `check_frozen_path_literals.py`, which CI `structure` does not yet wire).
- **No Cachix** in this repo: no `cachix-build` job, no `cachix` environment, no `CACHIX_AUTH_TOKEN`. Do not invent a cache-publish path here.

## Gaps

- No Slack Claude Tag. Grok Bot routines (ci-fail-watch, weekday digest) are read-only notify; they do not page or merge.
- Cachix is **not** present in `ros2_hzj`. Do not invent `CACHIX_AUTH_TOKEN` or a `cachix` environment for this repo. Where another org repo already has a `cachix-build` job (for example `topsun_dimos`), `CACHIX_AUTH_TOKEN` lives in that repo's GitHub Actions **`cachix` environment** (not a repo-level Actions secret by default). Missing/empty token on a publish path logs `Pushing is disabled.` See [cache-publish](/docs/ci-oncall/references/cache-publish.md) and [topsun_dimos #135](https://github.com/topsun-bot/topsun_dimos/pull/135).
- No org-wide alert channel.
- No Datadog / equivalent metrics. Timeline is Actions run history + git
  history.

## Access posture

All bindings are read-only. The kit does not carry write credentials to
Cachix, GHCR, or GitHub environments. The agent never pushes cache and
never deploys. Alert-editor extension is not opted in.
