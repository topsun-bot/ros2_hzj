# Chain A same-process

- **STATUS:** `ok`
- **Chain:** `A`
- **Topology:** `same-process`
- **Metric:** round-trip time (ping-pong in scripts/bench/pingpong.py) （单位：microseconds）
- **Domain / RMW:** domain_id=`42` RMW=`rmw_fastrtps_cpp` ROS_DOMAIN_ID=`42`
- **CYCLONEDDS_URI / iceoryx:** `(unset)` / `default`
- **Payload sizes (bytes):** `[64]`
- **Inter-message gap:** `5.0` ms (target `200.0` Hz)
- **Chain A ros_msg:** `uint8_multiarray`

数字是 **ping-pong RTT**（本仓 `scripts/bench/pingpong.py` 里计时），不是中间件根因，也不是和另一条链可比的对照表。 **不是** 飞书现场 / 实机 / 跨机根因证明。

## p50 / p95 / p99（微秒，RTT）

| case | payload (B) | gap (ms) | samples | timeouts | p50 (µs) | p95 (µs) | p99 (µs) | min | max |
|------|-------------|----------|---------|----------|----------|----------|----------|-----|-----|
| `ros_high_throughput` | 64 B | 5.0 | 400 | 0 | 588.90 | 664.10 | 715.14 | 309.59 | 948.98 |
| `ros_reliable` | 64 B | 5.0 | 400 | 0 | 605.61 | 685.16 | 740.86 | 408.24 | 836.42 |

QoS 名称对齐 `testdata.py` 预设：`high_throughput` = BestEffort/KeepLast(1)/Volatile；
`reliable` = Reliable(max_blocking_time=0)/KeepLast(5000)/Volatile。
这不是冻结表导航 QoS，也没有改 `ddspubsub` / `rospubsub` 默认值。

## Upstream pytest

`BENCH_SKIP_PYTEST=1`（pytest still exited 0 in this image). Step A IMU-ish 64 B / 5 ms / 200 Hz. same-process is an **honesty check only — do not tune**. 400/400, 0 timeouts. Primary table is [`../chain_a_same_host/summary.md`](../chain_a_same_host/summary.md). 不要和链 B 混表。不是飞书 / 实机根因。

