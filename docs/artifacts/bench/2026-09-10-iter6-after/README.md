# 2026-09-10-iter6-after (cursor-cloud-vm)

Hostname class: `cursor-cloud-vm`。Chain A inside `osrf/ros:humble-desktop` (same digest as Step A / iter5).

**One change (then reverted):** `shm_midsize` `port_queue_capacity` 512 → 64. See [`change.md`](change.md). Like-to-like vs [`../2026-09-10-iter6-imu-baseline/`](../2026-09-10-iter6-imu-baseline/README.md): [`delta.md`](delta.md).

**不要**和链 B 混表。**不是** 飞书现场 / 实机 / 跨机根因。

| 目录 | 链 | Topology | STATUS |
|------|----|----------|--------|
| [`chain_a_same_process/`](chain_a_same_process/summary.md) | A | `same-process` | ok — honesty only; p50 +1.5–3.8%; **do not tune** |
| [`chain_a_same_host/`](chain_a_same_host/summary.md) | A | `same-host` | ok — primary. BestEffort p50 **+3.52%** (not kept); Reliable flat; 0/400 |
| [`chain_a_cross_host_UDP/`](chain_a_cross_host_UDP/summary.md) | A | `cross-host-UDP` | blocked — 单机 VM |

链 B **未重跑**。落地 XML 回到 iter5 种子（中包 SHM 280000 / 2 MiB 保留）。《3》《4》《5》《6》仍 Hold。

```bash
BENCH_DATE=2026-09-10-iter6-after CHAIN_A_IMAGE=osrf/ros:humble-desktop \
  IMU_HF_CHAINS=A ./scripts/bench/run_imu_hf.sh
```
