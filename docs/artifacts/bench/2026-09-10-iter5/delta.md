# iter5 delta vs iter4 (Chain A only)

Like-to-like: **Chain A** `same-process` and `same-host` only. Same `run_large_packet.sh` command, sizes `102400,262144,1048576`, gap 100 ms, 80 samples, `uint8_multiarray`. Image digest `sha256:fb07245b32187d74350be25323d8ad2f8ca5c25c325759911a1eff2267a49c1e` (same as iter4 / iter3 / iter2-after).

**Do not** put these numbers in a table with Chain B. **Do not** treat same-host localhost as a Feishu / real-robot / cross-host root cause.

这些对照数字 **不是** 飞书现场、实机、或跨机根因证明。

Change under test: additive user SHM `maxMessageSize=280000`, `segment_size=2097152`; builtin UDP+SHM kept. See [`change.md`](change.md).

Δ = after − baseline. Negative = faster. Units: microseconds RTT.

## Headline (same-host BestEffort 256 KiB — primary; 1 MiB must hold)

| case | baseline (iter4) | after (iter5) | vs iter2-after (honesty) |
|------|------------------|---------------|--------------------------|
| `ros_high_throughput` 262144 B | p50 1652.6 µs | p50 1345.9 µs (**−18.56%**) | 1463.4 → 1345.9 (**−8.03%**) — recovered past iter2-after |
| `ros_high_throughput` 102400 B | p50 1214.4 µs | p50 1153.9 µs (**−4.99%**) | 1146.2 → 1153.9 (**+0.67%**, noise of iter2-after) |
| `ros_reliable` 102400 B | p50 1263.8 µs | p50 1143.4 µs (**−9.52%**) | 1129.8 → 1143.4 (**+1.20%**) |
| `ros_reliable` 262144 B | p50 1556.1 µs | p50 1353.4 µs (**−13.02%**) | 1362.6 → 1353.4 (**−0.68%**) |
| `ros_high_throughput` 1048576 B | 80/80, p50 3001.9 µs | 80/80, p50 2312.2 µs (**−22.98%**) | 3906.1 → 2312.2 (**−40.81%**) |
| `ros_reliable` 1048576 B | 80/80, p50 2917.0 µs | 80/80, p50 2368.5 µs (**−18.80%**) | 3304.9 → 2368.5 (**−28.33%**) |

The change is **kept** for same-host **BestEffort 256 KiB** (the booked leftover). 100 KiB BestEffort moved with it. Reliable mid-size recovery from iter4 is kept and extended. Same-host 1 MiB BestEffort/Reliable improved (did not regress). 1 MiB fragments can use the 2 MiB additive segment; that is a consequence of this one knob, not a second treatment. This still does not prove field root cause.

**Not kept:** exclusive UDP+SHM with `segment_size=768 KiB` (BestEffort 256 KiB 1653 → 1309 µs, but BestEffort 1 MiB **80/80 → 1/80**). UDP-only / no SHM (BestEffort 256 KiB flat; BestEffort 1 MiB **0/90**). See [`change.md`](change.md).

Cross-host UDP remains `STATUS: blocked` (single VM) — no percentile delta. Chain B was **not** remasured (knob is Chain A XML only).

## Chain A `same-host` (primary vs iter4)

Matching cases only. BestEffort 256 KiB is the treatment target. 1 MiB must stay near iter4 or better.

| case | payload (B) | p50 base → after | Δ p50 | p50 % | p95 base → after | Δ p95 | p95 % | p99 base → after | Δ p99 | p99 % |
|------|-------------|------------------|-------|-------|------------------|-------|-------|------------------|-------|-------|
| `ros_high_throughput` | 102400 | 1214.4 → 1153.9 | −60.57 | −4.99% | 1387.0 → 1355.7 | −31.28 | −2.25% | 1683.0 → 1448.6 | −234.34 | −13.92% |
| `ros_high_throughput` | 262144 | 1652.6 → 1345.9 | −306.76 | **−18.56%** | 1839.8 → 1541.1 | −298.68 | −16.23% | 1867.2 → 1583.1 | −284.06 | −15.21% |
| `ros_high_throughput` | 1048576 | 3001.9 → 2312.2 | −689.70 | **−22.98%** | 3411.1 → 2841.0 | −570.01 | −16.71% | 3451.1 → 3138.2 | −312.84 | −9.07% |
| `ros_reliable` | 102400 | 1263.8 → 1143.4 | −120.36 | −9.52% | 1466.3 → 1290.4 | −175.92 | −12.00% | 1483.4 → 1332.8 | −150.55 | −10.15% |
| `ros_reliable` | 262144 | 1556.1 → 1353.4 | −202.66 | −13.02% | 1891.7 → 1523.4 | −368.29 | −19.47% | 1948.5 → 1571.3 | −377.15 | −19.36% |
| `ros_reliable` | 1048576 | 2917.0 → 2368.5 | −548.46 | **−18.80%** | 3327.7 → 2699.1 | −628.63 | −18.89% | 3594.0 → 2843.0 | −751.01 | −20.90% |

## Chain A `same-host` vs iter2-after (mid-size honesty)

How much of the booked mid-size regression is still on the books. Not a second treatment. Negative vs this table is “past iter2-after.”

| case | payload (B) | p50 i2-after → iter5 | Δ p50 | p50 % | iter4 vs i2-after p50 % |
|------|-------------|----------------------|-------|-------|-------------------------|
| `ros_high_throughput` | 102400 | 1146.2 → 1153.9 | +7.70 | +0.67% | +5.96% |
| `ros_high_throughput` | 262144 | 1463.4 → 1345.9 | −117.50 | **−8.03%** | +12.93% |
| `ros_high_throughput` | 1048576 | 3906.1 → 2312.2 | −1593.9 | **−40.81%** | −23.15% |
| `ros_reliable` | 102400 | 1129.8 → 1143.4 | +13.60 | +1.20% | +11.86% |
| `ros_reliable` | 262144 | 1362.6 → 1353.4 | −9.21 | −0.68% | +14.20% |
| `ros_reliable` | 1048576 | 3304.9 → 2368.5 | −936.38 | **−28.33%** | −11.74% |

## Chain A `same-process` (honesty check only)

Matching cases only. **Do not** tune for this table. Mid-size and 1 MiB both moved faster vs iter4; that is consistent with fewer fragments on an intra-process path, but this is not a same-host claim.

| case | payload (B) | p50 base → after | Δ p50 | p50 % | p95 base → after | Δ p95 | p95 % | p99 base → after | Δ p99 | p99 % |
|------|-------------|------------------|-------|-------|------------------|-------|-------|------------------|-------|-------|
| `ros_high_throughput` | 102400 | 824.83 → 694.56 | −130.27 | −15.79% | 899.03 → 822.58 | −76.44 | −8.50% | 948.15 → 930.57 | −17.57 | −1.85% |
| `ros_high_throughput` | 262144 | 935.55 → 752.95 | −182.60 | −19.52% | 1047.7 → 850.96 | −196.72 | −18.78% | 1070.0 → 906.87 | −163.17 | −15.25% |
| `ros_high_throughput` | 1048576 | 1615.4 → 1371.7 | −243.74 | −15.09% | 1794.5 → 1493.8 | −300.69 | −16.76% | 1854.9 → 1520.2 | −334.71 | −18.04% |
| `ros_reliable` | 102400 | 818.44 → 671.83 | −146.61 | −17.91% | 908.50 → 740.08 | −168.43 | −18.54% | 951.99 → 769.05 | −182.93 | −19.22% |
| `ros_reliable` | 262144 | 906.80 → 760.10 | −146.70 | −16.18% | 1030.3 → 835.80 | −194.48 | −18.88% | 1087.2 → 877.49 | −209.72 | −19.29% |
| `ros_reliable` | 1048576 | 1596.3 → 1332.3 | −264.00 | −16.54% | 1738.7 → 1480.4 | −258.34 | −14.86% | 1870.6 → 1543.7 | −326.86 | −17.47% |

## Reading the tails

- Same-host BestEffort 256 KiB p50 **−18.6%** vs iter4 is the material mid-size result (past iter2-after by **−8.0%**).
- Same-host BestEffort 100 KiB is back to noise of iter2-after (+0.7%).
- Same-host Reliable 100/256 KiB iter4 recovery is kept and extended (now within ~1% of iter2-after).
- Same-host 1 MiB BestEffort/Reliable p50 **−19–23%** vs iter4 (80/80 both). Prefer-not-regressing 1 MiB is satisfied; the 2 MiB additive segment can carry 1 MiB fragments. Not a second knob.
- Same-process moving with mid-size is an honesty check, not a reason to chase intra-process noise.
- XMLPARSER: remasure ping-pong stderr is empty (no `shm_midsize` / `maxMessageSize` / `segment_size` parse errors).
- Exclusive 768 KiB SHM and UDP-only were **not** kept (both erased 1 MiB BestEffort). iter3 unfragmented SHM (`maxMessageSize` 2 MiB / `segment_size` 4 MiB) stays discarded.
