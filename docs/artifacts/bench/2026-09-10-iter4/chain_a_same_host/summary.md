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
| `ros_high_throughput` | 102400 B | 100.0 | 80 | 0 | 1214.4 | 1387.0 | 1683.0 | 960.77 | 1776.6 |
| `ros_high_throughput` | 262144 B | 100.0 | 80 | 0 | 1652.6 | 1839.8 | 1867.2 | 1387.8 | 1915.1 |
| `ros_high_throughput` | 1048576 B | 100.0 | 80 | 0 | 3001.9 | 3411.1 | 3451.1 | 2513.9 | 3510.5 |
| `ros_reliable` | 102400 B | 100.0 | 80 | 0 | 1263.8 | 1466.3 | 1483.4 | 876.05 | 1533.4 |
| `ros_reliable` | 262144 B | 100.0 | 80 | 0 | 1556.1 | 1891.7 | 1948.5 | 1076.6 | 1963.3 |
| `ros_reliable` | 1048576 B | 100.0 | 80 | 0 | 2917.0 | 3327.7 | 3594.0 | 2402.1 | 3696.3 |

QoS 名称对齐 `testdata.py` 预设：`high_throughput` = BestEffort/KeepLast(1)/Volatile；
`reliable` = Reliable(max_blocking_time=0)/KeepLast(5000)/Volatile。
这不是冻结表导航 QoS，也没有改 `ddspubsub` / `rospubsub` 默认值。

## Upstream pytest

`BENCH_SKIP_PYTEST=1`。iter4：`dynamic=false`、池仍 32。same-host Reliable 100/256 KiB p50 约 **−8–9%** vs iter3；1 MiB BestEffort p50 约 3.00 ms（iter3 约 2.94 ms，噪声内）；1 MiB Reliable 约 **−8%**。BestEffort 256 KiB **未**回到 iter2-after。对照 [`../delta.md`](../delta.md)。不要和链 B 混表。不是飞书 / 实机根因。

