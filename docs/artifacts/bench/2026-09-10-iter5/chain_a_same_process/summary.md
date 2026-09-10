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
| `ros_high_throughput` | 102400 B | 100.0 | 80 | 0 | 694.56 | 822.58 | 930.57 | 522.67 | 1042.2 |
| `ros_high_throughput` | 262144 B | 100.0 | 80 | 0 | 752.95 | 850.96 | 906.87 | 702.17 | 933.53 |
| `ros_high_throughput` | 1048576 B | 100.0 | 80 | 0 | 1371.7 | 1493.8 | 1520.2 | 1236.6 | 1525.0 |
| `ros_reliable` | 102400 B | 100.0 | 80 | 0 | 671.83 | 740.08 | 769.05 | 539.82 | 786.64 |
| `ros_reliable` | 262144 B | 100.0 | 80 | 0 | 760.10 | 835.80 | 877.49 | 621.98 | 930.51 |
| `ros_reliable` | 1048576 B | 100.0 | 80 | 0 | 1332.3 | 1480.4 | 1543.7 | 1228.8 | 1584.2 |

QoS 名称对齐 `testdata.py` 预设：`high_throughput` = BestEffort/KeepLast(1)/Volatile；
`reliable` = Reliable(max_blocking_time=0)/KeepLast(5000)/Volatile。
这不是冻结表导航 QoS，也没有改 `ddspubsub` / `rospubsub` 默认值。

## Upstream pytest

`BENCH_SKIP_PYTEST=1`。same-process 只作诚实对照，**不要**为它调参。mid-size 与 1 MiB p50 相对 iter4 都变快。对照 [`../delta.md`](../delta.md)。不要和链 B 混表。不是飞书 / 实机根因。

