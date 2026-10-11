# AGENTS

`ros2_hzj` is TOPSUN / 桦之坚's independent ROS 2 / DDS dual-chain workspace (not `topsun_dimos`). Chain A: `rmw_fastrtps_cpp`, domain **42**, `config/fastdds.xml`. Chain B: Cyclone domain **0**. No custom RMW (see the scoped exception below). LCM is out of scope.

## Commands

```bash
python3 scripts/prove_rmw.py
python3 scripts/check_source_map.py
python3 scripts/print_bench_gates.py
python3 scripts/check_risk_matrix.py
python3 scripts/check_executor_map.py
python3 scripts/check_runtime_provenance.py
python3 scripts/check_unitree_cyclone_swap.py
python3 scripts/check_three_chain_repro.py
python3 scripts/check_sink_layers.py
python3 scripts/check_dual_chain_baseline.py
python3 scripts/check_dod_evidence.py
python3 scripts/check_cega_bridge_hold.py
python3 scripts/check_frozen_path_literals.py
python3 config/env/load.py print-a
python3 config/env/load.py print-b
```

`import` of `load.py` does not write `os.environ`. Operators must `source` / apply explicitly.

## Hold — do not

- Do not edit `config/fastdds.xml` or `docs/artifacts/bench/SCOREBOARD.md`.
- Do not enable Agnocast / zenoh (no vendor trees, kmod, or `rmw_zenoh`).
- 《3》–《6》 (bench score loops, Mac HIL, Promptfoo, CVE) stay out of scope.
- Do not change `dimos_bridge` DDS behavior or vendor sources.
- Do not integrate Cega / rewrite Bridge runtime (wiki3 §13(4) Hold).
- Do not invent a custom RMW, except the scoped Rust rewrite waiver below.

<a id="rust-rmw-exception"></a>

## Exception — Rust RMW rewrite (2026-10-11)

Owner **张益新** (2026-10-11) waived the **custom RMW** Hold **only** for the
project 「用 Rust 重写 ROS 2 中间件（对标 ROS 2 Jazzy + DDS 1.4）」.

This is **not** a general license to write arbitrary RMWs.

**In scope (all must hold):**

- Directory: `rmw_hzj_rust/` at the repo root (that tree only; tests and
  docs for this RMW stay under it). Do **not** drop it into `vendor/` as a
  replacement for the public Fast-DDS / Cyclone / rmw snapshots.
- Implementation / `RMW_IMPLEMENTATION` name: `rmw_hzj_rust` or
  `rmw_hzj_rust_*` (prefix `rmw_hzj_rust`).
- Target: ROS 2 Jazzy + DDS 1.4 wire (stock Fast DDS / Cyclone
  interoperability), not a third transport.

**Still Hold (not waived):**

- Agnocast / zenoh / `rmw_zenoh` / kmod / heaphook (the zenoh ban is
  **unchanged** and is outside this exception)
- Cega / `dimos_bridge` runtime rewrite
- Edits to `config/fastdds.xml` or `docs/artifacts/bench/SCOREBOARD.md`
- 《3》–《6》
- Any custom RMW outside `rmw_hzj_rust/` or not named `rmw_hzj_rust*`

This waiver does **not** claim product DoD is met, and does **not** turn
`prove_rmw.py` into a modified-`.so` proof. It does not weaken any other
rule. Other work still follows 「No custom RMW」.

## Docs

- [docs/architecture/ci-cd-gates.md](docs/architecture/ci-cd-gates.md) — CI jobs, Hold boundary, `allow-hold-bypass`
- [docs/architecture/feishu-middleware-adr.md](docs/architecture/feishu-middleware-adr.md) — Feishu middleware ADR
- [docs/architecture/latency-attribution.md](docs/architecture/latency-attribution.md) — wiki3 §12 / §13.3 stage method (no SCOREBOARD number edits)
- [docs/architecture/feishu-risk-matrix.md](docs/architecture/feishu-risk-matrix.md) — wiki3 §9.4 layer checklist (no risk scores)
- [docs/architecture/feishu-executor-waitset.md](docs/architecture/feishu-executor-waitset.md) — wiki3 §13 WaitSet → callback identity map (Humble `rclcpp`/`rclpy` not in vendor)
- [docs/architecture/feishu-runtime-provenance.md](docs/architecture/feishu-runtime-provenance.md) — wiki3 §13 underlay vs overlay vs vendor snapshot (Humble ≠ rolling)
- [docs/architecture/unitree-sdk2-dds-swap.md](docs/architecture/unitree-sdk2-dds-swap.md) — Unitree bundled Cyclone 0.10.2 vs vendor 11.0.1: drop-in FAIL / wire UNPROVEN; default bundled; legal path `unitree_sdk2_hzj` + `UNITREE_DDS_PROVIDER=external`
- [docs/architecture/feishu-three-chain-repro.md](docs/architecture/feishu-three-chain-repro.md) — wiki3 §13(2) three-chain reproduce: map ≠ reproduce; `STATUS: blocked` on this host (no Humble runtime)
- [docs/architecture/feishu-sink-layers.md](docs/architecture/feishu-sink-layers.md) — Feishu 《通信中间件》 sink layers (app / rcl / rmw / DDS / executor / memory): Hold vs allowed; no XML
- [docs/architecture/feishu-dual-chain-baseline.md](docs/architecture/feishu-dual-chain-baseline.md) — wiki3 §13(3) FastDDS + Cyclone baseline pointer (no XML rewrite; SCOREBOARD pointer only; same-topology XML tuning is paused)
- [docs/architecture/feishu-dod-evidence.md](docs/architecture/feishu-dod-evidence.md) — wiki3 §6.3 product DoD honesty (`DoD: unmet` / `STATUS: blocked`; `prove_rmw.py` is env/string, not modified `.so`)
- [docs/architecture/feishu-cega-bridge-hold.md](docs/architecture/feishu-cega-bridge-hold.md) — wiki3 §13(4) Cega / Bridge deferred Hold (no Cega; no `dimos_bridge` runtime edits)
- [#rust-rmw-exception](#rust-rmw-exception) — 张益新 2026-10-11：仅 `rmw_hzj_rust/` 的 Rust 自研 RMW 例外；zenoh 不在此列
