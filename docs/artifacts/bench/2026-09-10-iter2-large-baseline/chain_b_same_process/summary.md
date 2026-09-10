# Chain B same-process

- **STATUS:** `ok`
- **Chain:** `B`
- **Topology:** `same-process`
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
| `dds_high_throughput` | 102400 B | 100.0 | 80 | 0 | 5038.8 | 5101.6 | 5142.7 | 4992.4 | 5150.8 |
| `dds_high_throughput` | 262144 B | 100.0 | 80 | 0 | 13002.5 | 13130.9 | 13226.7 | 12930.9 | 13327.0 |
| `dds_high_throughput` | 1048576 B | 100.0 | 80 | 0 | 51267.8 | 52115.5 | 54319.7 | 50940.4 | 60239.7 |
| `dds_reliable` | 102400 B | 100.0 | 80 | 0 | 2858.7 | 2927.3 | 3091.0 | 2810.6 | 3133.7 |
| `dds_reliable` | 262144 B | 100.0 | 80 | 0 | 7530.2 | 7599.4 | 7756.9 | 7418.0 | 7973.6 |
| `dds_reliable` | 1048576 B | 100.0 | 80 | 0 | 49289.7 | 49556.1 | 49718.9 | 48953.3 | 49753.1 |

QoS 名称对齐 `testdata.py` 预设：`high_throughput` = BestEffort/KeepLast(1)/Volatile；
`reliable` = Reliable(max_blocking_time=0)/KeepLast(5000)/Volatile。
这不是冻结表导航 QoS，也没有改 `ddspubsub` / `rospubsub` 默认值。

## Upstream pytest

- `dimos_bridge` official command exit `0` — log: `pytest_dimos_bridge_attempt.txt`
- temporary `topsun_dimos` checkout official command exit `0` — log: `pytest_topsun_dimos_stdout.txt`, junit: `pytest_topsun_dimos_junit.xml`
- 上游 harness 的 Latency 列是 **发完再等收齐** 的 drain time，不是 p50/p95/p99。

