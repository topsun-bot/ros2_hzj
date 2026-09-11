# iter8 delta vs iter7 (Chain A only)

Like-to-like: **Chain A** `same-process` and `same-host` only. Same `run_imu_hf.sh` command, size **64 B**, gap **5 ms** (target **200 Hz**), 400 samples, `uint8_multiarray`. Image digest `sha256:fb07245b32187d74350be25323d8ad2f8ca5c25c325759911a1eff2267a49c1e` (same as iter7 / iter6 / iter5).

**Primary metric is jitter** (RTT p95/p99 + inter-message interval variance / `|I − 5 ms|`). p50/mean are secondary. **Do not** claim success from average/p50 alone. **Do not** put these numbers in a table with Chain B. **Do not** treat same-host localhost as a Feishu / real-robot / cross-host root cause.

这些对照数字 **不是** 飞书现场、实机、或跨机根因证明。

Change under test (then **reverted**): default-participant SIMPLE discovery `leaseAnnouncement` 3 s → 15 s. See [`change.md`](change.md). Preferred baseline is [`../2026-09-11-iter7/`](../2026-09-11-iter7/README.md) (post–`healthy_check_timeout_ms` 10000). Continuity vs [`../2026-09-10-iter6-imu-baseline/`](../2026-09-10-iter6-imu-baseline/README.md) is cited below; it is **not** the keep/discard gate.

Δ = after − baseline. Negative = tighter / faster. Units: microseconds.

## Headline (same-host, 64 B / 200 Hz — primary; jitter gate vs iter7)

| case | RTT p95 / p99 | RTT p95−p50 | arrival I stdev | arrival \|I−5 ms\| p95 | keep? |
|------|---------------|-------------|-----------------|------------------------|-------|
| `ros_high_throughput` | 1148 → 1104 (−3.79%) / 1238 → 1145 (−7.48%) | 160 → 220 | 168 → 193 | 375 → 448 | **No** — arrival jitter widened; p95−p50 wider. Repeat p95 1174 / arrival 526 (lost the RTT win) |
| `ros_reliable` | 1173 → 1031 (−12.18%) / 1250 → 1139 (−8.88%) | 203 → 285 | 289 → 238 | 569 → 457 | Mixed on this run; repeat p95 1201 / arrival 513. Not a keep without BestEffort arrival |

Secondary p50 (do **not** use as the gate): BestEffort 988 → 885 µs (−10.48%); Reliable 971 → 746 µs (−23.18%). Both 0/400. A p50-only read would call this “faster”; jitter / repeat says discard.

The probe is **not kept**. Landed `config/fastdds.xml` is the iter7 seed (no `leaseAnnouncement` override; `healthy_check_timeout_ms` 10000 stays). Mid-size / **1 MiB** knobs are untouched, so those gains are not erased. Exclusive / oversized SHM stays discarded.

Cross-host UDP remains `STATUS: blocked` (single VM). Chain B was **not** remasured. 《3》《4》《5》《6》 still Hold.

## Chain A `same-host` (primary vs iter7)

### Jitter (primary)

| case | payload (B) | RTT p95 Δ | RTT p99 Δ | RTT p95−p50 base → after | pub I stdev base → after | pub \|I−tgt\| p95 | pub \|I−tgt\| p99 | arr I stdev | arr \|I−tgt\| p95 |
|------|-------------|-----------|-----------|--------------------------|-------------------------|-----------------|-----------------|-------------|---------------|
| `ros_high_throughput` | 64 | 1147.9 → 1104.4 (-43.50, -3.79%) | 1237.6 → 1145.1 (-92.53, -7.48%) | 159.54 → 219.59 | 44.37 → 34.09 | 180.28 → 171.83 | 263.38 → 212.02 | 167.66 → 193.00 | 375.21 → 448.24 |
| `ros_reliable` | 64 | 1173.4 → 1030.5 (-142.94, -12.18%) | 1249.7 → 1138.7 (-111.00, -8.88%) | 202.90 → 284.91 | 35.45 → 88.43 | 177.88 → 166.43 | 219.72 → 236.06 | 289.35 → 237.54 | 569.21 → 457.02 |

### RTT p50 (secondary — do not use as the keep/discard gate)

| case | payload (B) | p50 base → after | Δ p50 | p50 % | p95 base → after | Δ p95 | p95 % | p99 base → after | Δ p99 | p99 % |
|------|-------------|------------------|-------|-------|------------------|-------|-------|------------------|-------|-------|
| `ros_high_throughput` | 64 | 988.38 → 884.82 | -103.56 | -10.48% | 1147.9 → 1104.4 | -43.50 | -3.79% | 1237.6 → 1145.1 | -92.53 | -7.48% |
| `ros_reliable` | 64 | 970.54 → 745.59 | -224.95 | -23.18% | 1173.4 → 1030.5 | -142.94 | -12.18% | 1249.7 → 1138.7 | -111.00 | -8.88% |

Timeouts: 0/400 → 0/400 both cases. Effective rate stayed 200 Hz (RTT ≪ 5 ms). Publish cadence stayed near 5 ms (pub I p50 ~5091 µs). Arrival-interval jitter is the consumer-facing IMU gap and widened on BestEffort vs iter7.

## Continuity vs iter6 IMU baseline (not the gate)

same-host BestEffort vs [`../2026-09-10-iter6-imu-baseline/`](../2026-09-10-iter6-imu-baseline/README.md): RTT p95 1205 → 1104 (−8.37%); arrival `|I−5 ms|` p95 488 → 448. That continuity still includes the **kept** iter7 health-check win. The iter8 probe on top of iter7 did **not** hold arrival tails; keep/discard is vs iter7.

## Chain A `same-process` (honesty check only)

**Do not** tune for this table. same-process BestEffort p50 589 → 431 is a p50 move with **wider** p95−p50 (66 → 202); not a keep signal.

### Jitter (primary)

| case | payload (B) | RTT p95 Δ | RTT p99 Δ | RTT p95−p50 base → after | pub I stdev base → after | pub \|I−tgt\| p95 | pub \|I−tgt\| p99 | arr I stdev | arr \|I−tgt\| p95 |
|------|-------------|-----------|-----------|--------------------------|-------------------------|-----------------|-----------------|-------------|---------------|
| `ros_high_throughput` | 64 | 655.16 → 633.96 (-21.21, -3.24%) | 724.27 → 661.12 (-63.15, -8.72%) | 66.47 → 202.48 | 34.69 → 33.93 | 187.27 → 176.42 | 238.97 → 234.17 | 73.28 → 99.69 | 242.50 → 271.58 |
| `ros_reliable` | 64 | 651.02 → 639.76 (-11.25, -1.73%) | 689.46 → 704.90 (15.44, +2.24%) | 54.08 → 52.31 | 36.40 → 239.38 | 192.13 → 191.91 | 224.50 → 247.20 | 66.73 → 245.07 | 239.87 → 229.71 |

### RTT p50 (secondary — do not use as the keep/discard gate)

| case | payload (B) | p50 base → after | Δ p50 | p50 % | p95 base → after | Δ p95 | p95 % | p99 base → after | Δ p99 | p99 % |
|------|-------------|------------------|-------|-------|------------------|-------|-------|------------------|-------|-------|
| `ros_high_throughput` | 64 | 588.70 → 431.47 | -157.22 | -26.71% | 655.16 → 633.96 | -21.21 | -3.24% | 724.27 → 661.12 | -63.15 | -8.72% |
| `ros_reliable` | 64 | 596.94 → 587.45 | -9.484 | -1.59% | 651.02 → 639.76 | -11.25 | -1.73% | 689.46 → 704.90 | 15.44 | +2.24% |

Timeouts: 0/400 → 0/400 both cases.

## Reading the tails

- IMU **64 B / 200 Hz** and `healthy_check_timeout_ms` 10000 were already nailed on `main`. same-host is the HF bottleneck (iter7 BestEffort RTT p95 1148 vs 655 µs same-process).
- The official run moved BestEffort RTT p95/p99 the right way but **widened arrival `|I − 5 ms|` and p95−p50**. That is not a keep.
- A same-host repeat lost the RTT tail win and widened arrival further. Treat the official p50/p95 drop as VM noise, not a data-path win.
- Fast-DDS SIMPLE discovery still announces after initial bursts. Stretching `leaseAnnouncement` to 15 s does not change `alloc_buffer(total_bytes)` (64) or `maxMessageSize` 280000.
- **1 MiB / mid-size suite was not remasured under the discarded probe.** Landed XML equals iter7, so those gains stay. Exclusive / oversized SHM stays discarded.
- XMLPARSER accepted `leaseAnnouncement` (empty stderr) — the miss is data-path / noise, not schema.
