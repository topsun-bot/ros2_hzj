# iter6 delta vs IMU baseline (Chain A only)

Like-to-like: **Chain A** `same-process` and `same-host` only. Same `run_imu_hf.sh` command, size **64 B**, gap **5 ms** (target **200 Hz**), 400 samples, `uint8_multiarray`. Image digest `sha256:fb07245b32187d74350be25323d8ad2f8ca5c25c325759911a1eff2267a49c1e` (same as Step A / iter5).

**Primary metric is jitter** (RTT p95/p99 + inter-message interval variance / `|I − 5 ms|`). p50/mean are secondary. **Do not** claim success from average/p50 alone. **Do not** put these numbers in a table with Chain B. **Do not** treat same-host localhost as a Feishu / real-robot / cross-host root cause.

这些对照数字 **不是** 飞书现场、实机、或跨机根因证明。

Change under test (then **reverted**): `shm_midsize` `port_queue_capacity` 512 → 64. See [`change.md`](change.md).

Δ = after − baseline. Negative = tighter / faster. Units: microseconds.

## Headline (same-host, 64 B / 200 Hz — primary; jitter gate)

| case | RTT p95 / p99 | RTT p95−p50 | arrival I stdev | arrival \|I−5 ms\| p95 | keep? |
|------|---------------|-------------|-----------------|------------------------|-------|
| `ros_high_throughput` | 1205 → 1234 (**+2.38%**) / 1336 → 1384 (**+3.58%**) | 248 → 273 | 218 → 256 | 488 → 568 | **No** — tails and arrival jitter widened |
| `ros_reliable` | 1161 → 1200 (**+3.32%**) / 1286 → 1269 (−1.32%) | 258 → 279 | 224 → 271 | 492 → 585 | **No** — p95 and arrival jitter worse; p99 alone is not a keep |

Secondary p50 (do **not** use as the gate): BestEffort 957 → 961 µs (+0.37%); Reliable 903 → 921 µs (+1.98%). Both 0/400. A p50-only read would call this “flat”; jitter says discard.

The probe is **not kept**. Landed `config/fastdds.xml` is the iter5 seed (no `port_queue_capacity` override). Mid-size / **1 MiB** knobs are untouched, so those gains are not erased. Exclusive / oversized SHM stays discarded.

Cross-host UDP remains `STATUS: blocked` (single VM). Chain B was **not** remasured. 《3》《4》《5》《6》 still Hold.

## Chain A `same-host` (primary vs Step A)

### Jitter (primary)

| case | payload (B) | RTT p95 Δ | RTT p99 Δ | RTT p95−p50 base → after | pub I stdev base → after | pub \|I−tgt\| p95 | pub \|I−tgt\| p99 | arr I stdev | arr \|I−tgt\| p95 |
|------|-------------|-----------|-----------|--------------------------|-------------------------|-----------------|-----------------|-------------|---------------|
| `ros_high_throughput` | 64 | 1205.3 → 1234.0 (28.66, +2.38%) | 1335.6 → 1383.5 (47.87, +3.58%) | 248.17 → 273.32 | 53.06 → 63.02 | 225.22 → 237.96 | 266.12 → 318.29 | 218.17 → 255.70 | 487.78 → 567.58 |
| `ros_reliable` | 64 | 1161.3 → 1199.9 (38.56, +3.32%) | 1286.2 → 1269.3 (-16.99, -1.32%) | 258.08 → 278.75 | 56.44 → 52.73 | 242.16 → 219.66 | 279.03 → 281.16 | 224.05 → 271.37 | 491.65 → 584.90 |

### RTT p50 (secondary — do not use as the keep/discard gate)

| case | payload (B) | p50 base → after | Δ p50 | p50 % | p95 base → after | Δ p95 | p95 % | p99 base → after | Δ p99 | p99 % |
|------|-------------|------------------|-------|-------|------------------|-------|-------|------------------|-------|-------|
| `ros_high_throughput` | 64 | 957.12 → 960.64 | 3.515 | +0.37% | 1205.3 → 1234.0 | 28.66 | +2.38% | 1335.6 → 1383.5 | 47.87 | +3.58% |
| `ros_reliable` | 64 | 903.24 → 921.12 | 17.88 | +1.98% | 1161.3 → 1199.9 | 38.56 | +3.32% | 1286.2 → 1269.3 | -16.99 | -1.32% |

Timeouts: 0/400 → 0/400 both cases. Effective rate stayed 200 Hz (RTT ≪ 5 ms). Publish cadence stayed near 5 ms (pub I p50 ~5090 µs). Arrival-interval jitter is the consumer-facing IMU gap and got worse.

## Chain A `same-process` (honesty check only)

**Do not** tune for this table. same-process BestEffort arrival stdev 360 → 111 is a baseline outlier, not a keep signal.

### Jitter (primary)

| case | payload (B) | RTT p95 Δ | RTT p99 Δ | RTT p95−p50 base → after | pub I stdev base → after | pub \|I−tgt\| p95 | pub \|I−tgt\| p99 | arr I stdev | arr \|I−tgt\| p95 |
|------|-------------|-----------|-----------|--------------------------|-------------------------|-----------------|-----------------|-------------|---------------|
| `ros_high_throughput` | 64 | 732.52 → 723.49 (-9.034, -1.23%) | 806.08 → 779.13 (-26.95, -3.34%) | 125.06 → 100.89 | 339.77 → 53.30 | 238.89 → 237.92 | 304.29 → 270.58 | 360.45 → 110.90 | 334.46 → 297.74 |
| `ros_reliable` | 64 | 718.71 → 711.59 (-7.123, -0.99%) | 799.50 → 817.14 (17.64, +2.21%) | 107.12 → 99.82 | 50.35 → 56.35 | 221.76 → 228.81 | 287.17 → 314.16 | 115.98 → 110.32 | 306.93 → 308.80 |

### RTT p50 (secondary — do not use as the keep/discard gate)

| case | payload (B) | p50 base → after | Δ p50 | p50 % | p95 base → after | Δ p95 | p95 % | p99 base → after | Δ p99 | p99 % |
|------|-------------|------------------|-------|-------|------------------|-------|-------|------------------|-------|-------|
| `ros_high_throughput` | 64 | 607.46 → 622.60 | 15.14 | +2.49% | 732.52 → 723.49 | -9.034 | -1.23% | 806.08 → 779.13 | -26.95 | -3.34% |
| `ros_reliable` | 64 | 611.60 → 611.77 | 0.173 | +0.03% | 718.71 → 711.59 | -7.123 | -0.99% | 799.50 → 817.14 | 17.64 | +2.21% |

Timeouts: 0/400 → 0/400 both cases.

## Reading the tails

- Step A nailed **64 B / 200 Hz** before any knob. same-host is the HF bottleneck (baseline BestEffort RTT p95 1205 vs 733 µs same-process; p95−p50 248 vs 125 µs).
- The probe did **not** tighten same-host jitter. BestEffort p95/p99 and arrival `|I − 5 ms|` all moved the wrong way.
- Fast-DDS SHM `copy_to_shared_buffer` already copies `total_bytes` (64), not `maxMessageSize` 280000. A shorter port queue does not shrink that copy.
- **1 MiB / mid-size suite was not remasured under the discarded probe.** Landed XML equals iter5, so those gains stay. Prefer-not-regressing 1 MiB is satisfied by revert. Exclusive / oversized SHM stays discarded.
- XMLPARSER accepted `port_queue_capacity` (empty stderr) — the miss is data-path, not schema.
