# iter4 delta vs iter3 (Chain A only)

Like-to-like: **Chain A** `same-process` and `same-host` only. Same `run_large_packet.sh` command, sizes `102400,262144,1048576`, gap 100 ms, 80 samples, `uint8_multiarray`. Image digest `sha256:fb07245b32187d74350be25323d8ad2f8ca5c25c325759911a1eff2267a49c1e` (same as iter3 / iter2-after).

**Do not** put these numbers in a table with Chain B. **Do not** treat same-host localhost as a Feishu / real-robot / cross-host root cause.

这些对照数字 **不是** 飞书现场、实机、或跨机根因证明。

Change under test: default-participant RTPS send-buffer pool `preallocated_number=32` kept, `dynamic` true → **false** in `config/fastdds.xml`. See [`change.md`](change.md).

Δ = after − baseline. Negative = faster. Units: microseconds RTT.

## Headline (same-host mid-size — primary; 1 MiB must hold)

| case | baseline (iter3) | after (iter4) | vs iter2-after (honesty) |
|------|------------------|---------------|--------------------------|
| `ros_reliable` 102400 B | p50 1393.3 µs | p50 1263.8 µs (**−9.29%**) | 1129.8 → 1263.8 (**+11.9%**, was **+23.3%** in iter3) |
| `ros_reliable` 262144 B | p50 1693.1 µs | p50 1556.1 µs (**−8.09%**) | 1362.6 → 1556.1 (**+14.2%**, was **+24.3%** in iter3) |
| `ros_high_throughput` 102400 B | p50 1257.9 µs | p50 1214.4 µs (**−3.45%**) | 1146.2 → 1214.4 (**+6.0%**, was **+9.8%** in iter3) |
| `ros_high_throughput` 262144 B | p50 1591.9 µs | p50 1652.6 µs (**+3.81%**) | 1463.4 → 1652.6 (**+12.9%**, was **+8.8%** in iter3) — **not recovered** |
| `ros_high_throughput` 1048576 B | 80/80, p50 2935.2 µs | 80/80, p50 3001.9 µs (**+2.27%**, within noise of iter3) | 3906.1 → 3001.9 (**−23.2%**) |
| `ros_reliable` 1048576 B | 80/80, p50 3178.2 µs | 80/80, p50 2917.0 µs (**−8.22%**) | 3304.9 → 2917.0 (**−11.7%**) |

The change is **kept** for same-host **Reliable 100/256 KiB** p50/p95 (the booked +23–24% tax). BestEffort 100 KiB nudged back; BestEffort 256 KiB did **not** recover vs iter2-after and is reported honestly. Same-host 1 MiB BestEffort p50 stayed within ~2% of iter3; Reliable 1 MiB improved. This still does not prove field root cause.

**Not kept:** `preallocated_number` 32 → 16 and 32 → 0 with `dynamic` still true. 16 did not recover mid-size. 0 erased the 1 MiB win (BestEffort 2935 → 5075 µs). See [`change.md`](change.md).

Cross-host UDP remains `STATUS: blocked` (single VM) — no percentile delta. Chain B was **not** remasured (knob is Chain A XML only).

## Chain A `same-host` (primary vs iter3)

Matching cases only. Mid-size Reliable is the treatment target. 1 MiB must stay near iter3.

| case | payload (B) | p50 base → after | Δ p50 | p50 % | p95 base → after | Δ p95 | p95 % | p99 base → after | Δ p99 | p99 % |
|------|-------------|------------------|-------|-------|------------------|-------|-------|------------------|-------|-------|
| `ros_high_throughput` | 102400 | 1257.9 → 1214.4 | −43.45 | −3.45% | 1529.3 → 1387.0 | −142.31 | −9.31% | 1594.6 → 1683.0 | +88.38 | +5.54% |
| `ros_high_throughput` | 262144 | 1591.9 → 1652.6 | +60.73 | +3.81% | 1888.4 → 1839.8 | −48.64 | −2.58% | 2015.4 → 1867.2 | −148.27 | −7.36% |
| `ros_high_throughput` | 1048576 | 2935.2 → 3001.9 | +66.67 | +2.27% | 3417.5 → 3411.1 | −6.423 | −0.19% | 4499.4 → 3451.1 | −1048.4 | **−23.30%** |
| `ros_reliable` | 102400 | 1393.3 → 1263.8 | −129.51 | **−9.29%** | 1726.9 → 1466.3 | −260.53 | −15.09% | 1774.2 → 1483.4 | −290.89 | −16.39% |
| `ros_reliable` | 262144 | 1693.1 → 1556.1 | −137.04 | **−8.09%** | 2031.5 → 1891.7 | −139.74 | −6.88% | 2133.5 → 1948.5 | −185.00 | −8.67% |
| `ros_reliable` | 1048576 | 3178.2 → 2917.0 | −261.19 | **−8.22%** | 3671.8 → 3327.7 | −344.11 | −9.37% | 3887.4 → 3594.0 | −293.36 | −7.55% |

## Chain A `same-host` vs iter2-after (mid-size honesty)

How much of the booked regression is still on the books. Not a second treatment. Negative vs this table would be “fully back”; we are not there.

| case | payload (B) | p50 i2-after → iter4 | Δ p50 | p50 % | iter3 vs i2-after p50 % |
|------|-------------|----------------------|-------|-------|-------------------------|
| `ros_high_throughput` | 102400 | 1146.2 → 1214.4 | +68.26 | +5.96% | +9.75% |
| `ros_high_throughput` | 262144 | 1463.4 → 1652.6 | +189.25 | +12.93% | +8.78% |
| `ros_high_throughput` | 1048576 | 3906.1 → 3001.9 | −904.21 | **−23.15%** | −24.86% |
| `ros_reliable` | 102400 | 1129.8 → 1263.8 | +133.96 | +11.86% | +23.32% |
| `ros_reliable` | 262144 | 1362.6 → 1556.1 | +193.45 | +14.20% | +24.25% |
| `ros_reliable` | 1048576 | 3304.9 → 2917.0 | −387.92 | **−11.74%** | −3.83% |

## Chain A `same-process` (honesty check only)

Matching cases only. **Do not** tune for this table. Mid-size and 1 MiB both moved faster vs iter3; that is consistent with avoiding a hot-path grow, but this is not a same-host claim.

| case | payload (B) | p50 base → after | Δ p50 | p50 % | p95 base → after | Δ p95 | p95 % | p99 base → after | Δ p99 | p99 % |
|------|-------------|------------------|-------|-------|------------------|-------|-------|------------------|-------|-------|
| `ros_high_throughput` | 102400 | 860.32 → 824.83 | −35.49 | −4.12% | 1049.0 → 899.03 | −149.95 | −14.30% | 1402.5 → 948.15 | −454.30 | −32.39% |
| `ros_high_throughput` | 262144 | 1019.7 → 935.55 | −84.20 | −8.26% | 1215.5 → 1047.7 | −167.85 | −13.81% | 1311.4 → 1070.0 | −241.39 | −18.41% |
| `ros_high_throughput` | 1048576 | 1862.1 → 1615.4 | −246.72 | −13.25% | 2071.5 → 1794.5 | −276.99 | −13.37% | 2119.4 → 1854.9 | −264.57 | −12.48% |
| `ros_reliable` | 102400 | 904.18 → 818.44 | −85.75 | −9.48% | 1053.8 → 908.50 | −145.26 | −13.78% | 1156.1 → 951.99 | −204.13 | −17.66% |
| `ros_reliable` | 262144 | 1009.0 → 906.80 | −102.22 | −10.13% | 1201.8 → 1030.3 | −171.55 | −14.27% | 1323.7 → 1087.2 | −236.52 | −17.87% |
| `ros_reliable` | 1048576 | 1631.1 → 1596.3 | −34.85 | −2.14% | 1947.4 → 1738.7 | −208.69 | −10.72% | 2012.2 → 1870.6 | −141.60 | −7.04% |

## Reading the tails

- Same-host Reliable 100/256 KiB p50 −8–9% vs iter3 is the material mid-size result (about half the booked +23–24% vs iter2-after).
- Same-host BestEffort 256 KiB p50 did not recover vs iter2-after; do not claim all mid-size rows moved.
- Same-host 1 MiB BestEffort p50 +2.3% vs iter3 is treated as noise; the iter2-after 1 MiB BestEffort win (−23%) is still there. Reliable 1 MiB is faster than both iter3 and iter2-after.
- Same-host 1 MiB BestEffort p99 −23% vs iter3 (4499 → 3451 µs) is a tail improvement, not the treatment target.
- Same-process moving with mid-size is an honesty check, not a reason to chase intra-process noise.
- XMLPARSER: remasure ping-pong stderr is empty (no `send_buffers` / `preallocated_number` / `dynamic` parse errors).
- Shrinking the 32-slab (16 / 0, `dynamic` still true) was **not** kept. Additive / exclusive SHM stays discarded.
