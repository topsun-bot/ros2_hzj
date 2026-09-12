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

## Docs

- [docs/architecture/ci-cd-gates.md](docs/architecture/ci-cd-gates.md) — CI jobs, Hold boundary, `allow-hold-bypass`
- [docs/architecture/feishu-middleware-adr.md](docs/architecture/feishu-middleware-adr.md) — Feishu middleware ADR
- [docs/architecture/latency-attribution.md](docs/architecture/latency-attribution.md) — wiki3 §12 / §13.3 stage method (no SCOREBOARD number edits)
