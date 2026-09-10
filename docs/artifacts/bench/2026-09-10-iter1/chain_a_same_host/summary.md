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
iter1：Humble XMLPARSER 已接受合同种子（无 `<qos><history>` 报错）。对照：[`../delta.md`](../delta.md)。

## p50 / p95 / p99（微秒，RTT）

| case | msg size | samples | timeouts | p50 (µs) | p95 (µs) | p99 (µs) | min | max |
|------|----------|---------|----------|----------|----------|----------|-----|-----|
| `ros_high_throughput` | 64 B | 400 | 0 | 179.82 | 231.92 | 394.33 | 173.62 | 1102.8 |
| `ros_high_throughput` | 1024 B | 400 | 0 | 391.19 | 639.47 | 787.97 | 359.78 | 1323.8 |
| `ros_high_throughput` | 16384 B | 400 | 0 | 3054.7 | 3258.9 | 3351.5 | 2573.9 | 10062.9 |
| `ros_high_throughput` | 65536 B | 400 | 0 | 10543.5 | 11352.0 | 12220.8 | 9699.8 | 12815.2 |
| `ros_reliable` | 64 B | 400 | 0 | 235.67 | 268.59 | 469.78 | 222.31 | 632.77 |
| `ros_reliable` | 1024 B | 400 | 0 | 398.21 | 658.04 | 889.45 | 324.75 | 922.45 |
| `ros_reliable` | 16384 B | 400 | 0 | 3076.1 | 3469.8 | 3654.2 | 2568.5 | 4696.2 |
| `ros_reliable` | 65536 B | 400 | 0 | 10365.9 | 10925.8 | 11728.7 | 9802.5 | 12986.0 |

QoS 名称对齐 `testdata.py` 预设：`high_throughput` = BestEffort/KeepLast(1)/Volatile；
`reliable` = Reliable(max_blocking_time=0)/KeepLast(5000)/Volatile。
这不是冻结表导航 QoS，也没有改 `ddspubsub` / `rospubsub` 默认值。

## Upstream pytest

官方 `pytest -m tool -k 'ros or RawROS or DimosROS'` collection **失败**（`dimos_bridge` `Image` stub ImportError），exit `2` — `pytest_ros_stdout.txt`。
分位数只来自两进程 ping-pong（400 samples / case，0 timeouts）。

