# Chain B same-host

- **STATUS:** `ok`
- **Chain:** `B`
- **Topology:** `same-host`
- **Metric:** round-trip time (ping-pong in scripts/bench/pingpong.py) （单位：microseconds）
- **Domain / RMW:** domain_id=`0` RMW=`(n/a)` ROS_DOMAIN_ID=`(n/a)`
- **CYCLONEDDS_URI / iceoryx:** `(unset)` / `default`

数字是 **ping-pong RTT**（两进程，本仓 `scripts/bench/pingpong.py`）。
本机 **没有** `iox-roudi`，因此是 `same-host` localhost UDP，**不是** iceoryx SHM。
不要和 `same-process` 或链 A 放进同一张表，也不要写成根因。

## p50 / p95 / p99（微秒，RTT）

| case | msg size | samples | timeouts | p50 (µs) | p95 (µs) | p99 (µs) | min | max |
|------|----------|---------|----------|----------|----------|----------|-----|-----|
| `dds_high_throughput` | 64 B | 400 | 2 | 107.07 | 169.60 | 228.92 | 84.05 | 551.09 |
| `dds_high_throughput` | 1024 B | 400 | 1 | 122.66 | 140.59 | 159.46 | 116.82 | 228.64 |
| `dds_high_throughput` | 16384 B | 400 | 0 | 705.82 | 1085.5 | 4974.4 | 584.57 | 11488.3 |
| `dds_high_throughput` | 65536 B | 400 | 0 | 4414.1 | 5306.1 | 5566.9 | 3333.7 | 6252.9 |
| `dds_reliable` | 64 B | 400 | 0 | 94.44 | 125.80 | 178.04 | 79.27 | 557.81 |
| `dds_reliable` | 1024 B | 400 | 0 | 131.02 | 157.06 | 214.07 | 115.66 | 266.35 |
| `dds_reliable` | 16384 B | 400 | 0 | 716.70 | 989.80 | 1112.3 | 626.92 | 1234.2 |
| `dds_reliable` | 65536 B | 400 | 0 | 4098.2 | 5015.0 | 5413.7 | 3113.5 | 14124.9 |

QoS 名称对齐 `testdata.py` 预设：`high_throughput` = BestEffort/KeepLast(1)/Volatile；
`reliable` = Reliable(max_blocking_time=0)/KeepLast(5000)/Volatile。
这不是冻结表导航 QoS，也没有改 `ddspubsub` / `rospubsub` 默认值。

## Upstream pytest

- `dimos_bridge` official command exit `2` — log: `pytest_dimos_bridge_attempt.txt`
- temporary `topsun_dimos` checkout official command exit `0` — log: `pytest_topsun_dimos_stdout.txt`, junit: `pytest_topsun_dimos_junit.xml`
- 上游 harness 的 Latency 列是 **发完再等收齐** 的 drain time，不是 p50/p95/p99。

