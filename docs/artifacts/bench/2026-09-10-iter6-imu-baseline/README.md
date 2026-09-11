# 2026-09-10-iter6-imu-baseline (cursor-cloud-vm)

## IMU packet + rate (nailed first)

| Item | Value |
|------|--------|
| **Payload length** | **64 B** — compact 6-axis IMU (8 B `uint64` ts + 24 B accel `3×float64` + 24 B gyro `3×float64` + 8 B seq). Typical raw IMU is tens of bytes. Full `sensor_msgs/Imu` covariances (~216 B) sit **outside** the 32–128 B window. |
| **Rate** | **200 Hz** — inter-message gap **5 ms**. Robotics / Unitree-class band (100–200+ Hz). |
| Pacing | closed-loop + min 5 ms; if RTT > 5 ms, effective rate is **1/RTT** |
| Samples / warmup / timeout | 400 / 40 / 1 s |
| Chain A message | `std_msgs/UInt8MultiArray` |
| Primary metric | **jitter**: RTT **p95/p99** and inter-message interval variance. **Do not** claim success from p50/mean. |

**Step A only. No new transport knob.** iter5 seed stays (`shm_midsize` 280000 / 2 MiB + sockets + send_buffers). See [`NOTES.md`](NOTES.md) for SHM thresholds. Shared env: [`environment.md`](environment.md).

Hostname class: `cursor-cloud-vm`。Chain A inside `osrf/ros:humble-desktop` digest `sha256:fb07245b32187d74350be25323d8ad2f8ca5c25c325759911a1eff2267a49c1e`.

**不要**和链 B 混表。**不是** 飞书现场 / 实机 / 跨机根因。cross-host 仍 blocked。《3》《4》《5》《6》仍 Hold。

## Jitter (primary) — Chain A, 64 B / 200 Hz

| topology | case | RTT p95 / p99 | RTT p95−p50 | arrival I stdev | arrival \|I−5 ms\| p95 / p99 | loss |
|----------|------|---------------|-------------|-----------------|------------------------------|------|
| [`same-host`](chain_a_same_host/summary.md) **primary** | BestEffort | 1205 / 1336 µs | 248 µs | 218 µs | 488 / 635 µs | 0/400 |
| same-host | Reliable | 1161 / 1286 µs | 258 µs | 224 µs | 492 / 643 µs | 0/400 |
| [`same-process`](chain_a_same_process/summary.md) honesty | BestEffort | 733 / 806 µs | 125 µs | 360 µs | 334 / 449 µs | 0/400 |
| same-process | Reliable | 719 / 800 µs | 107 µs | 116 µs | 307 / 464 µs | 0/400 |

Publish cadence stays near the 5 ms target (same-host BestEffort pub I p50 5094 µs, pub stdev 53 µs). Arrival-interval jitter is larger than publish jitter — that is the consumer-facing IMU gap. same-host RTT tail (p95−p50 **248 µs**) is wider than same-process (**125 µs**); **do not tune same-process as primary**.

p50 RTT (secondary only): same-host BestEffort 957 µs; same-process 607 µs. Effective rate stayed **200 Hz**. [`chain_a_cross_host_UDP/`](chain_a_cross_host_UDP/summary.md) blocked.

链 B **未跑**。

```bash
BENCH_DATE=2026-09-10-iter6-imu-baseline CHAIN_A_IMAGE=osrf/ros:humble-desktop \
  IMU_HF_CHAINS=A ./scripts/bench/run_imu_hf.sh
```
