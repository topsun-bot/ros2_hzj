# Chain A same-process

- **STATUS:** `ok`
- **Chain:** `A`
- **Topology:** `same-process`
- **Metric:** round-trip time (ping-pong in scripts/bench/pingpong.py) （单位：microseconds）
- **Domain / RMW:** domain_id=`42` RMW=`rmw_fastrtps_cpp` ROS_DOMAIN_ID=`42`
- **CYCLONEDDS_URI / iceoryx:** `(unset)` / `default`

数字是 **ping-pong RTT**（本仓 `scripts/bench/pingpong.py` 里计时），不是中间件根因，也不是和另一条链可比的对照表。
在 Humble 容器内、`source config/env/chain_a.sh` 之后测：`same-process`，RMW=`rmw_fastrtps_cpp`，`ROS_DOMAIN_ID=42`。

## p50 / p95 / p99（微秒，RTT）

| case | msg size | samples | timeouts | p50 (µs) | p95 (µs) | p99 (µs) | min | max |
|------|----------|---------|----------|----------|----------|----------|-----|-----|
| `ros_high_throughput` | 64 B | 400 | 0 | 217.29 | 281.37 | 308.98 | 210.09 | 337.74 |
| `ros_high_throughput` | 1024 B | 400 | 0 | 360.95 | 461.64 | 498.51 | 351.12 | 629.47 |
| `ros_high_throughput` | 16384 B | 400 | 0 | 2937.8 | 3196.5 | 3663.4 | 2569.3 | 7733.0 |
| `ros_high_throughput` | 65536 B | 400 | 0 | 10154.8 | 10628.5 | 12220.0 | 9773.3 | 13632.6 |
| `ros_reliable` | 64 B | 400 | 0 | 222.75 | 336.92 | 444.97 | 210.19 | 788.66 |
| `ros_reliable` | 1024 B | 400 | 0 | 364.97 | 487.41 | 527.68 | 351.85 | 4769.9 |
| `ros_reliable` | 16384 B | 400 | 0 | 2923.9 | 3131.0 | 3918.6 | 2616.0 | 8557.5 |
| `ros_reliable` | 65536 B | 400 | 0 | 10035.2 | 13638.2 | 14438.5 | 9713.1 | 16028.4 |

QoS 名称对齐 `testdata.py` 预设：`high_throughput` = BestEffort/KeepLast(1)/Volatile；
`reliable` = Reliable(max_blocking_time=0)/KeepLast(5000)/Volatile。
这不是冻结表导航 QoS，也没有改 `ddspubsub` / `rospubsub` 默认值。

## Upstream pytest

官方 `pytest -m tool -k 'ros or RawROS or DimosROS'` collection **失败**（`dimos_bridge` `Image` stub ImportError），exit `2` — `pytest_ros_stdout.txt`。
分位数只来自 ping-pong（400 samples / case，0 timeouts）。不要和链 B 放进同一张表。

