# iter6 change — shm_midsize port_queue_capacity 64 (HF)

**One change.** Config-only. Ask a human to merge; this run does not merge.

Applied **after** [`../2026-09-10-iter6-imu-baseline/`](../2026-09-10-iter6-imu-baseline/README.md) existed on this branch (Step A SHA `da24788`).

## Hypothesis

Step A (no new knob; iter5 seed) recorded Chain A IMU-scale 64 B / 5 ms / 200 Hz:

| topology | BestEffort p50 / p99 | Reliable p50 / p99 | loss |
|----------|----------------------|--------------------|------|
| same-host (**primary**) | 965 / 1272 µs | 948 / 1285 µs | 0/400 |
| same-process (honesty) | 589 / 715 µs | 606 / 741 µs | 0/400 |

same-host BestEffort p50 is **~1.64×** same-process. Do **not** tune same-process as primary.

Humble Fast-DDS 2.6 `SharedMemTransportDescriptor::shm_default_port_queue_capacity` is **512**. That listening port is sized for bursty mid-size / 1 MiB fragment fan-out. IMU ping-pong is **one-in-flight** (closed-loop). A 512-deep ring is colder than a queue that only needs a handful of descriptors.

**Prediction:** set `port_queue_capacity` to **64** on the existing `shm_midsize` transport (the only user SHM). 64 still holds a 1 MiB ~16-fragment burst both ways (32) with slack, so this is an HF-sized queue, not a 1 MiB eraser. `maxMessageSize` 280000 / `segment_size` 2 MiB stay. Builtin UDP+SHM stay. iter2 sockets and iter3/4 `send_buffers` 32 / `dynamic=false` stay. Exclusive / oversized SHM stays discarded.

This is **one knob** (SHM port queue depth on the accepted mid-size transport). Not a second SHM. Not exclusive SHM. Not a socket-buffer or send-buffer-pool change.

This does **not** prove a Feishu / real-robot / cross-host root cause.

## Exact diff (behavior)

In `config/fastdds.xml` only, inside the existing `shm_midsize` descriptor:

```xml
<port_queue_capacity>64</port_queue_capacity>
```

`config/fastdds.zh.md` notes the knob.

## What was NOT changed

- DimOS `ddspubsub` / `rospubsub` / ping-pong QoS, sizes, gap, sample counts
- `config/env/chain_a.sh` (still RMW=`rmw_fastrtps_cpp`, domain 42)
- No `RMW_FASTRTPS_USE_QOS_FROM_XML`, no `historyMemoryPolicy`, no `publishMode`
- iter2 `sendSocketBufferSize` / `listenSocketBufferSize` 2 MiB
- iter3/4 `preallocated_number=32` / `dynamic=false`
- iter5 `maxMessageSize=280000` / `segment_size=2097152` / `useBuiltinTransports=true`
- Exclusive / oversized SHM (still discarded)
- Chain B Cyclone URI / iceoryx
- Cross-host UDP (still blocked; single VM)
- 《3》90%/LLM scoring, 《4》Mac/preprod hero, 《5》Promptfoo, 《6》CVE audit

## Remeasure command (same as Step A, Chain A only)

```bash
BENCH_DATE=2026-09-10-iter6-after \
  CHAIN_A_IMAGE=osrf/ros:humble-desktop \
  IMU_HF_CHAINS=A \
  ./scripts/bench/run_imu_hf.sh
```

Like-to-like vs `docs/artifacts/bench/2026-09-10-iter6-imu-baseline/` Chain A only: size `64`, gap 5 ms, 400 samples, `uint8_multiarray`. Primary table: **same-host**. Same-process is an honesty check only. Deltas in [`delta.md`](delta.md). Do not put Chain A and Chain B in one table.

Spot-check (not a second treatment): same-host large-packet 1 MiB BestEffort/Reliable must stay 80/80 and within noise of iter5 if remasured. Document the tradeoff if not.
