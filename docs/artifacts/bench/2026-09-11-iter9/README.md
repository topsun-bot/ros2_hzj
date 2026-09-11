# 2026-09-11-iter9 (cursor-cloud-vm)

Hostname class: `cursor-cloud-vm`。Chain A inside `osrf/ros:humble-desktop` (same digest as iter8 / iter7 / iter6 / iter5).

**IMU packet + rate (already nailed on main):** **64 B / 200 Hz** (5 ms). Primary metric is **jitter** (RTT p95/p99 + inter-message interval). Do **not** claim success from p50/mean.

**One change (then reverted):** default-participant `use_WriterLivelinessProtocol` true → false. See [`change.md`](change.md). Like-to-like vs [`../2026-09-11-iter7/`](../2026-09-11-iter7/README.md): [`delta.md`](delta.md). Continuity vs [`../2026-09-10-iter6-imu-baseline/`](../2026-09-10-iter6-imu-baseline/README.md) is cited in delta; **not** the gate.

**不要**和链 B 混表。**不是** 飞书现场 / 实机 / 跨机根因。

| 目录 | 链 | Topology | STATUS |
|------|----|----------|--------|
| [`chain_a_same_process/`](chain_a_same_process/summary.md) | A | `same-process` | ok — honesty only; **do not tune** |
| [`chain_a_same_host/`](chain_a_same_host/summary.md) | A | `same-host` | ok — primary. BestEffort arrival \|I−5 ms\| p95 375→543; repeat arrival 413; **not kept** |
| [`chain_a_cross_host_UDP/`](chain_a_cross_host_UDP/summary.md) | A | `cross-host-UDP` | blocked — 单机 VM |

链 B **未重跑**。落地 XML 回到 iter7 种子（`healthy_check_timeout_ms` 10000；中包 SHM 280000 / 2 MiB 保留；**1 MiB 赢面未擦**）。独占 / 过大 SHM 仍丢弃。《3》《4》《5》《6》仍 Hold。

```bash
BENCH_DATE=2026-09-11-iter9 CHAIN_A_IMAGE=osrf/ros:humble-desktop \
  IMU_HF_CHAINS=A ./scripts/bench/run_imu_hf.sh
```
