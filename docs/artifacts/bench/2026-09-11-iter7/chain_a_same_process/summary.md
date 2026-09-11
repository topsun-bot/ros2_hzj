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
| `ros_high_throughput` | 64 B | 5.0 | 400 | 0 | 588.70 | 655.16 | 724.27 | 446.85 | 769.95 |
| `ros_reliable` | 64 B | 5.0 | 400 | 0 | 596.94 | 651.02 | 689.46 | 449.77 | 733.40 |

## Jitter（主指标：RTT 尾 + inter-message interval）

Do **not** read p50/mean as success. `pub_interval` = consecutive post-warmup publish times (includes timed-out publishes). `arrival_interval` = consecutive successful pong times. `jitter_abs` = |interval − target gap|. `rfc3550` = running mean of |Δinterval|.

| case | payload (B) | RTT p95−p50 | RTT p99−p50 | RTT stdev | pub I p50 | pub I stdev | pub |I−tgt| p95 | pub |I−tgt| p99 | pub rfc3550 | arr I stdev | arr |I−tgt| p95 | arr |I−tgt| p99 |
|------|-------------|-------------|-------------|-----------|-----------|-------------|---------------|---------------|-------------|-------------|---------------|---------------|
| `ros_high_throughput` | 64 B | 66.47 | 135.57 | 40.51 | 5098.1 | 34.69 | 187.27 | 238.97 | 42.74 | 73.28 | 242.50 | 285.62 |
| `ros_reliable` | 64 B | 54.08 | 92.53 | 36.32 | 5100.1 | 36.40 | 192.13 | 224.50 | 51.19 | 66.73 | 239.87 | 286.21 |

QoS 名称对齐 `testdata.py` 预设：`high_throughput` = BestEffort/KeepLast(1)/Volatile；
`reliable` = Reliable(max_blocking_time=0)/KeepLast(5000)/Volatile。
这不是冻结表导航 QoS，也没有改 `ddspubsub` / `rospubsub` 默认值。

## Upstream pytest

`BENCH_SKIP_PYTEST=1`。**64 B / 200 Hz / 5 ms**. Honesty only; **do not tune**. Probe `healthy_check_timeout_ms` 10000. 0/400 timeouts. 不要和链 B 混表。不是飞书 / 实机根因。

