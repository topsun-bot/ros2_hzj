# iter3 delta vs iter2-after (Chain A only)

Like-to-like: **Chain A** `same-process` and `same-host` only. Same `run_large_packet.sh` command, sizes `102400,262144,1048576`, gap 100 ms, 80 samples, `uint8_multiarray`.

**Do not** put these numbers in a table with Chain B. **Do not** treat same-host localhost as a Feishu / real-robot / cross-host root cause.

这些对照数字 **不是** 飞书现场、实机、或跨机根因证明。

Change under test: default-participant RTPS send-buffer pool `preallocated_number=32`, `dynamic=true` in `config/fastdds.xml`. See [`change.md`](change.md).

Δ = after − baseline. Negative = faster. Units: microseconds RTT.

## Headline (same-host 1 MiB — primary)

| case | baseline (iter2-after) | after (iter3) |
|------|------------------------|---------------|
| `ros_high_throughput` 1048576 B | 80/80, p50 3906.1 µs | 80/80, p50 2935.2 µs (**−24.86%**) |
| `ros_reliable` 1048576 B | 80/80, p50 3304.9 µs | 80/80, p50 3178.2 µs (**−3.83%**) |

The change is **kept** for the same-host 1 MiB BestEffort p50/p95 drop. 100 KiB / 256 KiB same-host p50 moved the other way (about +9–24%); that is reported honestly and was **not** the treatment target. Same-host 1 MiB p99 is slightly higher (+3.5% BestEffort, +3.3% Reliable). This still does not prove field root cause.

Cross-host UDP remains `STATUS: blocked` (single VM) — no percentile delta. Chain B was **not** remasured (knob is Chain A XML only).

## Chain A `same-host` (primary)

Matching cases only. 1 MiB is the treatment target.

| case | payload (B) | p50 base → after | Δ p50 | p50 % | p95 base → after | Δ p95 | p95 % | p99 base → after | Δ p99 | p99 % |
|------|-------------|------------------|-------|-------|------------------|-------|-------|------------------|-------|-------|
| `ros_high_throughput` | 102400 | 1146.2 → 1257.9 | +111.71 | +9.75% | 1257.8 → 1529.3 | +271.47 | +21.58% | 1295.4 → 1594.6 | +299.18 | +23.10% |
| `ros_high_throughput` | 262144 | 1463.4 → 1591.9 | +128.53 | +8.78% | 1626.9 → 1888.4 | +261.51 | +16.07% | 1741.1 → 2015.4 | +274.35 | +15.76% |
| `ros_high_throughput` | 1048576 | 3906.1 → 2935.2 | −970.87 | **−24.86%** | 4312.0 → 3417.5 | −894.49 | −20.74% | 4347.2 → 4499.4 | +152.21 | +3.50% |
| `ros_reliable` | 102400 | 1129.8 → 1393.3 | +263.47 | +23.32% | 1248.0 → 1726.9 | +478.90 | +38.37% | 1426.9 → 1774.2 | +347.39 | +24.35% |
| `ros_reliable` | 262144 | 1362.6 → 1693.1 | +330.49 | +24.25% | 1514.5 → 2031.5 | +516.97 | +34.13% | 1591.5 → 2133.5 | +541.97 | +34.05% |
| `ros_reliable` | 1048576 | 3304.9 → 3178.2 | −126.73 | **−3.83%** | 3705.3 → 3671.8 | −33.50 | −0.90% | 3764.9 → 3887.4 | +122.49 | +3.25% |

## Chain A `same-process` (honesty check only)

Matching cases only. **Do not** tune for this table. Same-process 100/256 KiB p50 moved +25–32% (worse). Same-process 1 MiB improved (BestEffort **−46.5%**, Reliable **−20.2%**) — consistent with a send-buffer wait on large fragment bursts, but this is not a same-host claim and is not a reason to chase same-process noise.

| case | payload (B) | p50 base → after | Δ p50 | p50 % | p95 base → after | Δ p95 | p95 % | p99 base → after | Δ p99 | p99 % |
|------|-------------|------------------|-------|-------|------------------|-------|-------|------------------|-------|-------|
| `ros_high_throughput` | 102400 | 687.95 → 860.32 | +172.37 | +25.06% | 763.89 → 1049.0 | +285.09 | +37.32% | 778.78 → 1402.5 | +623.67 | +80.08% |
| `ros_high_throughput` | 262144 | 772.02 → 1019.7 | +247.72 | +32.09% | 847.05 → 1215.5 | +368.49 | +43.50% | 861.75 → 1311.4 | +449.68 | +52.18% |
| `ros_high_throughput` | 1048576 | 3478.7 → 1862.1 | −1616.6 | −46.47% | 3708.5 → 2071.5 | −1637.0 | −44.14% | 3799.6 → 2119.4 | −1680.1 | −44.22% |
| `ros_reliable` | 102400 | 686.60 → 904.18 | +217.59 | +31.69% | 761.53 → 1053.8 | +292.23 | +38.37% | 847.56 → 1156.1 | +308.55 | +36.40% |
| `ros_reliable` | 262144 | 769.47 → 1009.0 | +239.55 | +31.13% | 852.89 → 1201.8 | +348.95 | +40.91% | 886.09 → 1323.7 | +437.64 | +49.39% |
| `ros_reliable` | 1048576 | 2044.8 → 1631.1 | −413.73 | −20.23% | 3683.2 → 1947.4 | −1735.8 | −47.13% | 3791.6 → 2012.2 | −1779.4 | −46.93% |

## Reading the tails

- Same-host 1 MiB BestEffort p50/p95 down ~21–25% is the material same-host result.
- Same-host 100/256 KiB p50 up is not a reason to revert the 1 MiB treatment; it is also not a claim those sizes improved.
- Same-process 1 MiB moving a lot is an honesty check, not a target. Same-process 100/256 KiB getting slower is out of scope (iter2 +4–8% noise was already out of scope).
- XMLPARSER: remasure ping-pong stderr is empty (no `send_buffers` / `preallocated_number` / `dynamic` parse errors).
- A same-host SHM `maxMessageSize` / `segment_size` probe was **not** kept (1 MiB same-host p50 ~+36%). See [`change.md`](change.md).
