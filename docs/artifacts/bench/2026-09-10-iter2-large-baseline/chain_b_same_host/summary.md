# Chain B same-host

- **STATUS:** `ok`
- **Chain:** `B`
- **Topology:** `same-host`
- **Metric:** round-trip time (ping-pong in scripts/bench/pingpong.py) （单位：microseconds）
- **Domain / RMW:** domain_id=`0` RMW=`(n/a)` ROS_DOMAIN_ID=`(n/a)`
- **CYCLONEDDS_URI / iceoryx:** `(unset)` / `default`
- **Payload sizes (bytes):** `[102400, 262144, 1048576]`
- **Inter-message gap:** `100.0` ms (target `10.0` Hz)
- **Chain A ros_msg:** `(n/a)`

数字是 **ping-pong RTT**（本仓 `scripts/bench/pingpong.py` 里计时），不是中间件根因，也不是和另一条链可比的对照表。 **不是** 飞书现场 / 实机 / 跨机根因证明。

## p50 / p95 / p99（微秒，RTT）

| case | payload (B) | gap (ms) | samples | timeouts | p50 (µs) | p95 (µs) | p99 (µs) | min | max |
|------|-------------|----------|---------|----------|----------|----------|----------|-----|-----|
| `dds_high_throughput` | 102400 B | 100.0 | 80 | 0 | 4999.2 | 5572.1 | 6084.9 | 4303.8 | 7222.2 |
| `dds_high_throughput` | 262144 B | 100.0 | 80 | 0 | 13781.8 | 14404.7 | 14915.1 | 12455.7 | 16448.4 |
| `dds_high_throughput` | 1048576 B | 100.0 | 0 | 90 | — | — | — | — | — |
| `dds_reliable` | 102400 B | 100.0 | 80 | 0 | 4637.8 | 5367.6 | 5910.9 | 3849.2 | 6515.6 |
| `dds_reliable` | 262144 B | 100.0 | 80 | 0 | 11959.6 | 13653.4 | 14473.4 | 10440.3 | 15211.4 |
| `dds_reliable` | 1048576 B | 100.0 | 80 | 0 | 270913.6 | 272982.9 | 300308.8 | 163886.7 | 303330.3 |

QoS 名称对齐 `testdata.py` 预设：`high_throughput` = BestEffort/KeepLast(1)/Volatile；
`reliable` = Reliable(max_blocking_time=0)/KeepLast(5000)/Volatile。
这不是冻结表导航 QoS，也没有改 `ddspubsub` / `rospubsub` 默认值。

## Upstream pytest

`BENCH_SKIP_PYTEST=1`。same-host **localhost UDP, not SHM**（无 RouDi）。1 MiB `dds_high_throughput`：**90 timeouts / 0 samples**（不是 OOM）。1 MiB `dds_reliable` 有 80 个样本。不要和链 A 放进同一张表。不是飞书 / 实机根因。

