# Chain A cross-host-UDP

- **STATUS:** `blocked`
- **Chain:** `A`
- **Topology:** `cross-host-UDP`
- **Metric:** rtt （单位：microseconds）
- **Domain / RMW:** domain_id=`` RMW=`(n/a)` ROS_DOMAIN_ID=`(n/a)`
- **CYCLONEDDS_URI / iceoryx:** `(unset)` / ``

数字是 **ping-pong RTT**（本仓 `scripts/bench/pingpong.py` 里计时），不是中间件根因，也不是和另一条链可比的对照表。

## p50 / p95 / p99（微秒，RTT）

| case | msg size | samples | timeouts | p50 (µs) | p95 (µs) | p99 (µs) | min | max |
|------|----------|---------|----------|----------|----------|----------|-----|-----|

QoS 名称对齐 `testdata.py` 预设：`high_throughput` = BestEffort/KeepLast(1)/Volatile；
`reliable` = Reliable(max_blocking_time=0)/KeepLast(5000)/Volatile。
这不是冻结表导航 QoS，也没有改 `ddspubsub` / `rospubsub` 默认值。

## Upstream pytest

Not run: needs a second host.

