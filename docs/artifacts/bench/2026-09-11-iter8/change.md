# iter8 change — SIMPLE discovery leaseAnnouncement 15 s (HF) — **not kept**

**One change** was applied, remasured, then **reverted**. Ask a human to merge; this run does not merge.

Applied **after** [`../2026-09-11-iter7/`](../2026-09-11-iter7/README.md) existed on `main` (PR #12, SHA `63574b8666490f5f88954eb80db21852b7f611e8`). IMU **64 B / 200 Hz** and `healthy_check_timeout_ms` 10000 were already nailed. Remasure SHA while the probe was on: `be6016b`. Landed `config/fastdds.xml` is the iter7 seed again.

**Primary success metric is jitter** (RTT p95/p99 + inter-message interval variance / `|I − 5 ms|`). Do **not** keep from p50/mean alone.

## Hypothesis

iter7 (post–`healthy_check_timeout_ms` 10000) recorded Chain A IMU-scale **64 B / 5 ms / 200 Hz**:

| topology | BestEffort RTT p95 / p99 | RTT p95−p50 | arrival I stdev / \|I−5 ms\| p95 | loss |
|----------|--------------------------|-------------|------------------------------|------|
| same-host (**primary**) | 1148 / 1238 µs | 160 µs | 168 / 375 µs | 0/400 |
| same-process (honesty) | 655 / 724 µs | 66 µs | 73 / 243 µs | 0/400 |

iter6 Step B (`port_queue_capacity` 512 → 64) made same-host BestEffort p95/p99 and arrival jitter **worse** and was **reverted**. Do **not** tune same-process as primary.

Humble Fast-DDS 2.6 `leaseAnnouncement` (`leaseDuration_announcementperiod`) default is **3 s**. After initial announcements, PDP `resend_participant_info_event_` fires on that period. IMU same-host is **~5 s** of one-in-flight 64 B / 5 ms traffic. Prediction: a 3 s SPDP write shares the SHM/UDP path and can land in same-host **p95/p99** / arrival `|I−5 ms|`. **15 s** stays under the default 20 s `leaseDuration` (not a second knob) so peers do not expire.

This is **one knob** (SIMPLE discovery announcement period on the default participant). Not `healthy_check_timeout_ms`. Not `port_queue_capacity`. Not a socket-buffer / send-buffer / mid-size SHM size change.

This does **not** prove a Feishu / real-robot / cross-host root cause.

## Exact diff (behavior, while probed)

In `config/fastdds.xml` only, inside the existing default participant `<rtps>`:

```xml
<builtin>
    <discovery_config>
        <leaseAnnouncement>
            <sec>15</sec>
            <nanosec>0</nanosec>
        </leaseAnnouncement>
    </discovery_config>
</builtin>
```

`healthy_check_timeout_ms` 10000 / `maxMessageSize` 280000 / `segment_size` 2 MiB / builtin / sockets / `send_buffers` 32 / `dynamic=false` stayed. Exclusive / oversized SHM stayed discarded. 1 MiB stays on the builtin fragment path.

## Remeasure (same as iter7)

```bash
BENCH_DATE=2026-09-11-iter8 \
  CHAIN_A_IMAGE=osrf/ros:humble-desktop \
  IMU_HF_CHAINS=A \
  ./scripts/bench/run_imu_hf.sh
```

XMLPARSER: pingpong stderr empty (Humble accepted `leaseAnnouncement`).

## Result — not kept (jitter gate vs iter7)

| case (same-host, 64 B / 200 Hz) | iter7 (health 10 s) | after (announce 15 s) |
|---------------------------------|---------------------|------------------------|
| BestEffort RTT p95 / p99 | 1148 / 1238 µs | 1104 / 1145 µs (−3.79% / −7.48%) |
| BestEffort RTT p95−p50 | 160 µs | 220 µs (**wider**) |
| BestEffort arrival I stdev / \|I−5 ms\| p95 | 168 / 375 µs | 193 / 448 µs (**worse**) |
| Reliable RTT p95 / p99 | 1173 / 1250 µs | 1031 / 1139 µs |
| Reliable arrival \|I−5 ms\| p95 | 569 µs | 457 µs |
| BestEffort p50 (secondary) | 988 µs | 885 µs (−10.5%; **not the gate**) |
| loss | 0/400 | 0/400 |

A same-host **repeat** lost the official-run RTT win (BestEffort p95 **1174** / p99 **1262** vs iter7 1148 / 1238) and widened arrival `|I−5 ms|` p95 to **526 µs**. Official-run p50/p95 movement without a held arrival-interval win is **not** a keep.

same-process honesty is not the gate. Stretching SPDP announce does not cut the Python/rclpy IPC tax on the 64 B hot path.

**Reverted.** Landed XML has no `leaseAnnouncement` override (Humble default 3 s). iter7 `healthy_check_timeout_ms` 10000 + iter5 mid-size SHM + sockets + send_buffers stay. Exclusive / oversized SHM stays discarded.

## 1 MiB / mid-size (do not spit those gains)

The probe is discovery-only. **1 MiB / mid-size suite was not remasured under the discarded probe.** Landed XML equals iter7 (`healthy_check_timeout_ms` 10000, 280000 / 2 MiB, sockets, send_buffers), so those gains stay. Prefer-not-regressing 1 MiB is satisfied by revert.

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
- Chain B; cross-host UDP; 《3》《4》《5》《6》
