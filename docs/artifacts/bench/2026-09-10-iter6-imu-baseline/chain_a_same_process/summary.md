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
| `ros_high_throughput` | 64 B | 5.0 | 400 | 0 | 607.46 | 732.52 | 806.08 | 336.50 | 834.15 |
| `ros_reliable` | 64 B | 5.0 | 400 | 0 | 611.60 | 718.71 | 799.50 | 306.17 | 902.03 |

## Jitter（主指标：RTT 尾 + inter-message interval）

Do **not** read p50/mean as success. `pub_interval` = consecutive post-warmup publish times (includes timed-out publishes). `arrival_interval` = consecutive successful pong times. `jitter_abs` = |interval − target gap|. `rfc3550` = running mean of |Δinterval|.

| case | payload (B) | RTT p95−p50 | RTT p99−p50 | RTT stdev | pub I p50 | pub I stdev | pub |I−tgt| p95 | pub |I−tgt| p99 | pub rfc3550 | arr I stdev | arr |I−tgt| p95 | arr |I−tgt| p99 |
|------|-------------|-------------|-------------|-----------|-----------|-------------|---------------|---------------|-------------|-------------|---------------|---------------|
| `ros_high_throughput` | 64 B | 125.06 | 198.62 | 74.26 | 5096.6 | 339.77 | 238.89 | 304.29 | 69.75 | 360.45 | 334.46 | 449.49 |
| `ros_reliable` | 64 B | 107.12 | 187.91 | 74.46 | 5096.0 | 50.35 | 221.76 | 287.17 | 29.83 | 115.98 | 306.93 | 463.89 |

QoS 名称对齐 `testdata.py` 预设：`high_throughput` = BestEffort/KeepLast(1)/Volatile；
`reliable` = Reliable(max_blocking_time=0)/KeepLast(5000)/Volatile。
这不是冻结表导航 QoS，也没有改 `ddspubsub` / `rospubsub` 默认值。

## Upstream pytest

`BENCH_SKIP_PYTEST=1`。**64 B / 200 Hz / 5 ms** first. same-process is an **honesty check only — do not tune**. Primary table is [`../chain_a_same_host/summary.md`](../chain_a_same_host/summary.md). 0/400 timeouts. 不要和链 B 混表。不是飞书 / 实机根因。

