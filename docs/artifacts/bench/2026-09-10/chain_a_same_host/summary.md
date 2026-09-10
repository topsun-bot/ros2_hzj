# Chain A same-host

- **STATUS:** `ok`
- **Chain:** `A`
- **Topology:** `same-host`
- **Metric:** round-trip time (ping-pong in scripts/bench/pingpong.py) （单位：microseconds）
- **Domain / RMW:** domain_id=`42` RMW=`rmw_fastrtps_cpp` ROS_DOMAIN_ID=`42`
- **CYCLONEDDS_URI / iceoryx:** `(unset)` / `default`

数字是 **ping-pong RTT**（两进程，本仓 `scripts/bench/pingpong.py`）。
拓扑是 **`same-host`**（client + responder）。Fast-DDS 走 Humble `rmw_fastrtps_cpp` **默认 transport**；`config/fastdds.xml` **没有** 强制 UDP-only 或 SHM-only。
**不要**把本表标成 SHM。不要和 `same-process` 或链 B 放进同一张表，也不要写成根因。

## p50 / p95 / p99（微秒，RTT）

| case | msg size | samples | timeouts | p50 (µs) | p95 (µs) | p99 (µs) | min | max |
|------|----------|---------|----------|----------|----------|----------|-----|-----|
| `ros_high_throughput` | 64 B | 400 | 0 | 185.57 | 336.16 | 459.50 | 172.41 | 614.17 |
| `ros_high_throughput` | 1024 B | 400 | 0 | 364.75 | 673.79 | 861.24 | 327.87 | 4014.1 |
| `ros_high_throughput` | 16384 B | 400 | 0 | 3105.4 | 3434.9 | 3806.9 | 2650.9 | 10089.0 |
| `ros_high_throughput` | 65536 B | 400 | 0 | 10400.7 | 11101.8 | 13389.3 | 9798.5 | 13835.9 |
| `ros_reliable` | 64 B | 400 | 0 | 191.36 | 287.93 | 417.81 | 171.02 | 460.25 |
| `ros_reliable` | 1024 B | 400 | 0 | 372.16 | 548.26 | 700.84 | 322.01 | 983.56 |
| `ros_reliable` | 16384 B | 400 | 0 | 2972.8 | 3290.1 | 3430.1 | 2556.4 | 3561.3 |
| `ros_reliable` | 65536 B | 400 | 0 | 10253.3 | 10947.9 | 12135.1 | 9497.2 | 13124.4 |

QoS 名称对齐 `testdata.py` 预设：`high_throughput` = BestEffort/KeepLast(1)/Volatile；
`reliable` = Reliable(max_blocking_time=0)/KeepLast(5000)/Volatile。
这不是冻结表导航 QoS，也没有改 `ddspubsub` / `rospubsub` 默认值。

## Upstream pytest

官方 `pytest -m tool -k 'ros or RawROS or DimosROS'` collection **失败**（`dimos_bridge` `Image` stub ImportError），exit `2` — `pytest_ros_stdout.txt`。
分位数只来自两进程 ping-pong（400 samples / case，0 timeouts）。

