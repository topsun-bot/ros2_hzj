# iter9 change — default-participant WLP off (HF) — **not kept**

**One change** was applied, remasured, then **reverted**. Ask a human to merge; this run does not merge.

Applied **after** [`../2026-09-11-iter8/`](../2026-09-11-iter8/README.md) existed on `main` (PR #17, SHA `d611bfdf7df2d95c9a362727380126bfc4321665`). IMU **64 B / 200 Hz** and `healthy_check_timeout_ms` 10000 were already nailed. `leaseAnnouncement` 15 s was discarded. Remasure SHA while the probe was on: `44ad5d2`. Landed `config/fastdds.xml` is the iter7 seed again.

**Primary success metric is jitter** (RTT p95/p99 + inter-message interval variance / `|I − 5 ms|`). Do **not** keep from p50/mean alone.

## Hypothesis

iter7 (post–`healthy_check_timeout_ms` 10000; landed seed after iter8 revert) recorded Chain A IMU-scale **64 B / 5 ms / 200 Hz**:

| topology | BestEffort RTT p95 / p99 | RTT p95−p50 | arrival I stdev / \|I−5 ms\| p95 | loss |
|----------|--------------------------|-------------|------------------------------|------|
| same-host (**primary**) | 1148 / 1238 µs | 160 µs | 168 / 375 µs | 0/400 |
| same-process (honesty) | 655 / 724 µs | 66 µs | 73 / 243 µs | 0/400 |

iter8 (`leaseAnnouncement` 3 s → 15 s) moved official-run RTT p95 the right way but **widened arrival** and was **reverted**. Do **not** retry leaseAnnouncement / leaseDuration. Do **not** tune same-process as primary.

Humble Fast-DDS 2.6 `use_WriterLivelinessProtocol` default is **true**. WLP adds a builtin writer/reader that share the non-dynamic 32-buffer send pool (`dynamic=false`) and the SHM/UDP path with 64 B one-in-flight. Prediction: turning WLP **off** removes that control-plane pair from the same-host **p95/p99** / arrival `|I−5 ms|` window.

This is **one knob** (WLP enable flag on the default participant). Not `leaseAnnouncement` / `leaseDuration`. Not `healthy_check_timeout_ms`. Not `port_queue_capacity`. Not a socket-buffer / send-buffer / mid-size SHM size change.

This does **not** prove a Feishu / real-robot / cross-host root cause.

## Exact diff (behavior, while probed)

In `config/fastdds.xml` only, inside the existing default participant `<rtps>`:

```xml
<builtin>
    <use_WriterLivelinessProtocol>false</use_WriterLivelinessProtocol>
</builtin>
```

`healthy_check_timeout_ms` 10000 / `maxMessageSize` 280000 / `segment_size` 2 MiB / builtin / sockets / `send_buffers` 32 / `dynamic=false` stayed. Exclusive / oversized SHM stayed discarded. 1 MiB stays on the builtin fragment path.

## Remeasure (same as iter7 / iter8)

```bash
BENCH_DATE=2026-09-11-iter9 \
  CHAIN_A_IMAGE=osrf/ros:humble-desktop \
  IMU_HF_CHAINS=A \
  ./scripts/bench/run_imu_hf.sh
```

XMLPARSER: pingpong stderr empty (Humble accepted `use_WriterLivelinessProtocol`).

## Result — not kept (jitter gate vs iter7)

| case (same-host, 64 B / 200 Hz) | iter7 (health 10 s) | after (WLP off) |
|---------------------------------|---------------------|-----------------|
| BestEffort RTT p95 / p99 | 1148 / 1238 µs | 1148 / 1253 µs (+0.03% / +1.21%) |
| BestEffort RTT p95−p50 | 160 µs | 223 µs (**wider**) |
| BestEffort arrival I stdev / \|I−5 ms\| p95 | 168 / 375 µs | 325 / 543 µs (**worse**) |
| Reliable RTT p95 / p99 | 1173 / 1250 µs | 1197 / 1312 µs |
| Reliable arrival \|I−5 ms\| p95 | 569 µs | 587 µs |
| BestEffort p50 (secondary) | 988 µs | 925 µs (−6.41%; **not the gate**) |
| loss | 0/400 | 0/400 |

A same-host **repeat** moved BestEffort RTT p95 to **1115** / p99 **1189** vs iter7 1148 / 1238 but arrival `|I−5 ms|` p95 stayed wide at **413 µs**. Official-run p50 drop without a held arrival-interval win is **not** a keep.

same-process honesty is not the gate. Turning WLP off does not cut the Python/rclpy IPC tax on the 64 B hot path.

**Reverted.** Landed XML has no `use_WriterLivelinessProtocol` override (Humble default true). iter7 `healthy_check_timeout_ms` 10000 + iter5 mid-size SHM + sockets + send_buffers stay. Exclusive / oversized SHM stays discarded.

## 1 MiB / mid-size (do not spit those gains)

The probe is WLP-only. **1 MiB / mid-size suite was not remasured under the discarded probe.** Landed XML equals iter7 (`healthy_check_timeout_ms` 10000, 280000 / 2 MiB, sockets, send_buffers), so those gains stay. Prefer-not-regressing 1 MiB is satisfied by revert.

This does **not** prove a Feishu / real-robot / cross-host root cause. 《3》《4》《5》《6》 still Hold.

## What was NOT changed (landed tree)

- DimOS `ddspubsub` / `rospubsub` / ping-pong QoS, sizes, gap, sample counts
- `config/env/chain_a.sh`
- No `RMW_FASTRTPS_USE_QOS_FROM_XML`, no `historyMemoryPolicy`, no `publishMode`
- iter2 `sendSocketBufferSize` / `listenSocketBufferSize` 2 MiB
- iter3/4 `preallocated_number=32` / `dynamic=false`
- iter5 `shm_midsize` `maxMessageSize` 280000 / `segment_size` 2 MiB
- iter6 discarded `port_queue_capacity` 64 (not revived)
- iter7 `healthy_check_timeout_ms` 10000 (kept)
- iter8 discarded `leaseAnnouncement` 15 s (not revived; do not retry lease)
- Chain B; cross-host UDP; 《3》《4》《5》《6》
