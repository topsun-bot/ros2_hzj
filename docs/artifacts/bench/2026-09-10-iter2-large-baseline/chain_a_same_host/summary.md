# Chain A same-host

- **STATUS:** `ok`
- **Chain:** `A`
- **Topology:** `same-host`
- **Metric:** round-trip time (ping-pong in scripts/bench/pingpong.py) （单位：microseconds）
- **Domain / RMW:** domain_id=`42` RMW=`rmw_fastrtps_cpp` ROS_DOMAIN_ID=`42`
- **CYCLONEDDS_URI / iceoryx:** `(unset)` / `default`
- **Payload sizes (bytes):** `[102400, 262144, 1048576]`
- **Inter-message gap:** `100.0` ms (target `10.0` Hz)
- **Chain A ros_msg:** `uint8_multiarray`

数字是 **ping-pong RTT**（本仓 `scripts/bench/pingpong.py` 里计时），不是中间件根因，也不是和另一条链可比的对照表。 **不是** 飞书现场 / 实机 / 跨机根因证明。

## p50 / p95 / p99（微秒，RTT）

| case | payload (B) | gap (ms) | samples | timeouts | p50 (µs) | p95 (µs) | p99 (µs) | min | max |
|------|-------------|----------|---------|----------|----------|----------|----------|-----|-----|
| `ros_high_throughput` | 102400 B | 100.0 | 80 | 0 | 1098.8 | 1183.1 | 1211.7 | 877.86 | 1251.7 |
| `ros_high_throughput` | 262144 B | 100.0 | 80 | 0 | 1368.3 | 1542.5 | 1635.5 | 1176.4 | 1639.7 |
| `ros_high_throughput` | 1048576 B | 100.0 | 0 | 90 | — | — | — | — | — |
| `ros_reliable` | 102400 B | 100.0 | 80 | 0 | 1095.6 | 1236.0 | 1322.7 | 848.51 | 1377.9 |
| `ros_reliable` | 262144 B | 100.0 | 80 | 0 | 1329.9 | 1595.8 | 1692.4 | 1032.4 | 1695.0 |
| `ros_reliable` | 1048576 B | 100.0 | 80 | 0 | 46755.6 | 47250.4 | 47512.0 | 24529.9 | 47551.5 |

QoS 名称对齐 `testdata.py` 预设：`high_throughput` = BestEffort/KeepLast(1)/Volatile；
`reliable` = Reliable(max_blocking_time=0)/KeepLast(5000)/Volatile。
这不是冻结表导航 QoS，也没有改 `ddspubsub` / `rospubsub` 默认值。

## Upstream pytest

`BENCH_SKIP_PYTEST=1`。1 MiB `ros_high_throughput`（BestEffort）same-host：**90 timeouts / 0 samples**（不是 OOM）。1 MiB `ros_reliable` 有 80 个样本。不要和链 B 放进同一张表。不是飞书 / 实机根因。

