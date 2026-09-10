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
| `ros_high_throughput` | 102400 B | 100.0 | 80 | 0 | 824.83 | 899.03 | 948.15 | 618.15 | 1001.3 |
| `ros_high_throughput` | 262144 B | 100.0 | 80 | 0 | 935.55 | 1047.7 | 1070.0 | 761.96 | 1081.4 |
| `ros_high_throughput` | 1048576 B | 100.0 | 80 | 0 | 1615.4 | 1794.5 | 1854.9 | 1425.0 | 1939.4 |
| `ros_reliable` | 102400 B | 100.0 | 80 | 0 | 818.44 | 908.50 | 951.99 | 620.71 | 1022.3 |
| `ros_reliable` | 262144 B | 100.0 | 80 | 0 | 906.80 | 1030.3 | 1087.2 | 718.15 | 1263.5 |
| `ros_reliable` | 1048576 B | 100.0 | 80 | 0 | 1596.3 | 1738.7 | 1870.6 | 1340.8 | 1978.2 |

QoS 名称对齐 `testdata.py` 预设：`high_throughput` = BestEffort/KeepLast(1)/Volatile；
`reliable` = Reliable(max_blocking_time=0)/KeepLast(5000)/Volatile。
这不是冻结表导航 QoS，也没有改 `ddspubsub` / `rospubsub` 默认值。

## Upstream pytest

`BENCH_SKIP_PYTEST=1`。same-process 只作诚实对照，**不要**为它调参。mid-size 与 1 MiB p50 相对 iter3 都变快。对照 [`../delta.md`](../delta.md)。不要和链 B 混表。不是飞书 / 实机根因。

