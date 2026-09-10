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
| `ros_high_throughput` | 102400 B | 100.0 | 80 | 0 | 1153.9 | 1355.7 | 1448.6 | 921.39 | 1458.3 |
| `ros_high_throughput` | 262144 B | 100.0 | 80 | 0 | 1345.9 | 1541.1 | 1583.1 | 1048.1 | 1600.2 |
| `ros_high_throughput` | 1048576 B | 100.0 | 80 | 0 | 2312.2 | 2841.0 | 3138.2 | 2070.2 | 3173.8 |
| `ros_reliable` | 102400 B | 100.0 | 80 | 0 | 1143.4 | 1290.4 | 1332.8 | 700.15 | 1358.6 |
| `ros_reliable` | 262144 B | 100.0 | 80 | 0 | 1353.4 | 1523.4 | 1571.3 | 870.11 | 1659.9 |
| `ros_reliable` | 1048576 B | 100.0 | 80 | 0 | 2368.5 | 2699.1 | 2843.0 | 1986.6 | 2894.9 |

QoS 名称对齐 `testdata.py` 预设：`high_throughput` = BestEffort/KeepLast(1)/Volatile；
`reliable` = Reliable(max_blocking_time=0)/KeepLast(5000)/Volatile。
这不是冻结表导航 QoS，也没有改 `ddspubsub` / `rospubsub` 默认值。

## Upstream pytest

`BENCH_SKIP_PYTEST=1`。iter5：additive SHM `maxMessageSize=280000` / `segment_size=2 MiB`，builtin 保留。same-host BestEffort 256 KiB p50 约 **−18.6%** vs iter4（并低于 iter2-after）；1 MiB BestEffort/Reliable 约 **−19–23%**，80/80。对照 [`../delta.md`](../delta.md)。不要和链 B 混表。不是飞书 / 实机根因。

