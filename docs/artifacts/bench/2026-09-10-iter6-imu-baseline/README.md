# 2026-09-10-iter6-imu-baseline (cursor-cloud-vm)

Hostname class: `cursor-cloud-vm`。Chain A inside `osrf/ros:humble-desktop` digest `sha256:fb07245b32187d74350be25323d8ad2f8ca5c25c325759911a1eff2267a49c1e` (same as iter5).

**Step A only.** High-frequency small-packet same-topology ping-pong (Feishu / IMU scale). **No new transport knob.** See [`NOTES.md`](NOTES.md) for the 64 B / 200 Hz justification and SHM size thresholds. Shared env: [`environment.md`](environment.md).

**不要**和链 B 混表。**不是** 飞书现场 / 实机 / 跨机根因。cross-host 仍 blocked。

## Exact size and rate

| Item | Value |
|------|--------|
| Payload length (bytes) | **64** (compact 6-axis IMU: 8 B ts + 24 B accel + 24 B gyro + 8 B seq) |
| Inter-message gap | **5 ms** (target **200 Hz**, IMU-ish) |
| Samples / warmup / timeout | 400 / 40 / 1 s |
| Pacing | minimum 5 ms between publishes; if RTT > 5 ms, effective rate is **1/RTT** (closed-loop) |
| Chain A message | `std_msgs/UInt8MultiArray` (contiguous uint8) |

Effective rate stayed **200 Hz** (p50 RTT ≪ 5 ms on both topologies). Timeouts are the loss proxy.

## Topologies (separate tables)

| 目录 | 链 | Topology | STATUS |
|------|----|----------|--------|
| [`chain_a_same_process/`](chain_a_same_process/summary.md) | A | `same-process` | ok — BestEffort p50 589 µs / p99 715 µs; Reliable p50 606 µs; **400/400**, 0 timeouts. Honesty check only — **do not tune** |
| [`chain_a_same_host/`](chain_a_same_host/summary.md) | A | `same-host` | ok — **primary**. BestEffort p50 965 µs / p99 1272 µs; Reliable p50 948 µs / p99 1285 µs; **400/400**, 0 timeouts |
| [`chain_a_cross_host_UDP/`](chain_a_cross_host_UDP/summary.md) | A | `cross-host-UDP` | blocked — 单机 VM |

same-host BestEffort p50 is **~1.64×** same-process (965 vs 589 µs). Same-host is the HF bottleneck; Step B must target that topology, not same-process.

链 B **未跑**（可选且必须分表；本 Step 无 Chain B 旋钮）。《3》《4》《5》《6》仍 Hold。

```bash
BENCH_DATE=2026-09-10-iter6-imu-baseline CHAIN_A_IMAGE=osrf/ros:humble-desktop \
  IMU_HF_CHAINS=A ./scripts/bench/run_imu_hf.sh
```
