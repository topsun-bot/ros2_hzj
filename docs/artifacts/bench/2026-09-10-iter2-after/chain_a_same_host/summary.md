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
| `ros_high_throughput` | 102400 B | 100.0 | 80 | 0 | 1146.2 | 1257.8 | 1295.4 | 814.47 | 1353.6 |
| `ros_high_throughput` | 262144 B | 100.0 | 80 | 0 | 1463.4 | 1626.9 | 1741.1 | 1123.2 | 1818.9 |
| `ros_high_throughput` | 1048576 B | 100.0 | 80 | 0 | 3906.1 | 4312.0 | 4347.2 | 3100.1 | 4359.8 |
| `ros_reliable` | 102400 B | 100.0 | 80 | 0 | 1129.8 | 1248.0 | 1426.9 | 867.84 | 1460.3 |
| `ros_reliable` | 262144 B | 100.0 | 80 | 0 | 1362.6 | 1514.5 | 1591.5 | 1019.2 | 1614.1 |
| `ros_reliable` | 1048576 B | 100.0 | 80 | 0 | 3304.9 | 3705.3 | 3764.9 | 2561.6 | 3814.2 |

QoS 名称对齐 `testdata.py` 预设：`high_throughput` = BestEffort/KeepLast(1)/Volatile；
`reliable` = Reliable(max_blocking_time=0)/KeepLast(5000)/Volatile。
这不是冻结表导航 QoS，也没有改 `ddspubsub` / `rospubsub` 默认值。

## Upstream pytest

`BENCH_SKIP_PYTEST=1`。iter2-after：1 MiB BestEffort **80/80**（基线 0/90）；1 MiB Reliable p50 约 3.3 ms（基线约 47.8 ms）。对照 [`../delta.md`](../delta.md)。不要和链 B 混表。不是飞书 / 实机根因。

