# 2026-09-10-iter6-imu-baseline (cursor-cloud-vm)

Hostname class: `cursor-cloud-vm`。Chain A inside `osrf/ros:humble-desktop` (same image class as iter5).

**Step A only.** High-frequency small-packet same-topology ping-pong (Feishu / IMU scale). **No new transport knob.** See [`NOTES.md`](NOTES.md) for the 64 B / 200 Hz justification and SHM size thresholds.

**不要**和链 B 混表。**不是** 飞书现场 / 实机 / 跨机根因。cross-host 仍 blocked。

## Exact size and rate

| Item | Value |
|------|--------|
| Payload length (bytes) | **64** (compact 6-axis IMU: ts + accel xyz + gyro xyz + seq) |
| Inter-message gap | **5 ms** (target **200 Hz**, IMU-ish) |
| Samples / warmup / timeout | 400 / 40 / 1 s |
| Pacing | minimum 5 ms between publishes; if RTT > 5 ms, effective rate is **1/RTT** (closed-loop) |
| Chain A message | `std_msgs/UInt8MultiArray` (contiguous uint8) |

## Topologies (separate tables)

| 目录 | 链 | Topology | STATUS |
|------|----|----------|--------|
| [`chain_a_same_process/`](chain_a_same_process/summary.md) | A | `same-process` | pending remasure |
| [`chain_a_same_host/`](chain_a_same_host/summary.md) | A | `same-host` | pending remasure — primary if HF IPC is the bottleneck |
| [`chain_a_cross_host_UDP/`](chain_a_cross_host_UDP/summary.md) | A | `cross-host-UDP` | blocked — 单机 VM |

链 B **未跑**（本 Step 无 Chain B 旋钮；Chain B 可选且必须分表）。《3》《4》《5》《6》仍 Hold。

```bash
BENCH_DATE=2026-09-10-iter6-imu-baseline CHAIN_A_IMAGE=osrf/ros:humble-desktop \
  IMU_HF_CHAINS=A ./scripts/bench/run_imu_hf.sh
```
