# Chain B same-process

- **STATUS:** `ok`
- **Chain:** `B`
- **Topology:** `same-process`
- **Metric:** round-trip time (ping-pong in scripts/bench/pingpong.py) （单位：microseconds）
- **Domain / RMW:** domain_id=`0` RMW=`(n/a)` ROS_DOMAIN_ID=`(n/a)`
- **CYCLONEDDS_URI / iceoryx:** `(unset)` / `default`

数字是 **ping-pong RTT**（本仓 `scripts/bench/pingpong.py` 里计时），不是中间件根因，也不是和另一条链可比的对照表。

## p50 / p95 / p99（微秒，RTT）

| case | msg size | samples | timeouts | p50 (µs) | p95 (µs) | p99 (µs) | min | max |
|------|----------|---------|----------|----------|----------|----------|-----|-----|
| `dds_high_throughput` | 64 B | 400 | 0 | 30.32 | 33.45 | 45.25 | 26.91 | 56.01 |
| `dds_high_throughput` | 1024 B | 400 | 0 | 94.23 | 103.73 | 117.97 | 62.69 | 134.98 |
| `dds_high_throughput` | 16384 B | 400 | 0 | 671.11 | 971.27 | 1041.7 | 514.84 | 1075.1 |
| `dds_high_throughput` | 65536 B | 400 | 0 | 3673.3 | 5070.5 | 5368.7 | 3297.3 | 5439.4 |
| `dds_reliable` | 64 B | 400 | 0 | 32.09 | 59.77 | 63.53 | 29.53 | 82.08 |
| `dds_reliable` | 1024 B | 400 | 0 | 65.75 | 91.36 | 103.93 | 59.63 | 205.61 |
| `dds_reliable` | 16384 B | 400 | 0 | 531.67 | 560.98 | 687.50 | 497.17 | 1038.5 |
| `dds_reliable` | 65536 B | 400 | 0 | 4145.6 | 5261.1 | 5318.0 | 3625.2 | 5339.6 |

QoS 名称对齐 `testdata.py` 预设：`high_throughput` = BestEffort/KeepLast(1)/Volatile；
`reliable` = Reliable(max_blocking_time=0)/KeepLast(5000)/Volatile。
这不是冻结表导航 QoS，也没有改 `ddspubsub` / `rospubsub` 默认值。

## Upstream pytest

- `dimos_bridge` 官方命令 collection **失败**（`Image` stub ImportError），exit `2` — `pytest_dimos_bridge_attempt.txt`
- 临时 `topsun_dimos` checkout 官方 `pytest -m tool -k dds`：**24 passed** — `pytest_topsun_dimos_stdout.txt` / `pytest_topsun_dimos_junit.xml`
- 上游 harness 的 Latency 列是 **发完再等收齐** 的 drain time，不是 p50/p95/p99。本表分位数只来自 ping-pong。

