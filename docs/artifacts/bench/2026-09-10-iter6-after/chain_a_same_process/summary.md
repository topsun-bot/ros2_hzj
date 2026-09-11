# Chain A same-process

- **STATUS:** `ok`
- **Chain:** `A`
- **Topology:** `same-process`
- **Metric:** round-trip time (ping-pong in scripts/bench/pingpong.py) （单位：microseconds）
- **Domain / RMW:** domain_id=`42` RMW=`rmw_fastrtps_cpp` ROS_DOMAIN_ID=`42`
- **CYCLONEDDS_URI / iceoryx:** `(unset)` / `default`
- **Payload sizes (bytes):** `[64]`
- **Inter-message gap:** `5.0` ms (target `200.0` Hz)
- **Scale:** `IMU-ish`
- **Primary metric:** jitter (RTT p95/p99 + inter-message interval variance). Do **not** claim success from p50/mean alone.
- **Chain A ros_msg:** `uint8_multiarray`

数字是 **ping-pong RTT 与 inter-message interval**（本仓 `scripts/bench/pingpong.py` 里计时），不是中间件根因，也不是和另一条链可比的对照表。 **不是** 飞书现场 / 实机 / 跨机根因证明。

## p50 / p95 / p99（微秒，RTT）

| case | payload (B) | gap (ms) | samples | timeouts | p50 (µs) | p95 (µs) | p99 (µs) | min | max |
|------|-------------|----------|---------|----------|----------|----------|----------|-----|-----|
| `ros_high_throughput` | 64 B | 5.0 | 400 | 0 | 622.60 | 723.49 | 779.13 | 354.70 | 942.12 |
| `ros_reliable` | 64 B | 5.0 | 400 | 0 | 611.77 | 711.59 | 817.14 | 340.88 | 944.41 |

## Jitter（主指标：RTT 尾 + inter-message interval）

Do **not** read p50/mean as success. `pub_interval` = consecutive post-warmup publish times (includes timed-out publishes). `arrival_interval` = consecutive successful pong times. `jitter_abs` = |interval − target gap|. `rfc3550` = running mean of |Δinterval|.

| case | payload (B) | RTT p95−p50 | RTT p99−p50 | RTT stdev | pub I p50 | pub I stdev | pub |I−tgt| p95 | pub |I−tgt| p99 | pub rfc3550 | arr I stdev | arr |I−tgt| p95 | arr |I−tgt| p99 |
|------|-------------|-------------|-------------|-----------|-----------|-------------|---------------|---------------|-------------|-------------|---------------|---------------|
| `ros_high_throughput` | 64 B | 100.89 | 156.53 | 69.74 | 5097.6 | 53.30 | 237.92 | 270.58 | 48.63 | 110.90 | 297.74 | 417.32 |
| `ros_reliable` | 64 B | 99.82 | 205.37 | 71.17 | 5096.0 | 56.35 | 228.81 | 314.16 | 68.83 | 110.32 | 308.80 | 425.31 |

QoS 名称对齐 `testdata.py` 预设：`high_throughput` = BestEffort/KeepLast(1)/Volatile；
`reliable` = Reliable(max_blocking_time=0)/KeepLast(5000)/Volatile。
这不是冻结表导航 QoS，也没有改 `ddspubsub` / `rospubsub` 默认值。

## Upstream pytest

`BENCH_SKIP_PYTEST=1`。**64 B / 200 Hz / 5 ms** first. same-process is an **honesty check only — do not tune**. Primary table is [`../chain_a_same_host/summary.md`](../chain_a_same_host/summary.md). 0/400 timeouts. 不要和链 B 混表。不是飞书 / 实机根因。

