# iter2-after delta vs iter2-large-baseline (Chain A only)

Like-to-like: **Chain A** `same-process` and `same-host` only. Same `run_large_packet.sh` command, sizes `102400,262144,1048576`, gap 100 ms, 80 samples, `uint8_multiarray`.

**Do not** put these numbers in a table with Chain B. **Do not** treat same-host localhost as a Feishu / real-robot / cross-host root cause.

Change under test: default-participant UDP socket buffers 2 MiB in `config/fastdds.xml`. See [`change.md`](change.md).

Δ = after − baseline. Negative = faster. Units: microseconds RTT.

## Headline (same-host 1 MiB)

| case | baseline | after |
|------|----------|--------|
| `ros_high_throughput` 1048576 B | **0/90 samples** (all timeouts) | **80/80**, p50 3906.1 µs |
| `ros_reliable` 1048576 B | 80/80, p50 46755.6 µs | 80/80, p50 3304.9 µs (**−92.9%**) |

The 1 MiB BestEffort row has no p50 Δ because the baseline had no samples (honest — not invented). The change is **kept**. This still does not prove field root cause.

Cross-host UDP remains `STATUS: blocked` (single VM) — no percentile delta. Chain B was **not** remasured (knob is Chain A XML only).

## Chain A `same-process`

Matching cases only. Same-process already completed 1 MiB in the baseline (intra-process path); p50 moved about +4–8% (run noise / extra buffer setup). Not a large-payload same-host claim.

| case | payload (B) | p50 base → after | Δ p50 | p50 % | p95 base → after | Δ p95 | p95 % | p99 base → after | Δ p99 | p99 % |
|------|-------------|------------------|-------|-------|------------------|-------|-------|------------------|-------|-------|
| `ros_high_throughput` | 102400 | 660.08 → 687.95 | +27.87 | +4.22% | 710.47 → 763.89 | +53.42 | +7.52% | 736.12 → 778.78 | +42.67 | +5.80% |
| `ros_high_throughput` | 262144 | 745.74 → 772.02 | +26.29 | +3.53% | 855.58 → 847.05 | −8.530 | −1.00% | 922.26 → 861.75 | −60.51 | −6.56% |
| `ros_high_throughput` | 1048576 | 3211.9 → 3478.7 | +266.82 | +8.31% | 3420.4 → 3708.5 | +288.10 | +8.42% | 3524.7 → 3799.6 | +274.82 | +7.80% |
| `ros_reliable` | 102400 | 646.32 → 686.60 | +40.27 | +6.23% | 705.56 → 761.53 | +55.97 | +7.93% | 743.98 → 847.56 | +103.59 | +13.92% |
| `ros_reliable` | 262144 | 739.41 → 769.47 | +30.05 | +4.06% | 812.54 → 852.89 | +40.35 | +4.97% | 912.52 → 886.09 | −26.43 | −2.90% |
| `ros_reliable` | 1048576 | 1934.5 → 2044.8 | +110.30 | +5.70% | 3427.0 → 3683.2 | +256.28 | +7.48% | 3578.5 → 3791.6 | +213.13 | +5.96% |

## Chain A `same-host`

Matching cases only. 100 KiB / 256 KiB p50 moved a few percent (noise). 1 MiB is the treatment target.

| case | payload (B) | p50 base → after | Δ p50 | p50 % | p95 base → after | Δ p95 | p95 % | p99 base → after | Δ p99 | p99 % |
|------|-------------|------------------|-------|-------|------------------|-------|-------|------------------|-------|-------|
| `ros_high_throughput` | 102400 | 1098.8 → 1146.2 | +47.38 | +4.31% | 1183.1 → 1257.8 | +74.72 | +6.32% | 1211.7 → 1295.4 | +83.66 | +6.90% |
| `ros_high_throughput` | 262144 | 1368.3 → 1463.4 | +95.05 | +6.95% | 1542.5 → 1626.9 | +84.46 | +5.48% | 1635.5 → 1741.1 | +105.59 | +6.46% |
| `ros_high_throughput` | 1048576 | *(no baseline p50 — 0/90)* → 3906.1 | n/a | n/a | n/a → 4312.0 | n/a | n/a | n/a → 4347.2 | n/a | n/a |
| `ros_reliable` | 102400 | 1095.6 → 1129.8 | +34.25 | +3.13% | 1236.0 → 1248.0 | +11.98 | +0.97% | 1322.7 → 1426.9 | +104.17 | +7.88% |
| `ros_reliable` | 262144 | 1329.9 → 1362.6 | +32.67 | +2.46% | 1595.8 → 1514.5 | −81.26 | −5.09% | 1692.4 → 1591.5 | −100.88 | −5.96% |
| `ros_reliable` | 1048576 | 46755.6 → 3304.9 | −43450.7 | **−92.93%** | 47250.4 → 3705.3 | −43545.0 | −92.16% | 47512.0 → 3764.9 | −43747.1 | −92.08% |

## Reading the tails

- Same-process +4–8% p50 is not a reason to revert; the hypothesized failure mode was same-host 1 MiB.
- Same-host 1 MiB BestEffort going from total loss to 80 samples is the material change.
- Same-host 1 MiB Reliable p50 47.8 ms → 3.3 ms is kept as an honest delta, not a field root-cause claim.
- XMLPARSER: after ping-pong stdout has **no** parse errors for `sendSocketBufferSize` / `listenSocketBufferSize`.
