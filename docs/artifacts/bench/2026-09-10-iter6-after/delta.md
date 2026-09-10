# iter6 delta vs IMU baseline (Chain A only)

Like-to-like: **Chain A** `same-process` and `same-host` only. Same `run_imu_hf.sh` command, size `64`, gap 5 ms (200 Hz), 400 samples, `uint8_multiarray`. Image digest `sha256:fb07245b32187d74350be25323d8ad2f8ca5c25c325759911a1eff2267a49c1e` (same as Step A / iter5).

**Do not** put these numbers in a table with Chain B. **Do not** treat same-host localhost as a Feishu / real-robot / cross-host root cause.

这些对照数字 **不是** 飞书现场、实机、或跨机根因证明。

Change under test (then **reverted**): `shm_midsize` `port_queue_capacity` 512 → 64. See [`change.md`](change.md).

Δ = after − baseline. Negative = faster. Units: microseconds RTT.

## Headline (same-host BestEffort 64 B / 200 Hz — primary)

| case | baseline (Step A) | after (queue 64) | keep? |
|------|-------------------|------------------|-------|
| `ros_high_throughput` 64 B | p50 964.82 µs, p99 1271.9 µs, 0/400 | p50 998.78 µs (**+3.52%**), p99 1272.2 µs, 0/400 | **No** — p50 did not improve; max 1360 → 2729 µs |
| `ros_reliable` 64 B | p50 948.04 µs, 0/400 | p50 947.46 µs (−0.06%), 0/400 | flat |

The probe is **not kept**. Landed `config/fastdds.xml` is the iter5 seed (no `port_queue_capacity` override). Mid-size / 1 MiB knobs are untouched, so those gains are not erased. Exclusive / oversized SHM stays discarded.

Cross-host UDP remains `STATUS: blocked` (single VM). Chain B was **not** remasured.

## Chain A `same-host` (primary vs Step A)

| case | payload (B) | p50 base → after | Δ p50 | p50 % | p95 base → after | Δ p95 | p95 % | p99 base → after | Δ p99 | p99 % |
|------|-------------|------------------|-------|-------|------------------|-------|-------|------------------|-------|-------|
| `ros_high_throughput` | 64 | 964.82 → 998.78 | +33.96 | +3.52% | 1168.5 → 1184.5 | +15.97 | +1.37% | 1271.9 → 1272.2 | +0.369 | +0.03% |
| `ros_reliable` | 64 | 948.04 → 947.46 | −0.582 | −0.06% | 1213.1 → 1190.0 | −23.16 | −1.91% | 1285.0 → 1269.4 | −15.57 | −1.21% |

Timeouts: 0/400 → 0/400 both cases. Effective rate stayed 200 Hz (p50 ≪ 5 ms).

## Chain A `same-process` (honesty check only)

**Do not** tune for this table.

| case | payload (B) | p50 base → after | Δ p50 | p50 % | p95 base → after | Δ p95 | p95 % | p99 base → after | Δ p99 | p99 % |
|------|-------------|------------------|-------|-------|------------------|-------|-------|------------------|-------|-------|
| `ros_high_throughput` | 64 | 588.90 → 611.02 | +22.11 | +3.76% | 664.10 → 690.23 | +26.12 | +3.93% | 715.14 → 744.27 | +29.13 | +4.07% |
| `ros_reliable` | 64 | 605.61 → 614.68 | +9.072 | +1.50% | 685.16 → 692.15 | +6.991 | +1.02% | 740.86 → 717.16 | −23.70 | −3.20% |

Timeouts: 0/400 → 0/400 both cases.

## Reading the tails

- Same-host is the HF bottleneck (Step A BestEffort p50 965 vs 589 µs same-process). This probe did not close that gap.
- Fast-DDS SHM `copy_to_shared_buffer` already copies `total_bytes` (64), not `maxMessageSize` 280000. A shorter port queue does not shrink that copy.
- 1 MiB / mid-size suite was **not** remasured under the discarded probe. Landed XML equals iter5, so those gains stay. Prefer-not-regressing 1 MiB is satisfied by revert.
- XMLPARSER accepted `port_queue_capacity` (empty stderr) — the miss is data-path, not schema.
