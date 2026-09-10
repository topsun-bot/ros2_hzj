# iter6 change — shm_midsize port_queue_capacity 64 (HF) — **not kept**

**One change** was applied, remasured, then **reverted**. Ask a human to merge; this run does not merge.

Applied **after** [`../2026-09-10-iter6-imu-baseline/`](../2026-09-10-iter6-imu-baseline/README.md) existed (Step A SHA `da24788`). Remasure SHA while the probe was on: `2d904a5`. Landed `config/fastdds.xml` is the iter5 seed again.

## Hypothesis

Step A (no new knob; iter5 seed) recorded Chain A IMU-scale 64 B / 5 ms / 200 Hz:

| topology | BestEffort p50 / p99 | Reliable p50 / p99 | loss |
|----------|----------------------|--------------------|------|
| same-host (**primary**) | 965 / 1272 µs | 948 / 1285 µs | 0/400 |
| same-process (honesty) | 589 / 715 µs | 606 / 741 µs | 0/400 |

same-host BestEffort p50 is **~1.64×** same-process. Do **not** tune same-process as primary.

Humble Fast-DDS 2.6 `port_queue_capacity` default is **512**. That listening port is sized for bursty mid-size / 1 MiB fragment fan-out. IMU ping-pong is **one-in-flight**. Prediction: 64-deep still holds a 1 MiB ~16-fragment burst both ways, and a shorter ring could cut same-host 64 B RTT/jitter.

## Exact diff (behavior, while probed)

In `config/fastdds.xml` only, inside the existing `shm_midsize` descriptor:

```xml
<port_queue_capacity>64</port_queue_capacity>
```

`maxMessageSize` 280000 / `segment_size` 2 MiB / builtin / sockets / `send_buffers` 32 / `dynamic=false` stayed. Exclusive / oversized SHM stayed discarded.

## Remeasure (same as Step A)

```bash
BENCH_DATE=2026-09-10-iter6-after \
  CHAIN_A_IMAGE=osrf/ros:humble-desktop \
  IMU_HF_CHAINS=A \
  ./scripts/bench/run_imu_hf.sh
```

XMLPARSER: pingpong stderr empty (Humble accepted `port_queue_capacity`).

## Result — not kept

| case (same-host, 64 B / 200 Hz) | baseline | after (queue 64) |
|---------------------------------|----------|------------------|
| BestEffort p50 | 964.82 µs | 998.78 µs (**+3.52%**) |
| BestEffort p99 | 1271.9 µs | 1272.2 µs (+0.03%) |
| BestEffort max | 1360 µs | **2729 µs** (worse tail) |
| Reliable p50 | 948.04 µs | 947.46 µs (−0.06%) |
| loss | 0/400 | 0/400 |

same-process honesty moved +1.5–3.8% p50 (do not tune). The booked same-host BestEffort p50 did **not** improve. A 64 B one-in-flight copy already uses `alloc_buffer(total_bytes)`; shrinking the port ring does not cut the Python/rclpy IPC tax.

**Reverted.** Landed XML has no `port_queue_capacity` override (Humble default 512). iter5 mid-size SHM + sockets + send_buffers stay. 1 MiB / mid-size gains are **not** erased (no landed XML change vs iter5). Exclusive / oversized SHM stays discarded.

This does **not** prove a Feishu / real-robot / cross-host root cause.

## What was NOT changed (landed tree)

- DimOS `ddspubsub` / `rospubsub` / ping-pong QoS, sizes, gap, sample counts
- `config/env/chain_a.sh`
- No `RMW_FASTRTPS_USE_QOS_FROM_XML`
- iter2 sockets, iter3/4 send_buffers, iter5 `shm_midsize` 280000 / 2 MiB
- Chain B; cross-host UDP; 《3》《4》《5》《6》
