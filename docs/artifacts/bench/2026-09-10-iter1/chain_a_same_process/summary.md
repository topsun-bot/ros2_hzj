# Chain A same-process

- **STATUS:** `ok`
- **Chain:** `A`
- **Topology:** `same-process`
- **Metric:** round-trip time (ping-pong in scripts/bench/pingpong.py) （单位：microseconds）
- **Domain / RMW:** domain_id=`42` RMW=`rmw_fastrtps_cpp` ROS_DOMAIN_ID=`42`
- **CYCLONEDDS_URI / iceoryx:** `(unset)` / `default`

数字是 **ping-pong RTT**（本仓 `scripts/bench/pingpong.py` 里计时），不是中间件根因，也不是和另一条链可比的对照表。
在 Humble 容器内、`source config/env/chain_a.sh` 之后测：`same-process`，RMW=`rmw_fastrtps_cpp`，`ROS_DOMAIN_ID=42`。
iter1：`config/fastdds.xml` 已改为 Humble-valid `<topic><historyQos>`；本 run 的 ping-pong stdout **没有** `XMLPARSER` `Name: history` / `Error parsing fastdds.xml`。
不要和链 B 或 `same-host` 放进同一张表。不要写成飞书大包根因。

对照：[`../delta.md`](../delta.md) vs `2026-09-10` 同拓扑。

## p50 / p95 / p99（微秒，RTT）

| case | msg size | samples | timeouts | p50 (µs) | p95 (µs) | p99 (µs) | min | max |
|------|----------|---------|----------|----------|----------|----------|-----|-----|
| `ros_high_throughput` | 64 B | 400 | 0 | 223.21 | 306.55 | 647.07 | 213.88 | 854.71 |
| `ros_high_throughput` | 1024 B | 400 | 0 | 366.68 | 433.08 | 458.79 | 355.60 | 6444.0 |
| `ros_high_throughput` | 16384 B | 400 | 0 | 2925.4 | 3138.9 | 3286.7 | 2564.6 | 10031.6 |
| `ros_high_throughput` | 65536 B | 400 | 0 | 10015.3 | 11189.4 | 13022.4 | 9662.9 | 23676.7 |
| `ros_reliable` | 64 B | 400 | 0 | 223.68 | 315.43 | 359.61 | 213.63 | 506.25 |
| `ros_reliable` | 1024 B | 400 | 0 | 361.38 | 441.85 | 792.70 | 352.15 | 6326.1 |
| `ros_reliable` | 16384 B | 400 | 0 | 2926.9 | 3106.6 | 3204.9 | 2585.9 | 3556.6 |
| `ros_reliable` | 65536 B | 400 | 0 | 10047.1 | 14334.5 | 14796.3 | 9663.3 | 15588.5 |

QoS 名称对齐 `testdata.py` 预设：`high_throughput` = BestEffort/KeepLast(1)/Volatile；
`reliable` = Reliable(max_blocking_time=0)/KeepLast(5000)/Volatile。
这不是冻结表导航 QoS，也没有改 `ddspubsub` / `rospubsub` 默认值。

## Upstream pytest

官方 `pytest -m tool -k 'ros or RawROS or DimosROS'` collection **失败**（`dimos_bridge` `Image` stub ImportError），exit `2` — `pytest_ros_stdout.txt`。
分位数只来自 ping-pong（400 samples / case，0 timeouts）。不要和链 B 放进同一张表。

