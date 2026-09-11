# iter9 delta vs iter7 (Chain A only)

Like-to-like: **Chain A** `same-process` and `same-host` only. Same `run_imu_hf.sh` command, size **64 B**, gap **5 ms** (target **200 Hz**), 400 samples, `uint8_multiarray`. Image digest `sha256:fb07245b32187d74350be25323d8ad2f8ca5c25c325759911a1eff2267a49c1e` (same as iter8 / iter7 / iter6 / iter5).

**Primary metric is jitter** (RTT p95/p99 + inter-message interval variance / `|I − 5 ms|`). p50/mean are secondary. **Do not** claim success from average/p50 alone. **Do not** put these numbers in a table with Chain B. **Do not** treat same-host localhost as a Feishu / real-robot / cross-host root cause.

这些对照数字 **不是** 飞书现场、实机、或跨机根因证明。

Change under test (then **reverted**): default-participant `use_WriterLivelinessProtocol` true → false. See [`change.md`](change.md). Preferred baseline is [`../2026-09-11-iter7/`](../2026-09-11-iter7/README.md) (post–`healthy_check_timeout_ms` 10000; same landed XML as iter8 after revert). Continuity vs [`../2026-09-10-iter6-imu-baseline/`](../2026-09-10-iter6-imu-baseline/README.md) is cited below; it is **not** the keep/discard gate.

Δ = after − baseline. Negative = tighter / faster. Units: microseconds.

## Headline (same-host, 64 B / 200 Hz — primary; jitter gate vs iter7)

| case | RTT p95 / p99 | RTT p95−p50 | arrival I stdev | arrival \|I−5 ms\| p95 | keep? |
|------|---------------|-------------|-----------------|------------------------|-------|
| `ros_high_throughput` | 1148 → 1148 (+0.03%) / 1238 → 1253 (+1.21%) | 160 → 223 | 168 → 325 | 375 → 543 | **No** — arrival jitter widened; p95−p50 wider. Repeat p95 1115 / arrival 413 (arrival still wide) |
| `ros_reliable` | 1173 → 1197 (+1.98%) / 1250 → 1312 (+5.00%) | 203 → 255 | 289 → 405 | 569 → 587 | Worse tails; not a keep without BestEffort arrival |

Secondary p50 (do **not** use as the gate): BestEffort 988 → 925 µs (−6.41%); Reliable 971 → 941 µs (−3.02%). Both 0/400. A p50-only read would call this “faster”; jitter / repeat says discard.

The probe is **not kept**. Landed `config/fastdds.xml` is the iter7 seed (no WLP override; `healthy_check_timeout_ms` 10000 stays). Mid-size / **1 MiB** knobs are untouched, so those gains are not erased. Exclusive / oversized SHM stays discarded.

Cross-host UDP remains `STATUS: blocked` (single VM). Chain B was **not** remasured. 《3》《4》《5》《6》 still Hold.

## Chain A `same-host` (primary vs iter7)

### Jitter (primary)

| case | payload (B) | RTT p95 Δ | RTT p99 Δ | RTT p95−p50 base → after | pub I stdev base → after | pub \|I−tgt\| p95 | pub \|I−tgt\| p99 | arr I stdev | arr \|I−tgt\| p95 |
|------|-------------|-----------|-----------|--------------------------|-------------------------|-----------------|-----------------|-------------|---------------|
| `ros_high_throughput` | 64 | 1147.9 → 1148.3 (0.360, +0.03%) | 1237.6 → 1252.6 (14.96, +1.21%) | 159.54 → 223.27 | 44.37 → 222.47 | 180.28 → 210.34 | 263.38 → 287.37 | 167.66 → 325.41 | 375.21 → 542.90 |
| `ros_reliable` | 64 | 1173.4 → 1196.7 (23.25, +1.98%) | 1249.7 → 1312.2 (62.52, +5.00%) | 202.90 → 255.45 | 35.45 → 76.83 | 177.88 → 213.44 | 219.72 → 253.22 | 289.35 → 404.67 | 569.21 → 587.49 |

### RTT p50 (secondary — do not use as the keep/discard gate)

| case | payload (B) | p50 base → after | Δ p50 | p50 % | p95 base → after | Δ p95 | p95 % | p99 base → after | Δ p99 | p99 % |
|------|-------------|------------------|-------|-------|------------------|-------|-------|------------------|-------|-------|
| `ros_high_throughput` | 64 | 988.38 → 925.01 | -63.37 | -6.41% | 1147.9 → 1148.3 | 0.360 | +0.03% | 1237.6 → 1252.6 | 14.96 | +1.21% |
| `ros_reliable` | 64 | 970.54 → 941.24 | -29.30 | -3.02% | 1173.4 → 1196.7 | 23.25 | +1.98% | 1249.7 → 1312.2 | 62.52 | +5.00% |

Timeouts: 0/400 → 0/400 both cases. Effective rate stayed 200 Hz (RTT ≪ 5 ms). Publish cadence stayed near 5 ms (pub I p50 ~5086 µs). Arrival-interval jitter is the consumer-facing IMU gap and widened on BestEffort vs iter7.

## Continuity vs iter6 IMU baseline (not the gate)

same-host BestEffort vs [`../2026-09-10-iter6-imu-baseline/`](../2026-09-10-iter6-imu-baseline/README.md): RTT p95 1205 → 1148 (flat vs iter7); arrival `|I−5 ms|` p95 488 → 543. That continuity still includes the **kept** iter7 health-check win on RTT p95, but arrival is worse than both iter6-imu-baseline and iter7. Keep/discard is vs iter7.

## Chain A `same-process` (honesty check only)

**Do not** tune for this table. same-process BestEffort p50 589 → 588 is flat; arrival 243 → 240 is not a keep signal.

### Jitter (primary)

| case | payload (B) | RTT p95 Δ | RTT p99 Δ | RTT p95−p50 base → after | pub I stdev base → after | pub \|I−tgt\| p95 | pub \|I−tgt\| p99 | arr I stdev | arr \|I−tgt\| p95 |
|------|-------------|-----------|-----------|--------------------------|-------------------------|-----------------|-----------------|-------------|---------------|
| `ros_high_throughput` | 64 | 655.16 → 659.54 (4.375, +0.67%) | 724.27 → 704.88 (-19.39, -2.68%) | 66.47 → 71.97 | 34.69 → 41.10 | 187.27 → 209.16 | 238.97 → 248.84 | 73.28 → 72.27 | 242.50 → 240.36 |
| `ros_reliable` | 64 | 651.02 → 659.75 (8.736, +1.34%) | 689.46 → 702.33 (12.87, +1.87%) | 54.08 → 75.33 | 36.40 → 44.23 | 192.13 → 197.76 | 224.50 → 253.99 | 66.73 → 80.43 | 239.87 → 251.13 |

### RTT p50 (secondary — do not use as the keep/discard gate)

| case | payload (B) | p50 base → after | Δ p50 | p50 % | p95 base → after | Δ p95 | p95 % | p99 base → after | Δ p99 | p99 % |
|------|-------------|------------------|-------|-------|------------------|-------|-------|------------------|-------|-------|
| `ros_high_throughput` | 64 | 588.70 → 587.57 | -1.124 | -0.19% | 655.16 → 659.54 | 4.375 | +0.67% | 724.27 → 704.88 | -19.39 | -2.68% |
| `ros_reliable` | 64 | 596.94 → 584.42 | -12.51 | -2.10% | 651.02 → 659.75 | 8.736 | +1.34% | 689.46 → 702.33 | 12.87 | +1.87% |

Timeouts: 0/400 → 0/400 both cases.

## Reading the tails

- IMU **64 B / 200 Hz** and `healthy_check_timeout_ms` 10000 were already nailed on `main`. same-host is the HF bottleneck (iter7 BestEffort RTT p95 1148 vs 655 µs same-process).
- The official run left BestEffort RTT p95 flat and **widened arrival `|I − 5 ms|` and p95−p50**. That is not a keep.
- A same-host repeat recovered some RTT tail (p95 1115) but arrival stayed wide (413 vs 375). Treat the official p50 drop as VM noise / not a data-path win.
- Fast-DDS WLP is a builtin writer/reader pair. Turning it off does not change `alloc_buffer(total_bytes)` (64) or `maxMessageSize` 280000.
- **1 MiB / mid-size suite was not remasured under the discarded probe.** Landed XML equals iter7, so those gains stay. Exclusive / oversized SHM stays discarded.
- XMLPARSER accepted `use_WriterLivelinessProtocol` (empty stderr) — the miss is data-path / noise, not schema.
- Do **not** probe `leaseAnnouncement` / `leaseDuration` again (iter8 discarded).
