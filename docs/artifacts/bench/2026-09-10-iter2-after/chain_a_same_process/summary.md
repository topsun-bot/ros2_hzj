# Chain A same-process

- **STATUS:** `ok`
- **Chain:** `A`
- **Topology:** `same-process`
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
| `ros_high_throughput` | 102400 B | 100.0 | 80 | 0 | 687.95 | 763.89 | 778.78 | 542.50 | 781.24 |
| `ros_high_throughput` | 262144 B | 100.0 | 80 | 0 | 772.02 | 847.05 | 861.75 | 623.83 | 890.19 |
| `ros_high_throughput` | 1048576 B | 100.0 | 80 | 0 | 3478.7 | 3708.5 | 3799.6 | 3287.3 | 3838.7 |
| `ros_reliable` | 102400 B | 100.0 | 80 | 0 | 686.60 | 761.53 | 847.56 | 547.38 | 866.07 |
| `ros_reliable` | 262144 B | 100.0 | 80 | 0 | 769.47 | 852.89 | 886.09 | 642.07 | 905.37 |
| `ros_reliable` | 1048576 B | 100.0 | 80 | 0 | 2044.8 | 3683.2 | 3791.6 | 1800.2 | 3825.2 |

QoS 名称对齐 `testdata.py` 预设：`high_throughput` = BestEffort/KeepLast(1)/Volatile；
`reliable` = Reliable(max_blocking_time=0)/KeepLast(5000)/Volatile。
这不是冻结表导航 QoS，也没有改 `ddspubsub` / `rospubsub` 默认值。

## Upstream pytest

`BENCH_SKIP_PYTEST=1`。iter2-after socket-buffer 旋钮后 same-process p50 约 +4–8%（噪声）。对照 [`../delta.md`](../delta.md)。不要和链 B 混表。不是飞书 / 实机根因。

