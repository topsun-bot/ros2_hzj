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
| `ros_high_throughput` | 102400 B | 100.0 | 80 | 0 | 660.08 | 710.47 | 736.12 | 511.89 | 738.03 |
| `ros_high_throughput` | 262144 B | 100.0 | 80 | 0 | 745.74 | 855.58 | 922.26 | 596.09 | 950.87 |
| `ros_high_throughput` | 1048576 B | 100.0 | 80 | 0 | 3211.9 | 3420.4 | 3524.7 | 3058.0 | 3547.0 |
| `ros_reliable` | 102400 B | 100.0 | 80 | 0 | 646.32 | 705.56 | 743.98 | 514.71 | 817.19 |
| `ros_reliable` | 262144 B | 100.0 | 80 | 0 | 739.41 | 812.54 | 912.52 | 605.96 | 1080.6 |
| `ros_reliable` | 1048576 B | 100.0 | 80 | 0 | 1934.5 | 3427.0 | 3578.5 | 1734.4 | 3583.8 |

QoS 名称对齐 `testdata.py` 预设：`high_throughput` = BestEffort/KeepLast(1)/Volatile；
`reliable` = Reliable(max_blocking_time=0)/KeepLast(5000)/Volatile。
这不是冻结表导航 QoS，也没有改 `ddspubsub` / `rospubsub` 默认值。

## Upstream pytest

pytest -m tool -k 'ros or RawROS or DimosROS' exit 0; see pytest_ros_stdout.txt

