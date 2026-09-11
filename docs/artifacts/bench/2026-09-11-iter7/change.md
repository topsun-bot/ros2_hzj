# iter7 change — shm_midsize healthy_check_timeout_ms 10000 (HF) — **kept**

**One change.** Config-only. Ask a human to merge; this run does not merge.

Applied **after** [`../2026-09-10-iter6-imu-baseline/`](../2026-09-10-iter6-imu-baseline/README.md) existed on `main` (PR #11, SHA `0cee4ee96e07d405bcd423d2a256482c67a061a1`). IMU **64 B / 200 Hz** was already nailed. Remasure SHA with the knob on: `5efbca3`.

**Primary success metric is jitter** (RTT p95/p99 + inter-message interval variance). Do **not** keep from p50/mean alone.

## Hypothesis

iter6 Step A (no new knob; iter5 seed) recorded Chain A IMU-scale **64 B / 5 ms / 200 Hz**:

| topology | BestEffort RTT p95 / p99 | RTT p95−p50 | arrival I stdev / \|I−5 ms\| p95 | loss |
|----------|--------------------------|-------------|------------------------------|------|
| same-host (**primary**) | 1205 / 1336 µs | 248 µs | 218 / 488 µs | 0/400 |
| same-process (honesty) | 733 / 806 µs | 125 µs | 360 / 334 µs | 0/400 |

iter6 Step B (`port_queue_capacity` 512 → 64) made same-host BestEffort p95/p99 and arrival jitter **worse** and was **reverted**. A 64 B one-in-flight copy already uses `alloc_buffer(total_bytes)`. Do **not** tune same-process as primary.

Humble Fast-DDS 2.6 `healthy_check_timeout_ms` default is **1000**. The SHM port watcher takes `empty_cv_mutex` when that timeout elapses; `port_wait_timeout_ms` is `healthy_check_timeout_ms/3` (idle wait only). IMU ping-pong is **one-in-flight** (~2 s per case). Prediction: **10000 ms** keeps the watcher out of the same-host 64 B **p95/p99** window.

This is **one knob** (SHM health-check timeout on the existing `shm_midsize` descriptor). Not `port_queue_capacity`. Not a socket-buffer / send-buffer / mid-size SHM size change.

This does **not** prove a Feishu / real-robot / cross-host root cause.

## Exact diff (behavior)

In `config/fastdds.xml` only, inside the existing `shm_midsize` descriptor:

```xml
<healthy_check_timeout_ms>10000</healthy_check_timeout_ms>
```

`maxMessageSize` 280000 / `segment_size` 2 MiB / builtin / sockets / `send_buffers` 32 / `dynamic=false` stay. Exclusive / oversized SHM stays discarded. 1 MiB stays on the builtin fragment path (sample > 280000).

## Remeasure (same as iter6 Step A)

```bash
BENCH_DATE=2026-09-11-iter7 \
  CHAIN_A_IMAGE=osrf/ros:humble-desktop \
  IMU_HF_CHAINS=A \
  ./scripts/bench/run_imu_hf.sh
```

XMLPARSER: pingpong stderr empty (Humble accepted `healthy_check_timeout_ms`).

## Result — kept (jitter gate)

| case (same-host, 64 B / 200 Hz) | baseline | after (health 10 s) |
|---------------------------------|----------|---------------------|
| BestEffort RTT p95 / p99 | 1205 / 1336 µs | 1148 / 1238 µs (**−4.76% / −7.34%**) |
| BestEffort RTT p95−p50 | 248 µs | 160 µs (tighter) |
| BestEffort arrival I stdev / \|I−5 ms\| p95 | 218 / 488 µs | 168 / 375 µs (tighter) |
| Reliable RTT p95 / p99 | 1161 / 1286 µs | 1173 / 1250 µs (+1.04% / **−2.84%**) |
| Reliable arrival \|I−5 ms\| p95 | 492 µs | 569 µs (wider on this run) |
| BestEffort p50 (secondary) | 957 µs | 988 µs (+3.27%; **not the gate**) |
| loss | 0/400 | 0/400 |

same-process honesty is not the gate. A same-host **repeat** held the BestEffort win (p95 1153 µs, arrival \|I−5 ms\| p95 387 µs) and put Reliable arrival \|I−5 ms\| p95 at 501 µs (flat vs 492). First-run Reliable arrival is treated as VM noise, not a discard.

**Kept.** Landed XML has `healthy_check_timeout_ms` 10000 on `shm_midsize`. iter5 mid-size SHM + sockets + send_buffers stay. Exclusive / oversized SHM stays discarded.

## 1 MiB / mid-size spot-check (do not spit those gains)

The knob is on `shm_midsize` only. 1 MiB (1048576 > 280000) stays on the builtin fragment path. Like-to-like same-host large-packet remasure (100 / 256 KiB / 1 MiB, 80 samples, 100 ms) vs [`../2026-09-10-iter5/`](../2026-09-10-iter5/README.md):

| case (same-host) | iter5 p50 / p95 | iter7 spot p50 / p95 | 80/80? |
|------------------|-----------------|----------------------|--------|
| BestEffort 256 KiB | 1346 / 1541 µs | 1305 / 1474 µs | yes |
| BestEffort 1 MiB | 2312 / 2841 µs | 2301 / 2733 µs | yes |
| Reliable 1 MiB | 2368 / 2699 µs | 2339 / 2597 µs | yes |

**1 MiB / mid-size gains are not erased.** A 1 MiB-only cold run (no mid-size warmup in the same process) was slower on BestEffort and is **not** the like-to-like table.

This does **not** prove a Feishu / real-robot / cross-host root cause. 《3》《4》《5》《6》 still Hold.

## What was NOT changed

- DimOS `ddspubsub` / `rospubsub` / ping-pong QoS, sizes, gap, sample counts
- `config/env/chain_a.sh`
- No `RMW_FASTRTPS_USE_QOS_FROM_XML`, no `historyMemoryPolicy`, no `publishMode`
- iter2 `sendSocketBufferSize` / `listenSocketBufferSize` 2 MiB
- iter3/4 `preallocated_number=32` / `dynamic=false`
- iter5 `shm_midsize` `maxMessageSize` 280000 / `segment_size` 2 MiB
- iter6 discarded `port_queue_capacity` 64 (not revived)
- Chain B; cross-host UDP; 《3》《4》《5》《6》
