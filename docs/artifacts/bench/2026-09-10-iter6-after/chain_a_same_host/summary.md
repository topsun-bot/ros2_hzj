# Chain A same-host

- **STATUS:** `ok`
- **Chain:** `A`
- **Topology:** `same-host`
- **Metric:** round-trip time (ping-pong in scripts/bench/pingpong.py) （单位：microseconds）
- **Domain / RMW:** domain_id=`42` RMW=`rmw_fastrtps_cpp` ROS_DOMAIN_ID=`42`
- **CYCLONEDDS_URI / iceoryx:** `(unset)` / `default`
- **Payload sizes (bytes):** `[64]`
- **Inter-message gap:** `5.0` ms (target `200.0` Hz)
- **Chain A ros_msg:** `uint8_multiarray`

数字是 **ping-pong RTT**（本仓 `scripts/bench/pingpong.py` 里计时），不是中间件根因，也不是和另一条链可比的对照表。 **不是** 飞书现场 / 实机 / 跨机根因证明。

## p50 / p95 / p99（微秒，RTT）

| case | payload (B) | gap (ms) | samples | timeouts | p50 (µs) | p95 (µs) | p99 (µs) | min | max |
|------|-------------|----------|---------|----------|----------|----------|----------|-----|-----|
| `ros_high_throughput` | 64 B | 5.0 | 400 | 0 | 998.78 | 1184.5 | 1272.2 | 587.29 | 2729.3 |
| `ros_reliable` | 64 B | 5.0 | 400 | 0 | 947.46 | 1190.0 | 1269.4 | 419.32 | 1518.9 |

QoS 名称对齐 `testdata.py` 预设：`high_throughput` = BestEffort/KeepLast(1)/Volatile；
`reliable` = Reliable(max_blocking_time=0)/KeepLast(5000)/Volatile。
这不是冻结表导航 QoS，也没有改 `ddspubsub` / `rospubsub` 默认值。

## Upstream pytest

`BENCH_SKIP_PYTEST=1`。iter6 探测：`port_queue_capacity` 64。same-host BestEffort 64 B / 200 Hz p50 **+3.52%** vs Step A — **未保留**。Reliable 持平。0/400 timeouts。对照 [`../delta.md`](../delta.md)。不要和链 B 混表。不是飞书 / 实机根因。

