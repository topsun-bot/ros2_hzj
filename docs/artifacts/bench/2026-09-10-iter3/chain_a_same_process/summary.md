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
| `ros_high_throughput` | 102400 B | 100.0 | 80 | 0 | 860.32 | 1049.0 | 1402.5 | 744.27 | 1518.8 |
| `ros_high_throughput` | 262144 B | 100.0 | 80 | 0 | 1019.7 | 1215.5 | 1311.4 | 753.44 | 1330.6 |
| `ros_high_throughput` | 1048576 B | 100.0 | 80 | 0 | 1862.1 | 2071.5 | 2119.4 | 1654.4 | 2119.7 |
| `ros_reliable` | 102400 B | 100.0 | 80 | 0 | 904.18 | 1053.8 | 1156.1 | 734.23 | 1270.0 |
| `ros_reliable` | 262144 B | 100.0 | 80 | 0 | 1009.0 | 1201.8 | 1323.7 | 815.71 | 1489.4 |
| `ros_reliable` | 1048576 B | 100.0 | 80 | 0 | 1631.1 | 1947.4 | 2012.2 | 1313.8 | 2072.7 |

QoS 名称对齐 `testdata.py` 预设：`high_throughput` = BestEffort/KeepLast(1)/Volatile；
`reliable` = Reliable(max_blocking_time=0)/KeepLast(5000)/Volatile。
这不是冻结表导航 QoS，也没有改 `ddspubsub` / `rospubsub` 默认值。

## Upstream pytest

`BENCH_SKIP_PYTEST=1`。same-process 只作诚实对照，**不要**为它调参。1 MiB p50 变快；100/256 KiB p50 变慢。对照 [`../delta.md`](../delta.md)。不要和链 B 混表。不是飞书 / 实机根因。

