# AGENTS

`ros2_hzj` is TOPSUN / 桦之坚's independent ROS 2 / DDS dual-chain workspace (not `topsun_dimos`). Chain A: `rmw_fastrtps_cpp`, domain **42**, `config/fastdds.xml`. Chain B: Cyclone domain **0**. No custom RMW. LCM is out of scope.

## Commands

```bash
python3 scripts/prove_rmw.py
python3 scripts/check_source_map.py
python3 scripts/print_bench_gates.py
python3 config/env/load.py print-a
python3 config/env/load.py print-b
```

`import` of `load.py` does not write `os.environ`. Operators must `source` / apply explicitly.

## Hold — do not

- Do not edit `config/fastdds.xml` or `docs/artifacts/bench/SCOREBOARD.md`.
- Do not enable Agnocast / zenoh (no vendor trees, kmod, or `rmw_zenoh`).
- 《3》–《6》 (bench score loops, Mac HIL, Promptfoo, CVE) stay out of scope.
- Do not change `dimos_bridge` DDS behavior or vendor sources.

## Reviews

- PRs get GitHub Copilot review automatically (ruleset `copilot-auto-review`, id 22999465: `copilot_code_review`, `review_on_push=true`, `review_draft_pull_requests=true` on all branches). Required GitHub Approve is still 1 unless Settings → Copilot → Code review Auto-approval toggles are on (Allow Copilot to approve + count toward merge). Optional warn-not-fail workflow: [`.github/workflows/request-copilot-review.yml`](.github/workflows/request-copilot-review.yml) (`gh api` → `copilot-pull-request-reviewer[bot]`; not a required check).

## Docs

- [docs/architecture/ci-cd-gates.md](docs/architecture/ci-cd-gates.md) — CI jobs, Hold boundary, `allow-hold-bypass`, Copilot auto-review
- [docs/architecture/feishu-middleware-adr.md](docs/architecture/feishu-middleware-adr.md) — Feishu middleware ADR
- [docs/architecture/latency-attribution.md](docs/architecture/latency-attribution.md) — wiki3 §12 / §13.3 stage method (no SCOREBOARD number edits)
