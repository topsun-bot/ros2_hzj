# iter7 delta vs IMU baseline (Chain A only)

Like-to-like: **Chain A** `same-process` and `same-host` only. Same `run_imu_hf.sh` command, size **64 B**, gap **5 ms** (target **200 Hz**), 400 samples, `uint8_multiarray`. Image digest `sha256:fb07245b32187d74350be25323d8ad2f8ca5c25c325759911a1eff2267a49c1e` (same as Step A / iter6 / iter5).

**Primary metric is jitter** (RTT p95/p99 + inter-message interval variance / `|I − 5 ms|`). p50/mean are secondary. **Do not** claim success from average/p50 alone. **Do not** put these numbers in a table with Chain B. **Do not** treat same-host localhost as a Feishu / real-robot / cross-host root cause.

这些对照数字 **不是** 飞书现场、实机、或跨机根因证明。

Change under test (**kept**): `shm_midsize` `healthy_check_timeout_ms` 1000 → 10000. See [`change.md`](change.md).

Δ = after − baseline. Negative = tighter / faster. Units: microseconds.

## Headline (same-host, 64 B / 200 Hz — primary; jitter gate)

| case | RTT p95 / p99 | RTT p95−p50 | arrival I stdev | arrival \|I−5 ms\| p95 | keep? |
|------|---------------|-------------|-----------------|------------------------|-------|
| `ros_high_throughput` | 1205 → 1148 (**−4.76%**) / 1336 → 1238 (**−7.34%**) | 248 → 160 | 218 → 168 | 488 → 375 | **Yes** — tails and arrival jitter tightened |
| `ros_reliable` | 1161 → 1173 (+1.04%) / 1286 → 1250 (**−2.84%**) | 258 → 203 | 224 → 289 | 492 → 569 | Mixed on this run; repeat p95 1159 / arrival 501 (flat). Not a discard |

Secondary p50 (do **not** use as the gate): BestEffort 957 → 988 µs (+3.27%); Reliable 903 → 971 µs (+7.45%). Both 0/400. A p50-only read would call this “slower”; jitter says keep.

The probe is **kept**. Landed `config/fastdds.xml` adds `healthy_check_timeout_ms` 10000 on `shm_midsize`. Mid-size / **1 MiB** knobs are untouched (280000 / 2 MiB, sockets, send_buffers). Same-host large-packet spot vs iter5: BestEffort 1 MiB 2312 → 2301 µs p50 (80/80); BestEffort 256 KiB 1346 → 1305 µs. Exclusive / oversized SHM stays discarded.

Cross-host UDP remains `STATUS: blocked` (single VM). Chain B was **not** remasured. 《3》《4》《5》《6》 still Hold.

## Chain A `same-host` (primary vs iter6 IMU baseline)

### Jitter (primary)

| case | payload (B) | RTT p95 Δ | RTT p99 Δ | RTT p95−p50 base → after | pub I stdev base → after | pub \|I−tgt\| p95 | pub \|I−tgt\| p99 | arr I stdev | arr \|I−tgt\| p95 |
|------|-------------|-----------|-----------|--------------------------|-------------------------|-----------------|-----------------|-------------|---------------|
| `ros_high_throughput` | 64 | 1205.3 → 1147.9 (-57.38, -4.76%) | 1335.6 → 1237.6 (-97.97, -7.34%) | 248.17 → 159.54 | 53.06 → 44.37 | 225.22 → 180.28 | 266.12 → 263.38 | 218.17 → 167.66 | 487.78 → 375.21 |
| `ros_reliable` | 64 | 1161.3 → 1173.4 (12.12, +1.04%) | 1286.2 → 1249.7 (-36.57, -2.84%) | 258.08 → 202.90 | 56.44 → 35.45 | 242.16 → 177.88 | 279.03 → 219.72 | 224.05 → 289.35 | 491.65 → 569.21 |

### RTT p50 (secondary — do not use as the keep/discard gate)

| case | payload (B) | p50 base → after | Δ p50 | p50 % | p95 base → after | Δ p95 | p95 % | p99 base → after | Δ p99 | p99 % |
|------|-------------|------------------|-------|-------|------------------|-------|-------|------------------|-------|-------|
| `ros_high_throughput` | 64 | 957.12 → 988.38 | 31.25 | +3.27% | 1205.3 → 1147.9 | -57.38 | -4.76% | 1335.6 → 1237.6 | -97.97 | -7.34% |
| `ros_reliable` | 64 | 903.24 → 970.54 | 67.30 | +7.45% | 1161.3 → 1173.4 | 12.12 | +1.04% | 1286.2 → 1249.7 | -36.57 | -2.84% |

Timeouts: 0/400 → 0/400 both cases. Effective rate stayed 200 Hz (RTT ≪ 5 ms). Publish cadence stayed near 5 ms (pub I p50 ~5094 µs). Arrival-interval jitter is the consumer-facing IMU gap and tightened on BestEffort.

## Chain A `same-process` (honesty check only)

**Do not** tune for this table. same-process BestEffort arrival stdev 360 → 73 follows the iter6 baseline outlier, not a keep signal.

### Jitter (primary)

| case | payload (B) | RTT p95 Δ | RTT p99 Δ | RTT p95−p50 base → after | pub I stdev base → after | pub \|I−tgt\| p95 | pub \|I−tgt\| p99 | arr I stdev | arr \|I−tgt\| p95 |
|------|-------------|-----------|-----------|--------------------------|-------------------------|-----------------|-----------------|-------------|---------------|
| `ros_high_throughput` | 64 | 732.52 → 655.16 (-77.36, -10.56%) | 806.08 → 724.27 (-81.81, -10.15%) | 125.06 → 66.47 | 339.77 → 34.69 | 238.89 → 187.27 | 304.29 → 238.97 | 360.45 → 73.28 | 334.46 → 242.50 |
| `ros_reliable` | 64 | 718.71 → 651.02 (-67.70, -9.42%) | 799.50 → 689.46 (-110.04, -13.76%) | 107.12 → 54.08 | 50.35 → 36.40 | 221.76 → 192.13 | 287.17 → 224.50 | 115.98 → 66.73 | 306.93 → 239.87 |

### RTT p50 (secondary — do not use as the keep/discard gate)

| case | payload (B) | p50 base → after | Δ p50 | p50 % | p95 base → after | Δ p95 | p95 % | p99 base → after | Δ p99 | p99 % |
|------|-------------|------------------|-------|-------|------------------|-------|-------|------------------|-------|-------|
| `ros_high_throughput` | 64 | 607.46 → 588.70 | -18.77 | -3.09% | 732.52 → 655.16 | -77.36 | -10.56% | 806.08 → 724.27 | -81.81 | -10.15% |
| `ros_reliable` | 64 | 611.60 → 596.94 | -14.66 | -2.40% | 718.71 → 651.02 | -67.70 | -9.42% | 799.50 → 689.46 | -110.04 | -13.76% |

Timeouts: 0/400 → 0/400 both cases.

## Reading the tails

- IMU **64 B / 200 Hz** was already nailed on `main`. same-host is the HF bottleneck (baseline BestEffort RTT p95 1205 vs 733 µs same-process; p95−p50 248 vs 125 µs).
- The probe **tightened** same-host BestEffort jitter. p95/p99 and arrival `|I − 5 ms|` all moved the right way. p50 rose slightly — that is **not** a discard.
- A same-host repeat held BestEffort (p95 1153 / arrival 387). Reliable arrival 569 on the official run vs 501 on the repeat (baseline 492) is treated as noise.
- Fast-DDS SHM health-check default is 1000 ms. Stretching it to 10 s does not change `alloc_buffer(total_bytes)` (64) or `maxMessageSize` 280000.
- **1 MiB / mid-size like-to-like same-host spot vs iter5 stayed flat** (BestEffort 1 MiB 2312 → 2301 µs p50, 80/80). A 1 MiB-only cold run is not that table. Exclusive / oversized SHM stays discarded.
- XMLPARSER accepted `healthy_check_timeout_ms` (empty stderr) — the win is data-path, not schema.
