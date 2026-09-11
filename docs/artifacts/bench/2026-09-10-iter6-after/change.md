# iter6 change — shm_midsize port_queue_capacity 64 (HF) — **not kept**

**One change** was applied, remasured, then **reverted**. Ask a human to merge; this run does not merge.

Applied **after** [`../2026-09-10-iter6-imu-baseline/`](../2026-09-10-iter6-imu-baseline/README.md) existed (Step A first: **64 B / 200 Hz** nailed, no knob). Remasure SHA while the probe was on: `2b8f666` (jitter fields in `pingpong.py`). Landed `config/fastdds.xml` is the iter5 seed again.

**Primary success metric is jitter** (RTT p95/p99 + inter-message interval variance). Do **not** keep from p50/mean alone.

## Hypothesis

Step A (no new knob; iter5 seed) recorded Chain A IMU-scale **64 B / 5 ms / 200 Hz**:

| topology | BestEffort RTT p95 / p99 | RTT p95−p50 | arrival I stdev / \|I−5 ms\| p95 | loss |
|----------|--------------------------|-------------|------------------------------|------|
| same-host (**primary**) | 1205 / 1336 µs | 248 µs | 218 / 488 µs | 0/400 |
| same-process (honesty) | 733 / 806 µs | 125 µs | 360 / 334 µs | 0/400 |

same-host BestEffort RTT p95 is **~1.64×** same-process; p95−p50 is wider (248 vs 125 µs). Do **not** tune same-process as primary.

Humble Fast-DDS 2.6 `port_queue_capacity` default is **512**. That listening port is sized for bursty mid-size / 1 MiB fragment fan-out. IMU ping-pong is **one-in-flight**. Prediction: 64-deep still holds a 1 MiB ~16-fragment burst both ways, and a shorter ring could cut same-host 64 B **jitter**.

## Exact diff (behavior, while probed)

In `config/fastdds.xml` only, inside the existing `shm_midsize` descriptor:

```xml
<port_queue_capacity>64</port_queue_capacity>
```

`maxMessageSize` 280000 / `segment_size` 2 MiB / builtin / sockets / `send_buffers` 32 / `dynamic=false` stayed. Exclusive / oversized SHM stayed discarded. 1 MiB stays on the builtin fragment path.

## Remeasure (same as Step A)

```bash
BENCH_DATE=2026-09-10-iter6-after \
  CHAIN_A_IMAGE=osrf/ros:humble-desktop \
  IMU_HF_CHAINS=A \
  ./scripts/bench/run_imu_hf.sh
```

XMLPARSER: pingpong stderr empty (Humble accepted `port_queue_capacity`).

## Result — not kept (jitter gate)

| case (same-host, 64 B / 200 Hz) | baseline | after (queue 64) |
|---------------------------------|----------|------------------|
| BestEffort RTT p95 / p99 | 1205 / 1336 µs | 1234 / 1384 µs (**+2.38% / +3.58%**) |
| BestEffort RTT p95−p50 | 248 µs | 273 µs (wider) |
| BestEffort arrival I stdev / \|I−5 ms\| p95 | 218 / 488 µs | 256 / 568 µs (worse) |
| Reliable RTT p95 | 1161 µs | 1200 µs (**+3.32%**) |
| Reliable arrival \|I−5 ms\| p95 | 492 µs | 585 µs (worse) |
| BestEffort p50 (secondary) | 957 µs | 961 µs (+0.37%; **not a keep**) |
| loss | 0/400 | 0/400 |

same-process honesty is not the gate. The booked same-host **jitter** did **not** improve. A 64 B one-in-flight copy already uses `alloc_buffer(total_bytes)`; shrinking the port ring does not cut the Python/rclpy IPC tax.

**Reverted.** Landed XML has no `port_queue_capacity` override (Humble default 512). iter5 mid-size SHM + sockets + send_buffers stay. **1 MiB / mid-size gains are not erased** (no landed XML change vs iter5). Exclusive / oversized SHM stays discarded.

This does **not** prove a Feishu / real-robot / cross-host root cause. 《3》《4》《5》《6》 still Hold.

## What was NOT changed (landed tree)

- DimOS `ddspubsub` / `rospubsub` / ping-pong QoS, sizes, gap, sample counts
- `config/env/chain_a.sh`
- No `RMW_FASTRTPS_USE_QOS_FROM_XML`
- iter2 sockets, iter3/4 send_buffers, iter5 `shm_midsize` 280000 / 2 MiB
- Chain B; cross-host UDP; 《3》《4》《5》《6》
