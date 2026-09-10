# iter1 delta vs 2026-09-10 (Chain A only)

Like-to-like: **Chain A** `same-process` and `same-host` only. Same `scripts/bench/docker_chain_a.sh` / `pingpong.py` command, sizes `64,1024,16384,65536`, 400 samples, cases `ros_high_throughput` and `ros_reliable`.

**Do not** put these numbers in a table with Chain B. **Do not** treat 64 B same-process as a Feishu / large-packet / real-robot root cause.

Change under test: Humble-valid `<topic><historyQos>` in `config/fastdds.xml` so `loadXMLFile` succeeds. See [`change.md`](change.md).

Ping-pong still applies rclpy QoS in code and does not bind the named foxglove / goal_pose / way_point profiles. Large-payload **p50** moved by about 0–3% (run noise). Some **p99** tails moved a lot on small messages; that is not a large-payload claim. The change is **kept** (not reverted).

Cross-host UDP remains `STATUS: blocked` on both dates (single VM) — no percentile delta.

## Chain A `same-process`

Matching cases only (same chain, topology label, runner, sizes, 400 samples). Δ = iter1 − 2026-09-10. Negative = faster. Units: microseconds RTT.

| case | msg size | p50 base → iter1 | Δ p50 | p50 % | p95 base → iter1 | Δ p95 | p95 % | p99 base → iter1 | Δ p99 | p99 % |
|------|----------|------------------|-------|-------|------------------|-------|-------|------------------|-------|-------|
| `ros_high_throughput` | 64 B | 217.29 → 223.21 | +5.927 | +2.73% | 281.37 → 306.55 | +25.19 | +8.95% | 308.98 → 647.07 | +338.08 | +109.42% |
| `ros_high_throughput` | 1024 B | 360.95 → 366.68 | +5.722 | +1.59% | 461.64 → 433.08 | -28.56 | -6.19% | 498.51 → 458.79 | -39.73 | -7.97% |
| `ros_high_throughput` | 16384 B | 2937.8 → 2925.4 | -12.38 | -0.42% | 3196.5 → 3138.9 | -57.69 | -1.80% | 3663.4 → 3286.7 | -376.73 | -10.28% |
| `ros_high_throughput` | 65536 B | 10154.8 → 10015.3 | -139.46 | -1.37% | 10628.5 → 11189.4 | +560.97 | +5.28% | 12220.0 → 13022.4 | +802.38 | +6.57% |
| `ros_reliable` | 64 B | 222.75 → 223.68 | +0.931 | +0.42% | 336.92 → 315.43 | -21.49 | -6.38% | 444.97 → 359.61 | -85.36 | -19.18% |
| `ros_reliable` | 1024 B | 364.97 → 361.38 | -3.582 | -0.98% | 487.41 → 441.85 | -45.56 | -9.35% | 527.68 → 792.70 | +265.02 | +50.22% |
| `ros_reliable` | 16384 B | 2923.9 → 2926.9 | +3.025 | +0.10% | 3131.0 → 3106.6 | -24.39 | -0.78% | 3918.6 → 3204.9 | -713.68 | -18.21% |
| `ros_reliable` | 65536 B | 10035.2 → 10047.1 | +11.90 | +0.12% | 13638.2 → 14334.5 | +696.33 | +5.11% | 14438.5 → 14796.3 | +357.72 | +2.48% |

## Chain A `same-host`

Matching cases only (same chain, topology label, runner, sizes, 400 samples). Δ = iter1 − 2026-09-10. Negative = faster. Units: microseconds RTT.

| case | msg size | p50 base → iter1 | Δ p50 | p50 % | p95 base → iter1 | Δ p95 | p95 % | p99 base → iter1 | Δ p99 | p99 % |
|------|----------|------------------|-------|-------|------------------|-------|-------|------------------|-------|-------|
| `ros_high_throughput` | 64 B | 185.57 → 179.82 | -5.756 | -3.10% | 336.16 → 231.92 | -104.25 | -31.01% | 459.50 → 394.33 | -65.17 | -14.18% |
| `ros_high_throughput` | 1024 B | 364.75 → 391.19 | +26.43 | +7.25% | 673.79 → 639.47 | -34.32 | -5.09% | 861.24 → 787.97 | -73.27 | -8.51% |
| `ros_high_throughput` | 16384 B | 3105.4 → 3054.7 | -50.70 | -1.63% | 3434.9 → 3258.9 | -176.06 | -5.13% | 3806.9 → 3351.5 | -455.45 | -11.96% |
| `ros_high_throughput` | 65536 B | 10400.7 → 10543.5 | +142.78 | +1.37% | 11101.8 → 11352.0 | +250.21 | +2.25% | 13389.3 → 12220.8 | -1168.6 | -8.73% |
| `ros_reliable` | 64 B | 191.36 → 235.67 | +44.31 | +23.16% | 287.93 → 268.59 | -19.34 | -6.72% | 417.81 → 469.78 | +51.96 | +12.44% |
| `ros_reliable` | 1024 B | 372.16 → 398.21 | +26.05 | +7.00% | 548.26 → 658.04 | +109.78 | +20.02% | 700.84 → 889.45 | +188.61 | +26.91% |
| `ros_reliable` | 16384 B | 2972.8 → 3076.1 | +103.37 | +3.48% | 3290.1 → 3469.8 | +179.77 | +5.46% | 3430.1 → 3654.2 | +224.03 | +6.53% |
| `ros_reliable` | 65536 B | 10253.3 → 10365.9 | +112.61 | +1.10% | 10947.9 → 10925.8 | -22.10 | -0.20% | 12135.1 → 11728.7 | -406.37 | -3.35% |

## Reading the tails

- Same-process `ros_high_throughput` 64 B p99 +109% (309 → 647 µs) is a small-message tail, not 16 KiB / 64 KiB behavior.
- 16 KiB / 64 KiB p50 on both topologies stayed within a few percent of the 2026-09-10 baseline.
- This remasurement confirms the XML file loads (no Humble `XMLPARSER` `history` errors in iter1 stdout). It does **not** prove field latency root cause.
