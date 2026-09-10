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
| `ros_high_throughput` | 102400 B | 100.0 | 80 | 0 | 1257.9 | 1529.3 | 1594.6 | 924.65 | 1692.7 |
| `ros_high_throughput` | 262144 B | 100.0 | 80 | 0 | 1591.9 | 1888.4 | 2015.4 | 1214.4 | 2058.7 |
| `ros_high_throughput` | 1048576 B | 100.0 | 80 | 0 | 2935.2 | 3417.5 | 4499.4 | 2617.3 | 5575.7 |
| `ros_reliable` | 102400 B | 100.0 | 80 | 0 | 1393.3 | 1726.9 | 1774.2 | 1086.6 | 1857.8 |
| `ros_reliable` | 262144 B | 100.0 | 80 | 0 | 1693.1 | 2031.5 | 2133.5 | 1274.1 | 2194.0 |
| `ros_reliable` | 1048576 B | 100.0 | 80 | 0 | 3178.2 | 3671.8 | 3887.4 | 2473.4 | 4417.5 |

QoS 名称对齐 `testdata.py` 预设：`high_throughput` = BestEffort/KeepLast(1)/Volatile；
`reliable` = Reliable(max_blocking_time=0)/KeepLast(5000)/Volatile。
这不是冻结表导航 QoS，也没有改 `ddspubsub` / `rospubsub` 默认值。

## Upstream pytest

`BENCH_SKIP_PYTEST=1`。iter3 send-buffer 旋钮后 same-host 1 MiB BestEffort p50 约 2.9 ms（iter2-after 约 3.9 ms，**−25%**）；1 MiB Reliable p50 约 3.2 ms（**−3.8%**）。对照 [`../delta.md`](../delta.md)。不要和链 B 混表。不是飞书 / 实机根因。

