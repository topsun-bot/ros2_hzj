# Jazzy ROS 2 baseline summary

- **STATUS:** `blocked`
- **not_final_baseline:** `True`
- **host_class:** `unknown`
- **ROS_DISTRO:** `(unset)`
- **topology:** `cross-host`
- **domain:** `87`
- **UTC:** `2026-10-11T11:30:51Z`
- **CPU:** `arm` × 16
- **kernel:** `25.5.0`

Cloud / lab measurement only. Not the final 10× denominator until repeated on the target robot or HIL host.

Latency is one-way (same-host `CLOCK_MONOTONIC` stamp) or ping-pong RTT.
Throughput is received messages after warmup ÷ measure window.
CPU is process util over that window; RSS is `/proc/<pid>/status` VmRSS.

Fast DDS and Cyclone stay in **separate** tables. This is not a bake-off
and not a Humble dual-chain SCOREBOARD update.

## Blocked

cross-host orchestration is not implemented: it requires remote startup, a coordinated measurement window and result collection. Independent worker starts do not constitute a cross-host baseline.

## `rmw_fastrtps_cpp`

dpkg / recorded version: `not-installed`

| repeat | qos | size (B) | mode | Hz | p50 (µs) | p90 (µs) | p99 (µs) | max | msg/s | MB/s | loss | CPU% pub/sub | RSS peak KiB pub/sub | status | reason |
|-----|-----|----------|------|----|----------|----------|----------|-----|------|------|------|---------------|------------------------|--------|--------|
| 1 | reliable | 1024 | oneway | 100.00 | — | — | — | — | — | — | — | — | — | blocked | cross-host orchestration is not implemented: it requires remote startup, a coordinated measurement window and result collection. Independent worker starts do not constitute a cross-host baseline. |

## 重复运行的波动

- 汇总状态：`blocked`；预期重复数：`1`。
- 以下统计针对各次运行的指标值；p50/p99 的均值不是合并样本后的总体分位数。
- sample_stdev 为样本标准差（n−1）；CV = sample_stdev / |mean|。
- n < 2 时标准差与 CV 不可用；mean = 0 时 CV 不可用，以 — / JSON null 表示。
- 至少 3 次成功、编号唯一、指标完整，且达到预期重复数，才标记 complete。
- 重复编号的全部记录、失败记录不参与统计；缺失或非有限指标逐项排除并报告。
- complete 仅表示此参数组的重复统计完整，不表示全矩阵、全部拓扑或最终基线验收完成。

### 参数组 1

rmw=`rmw_fastrtps_cpp` / rmw_version=`` / host_class=`unknown` / ros_distro=`` / topology=`cross-host` / qos=`reliable` / mode=`oneway` / size_bytes=`1024` / hz_offered=`100.0` / duration_s=`10.0` / warmup_s=`2.0`

状态 `blocked`；成功 0 / 预期 1；指标完整且编号唯一 0；观测记录 1。

- 警告：missing grouping fields: ['rmw_version', 'ros_distro']
- 警告：repeat 1: status=blocked; cross-host orchestration is not implemented: it requires remote startup, a coordinated measurement window and result collection. Independent worker starts do not constitute a cross-host baseline.
- 警告：missing successful repeats: [1]
- 警告：at least 3 fully measured unique successful repeats required; got 0

| metric | n | mean | sample_stdev | min | max | CV |
|---|---|---|---|---|---|---|
| `p50_us` | 0 | — | — | — | — | — |
| `p99_us` | 0 | — | — | — | — | — |
| `max_us` | 0 | — | — | — | — | — |
| `throughput_msg_s` | 0 | — | — | — | — | — |
| `throughput_mbyte_s` | 0 | — | — | — | — | — |
| `pub_cpu_percent` | 0 | — | — | — | — | — |
| `sub_cpu_percent` | 0 | — | — | — | — | — |
| `pub_rss_kb_peak` | 0 | — | — | — | — | — |
| `sub_rss_kb_peak` | 0 | — | — | — | — | — |

## Method

- Warmup seconds are discarded before percentiles and throughput.
- Same-host uses two processes; the default configuration sets `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` (see each processes.json for the effective environment).
- 同进程、跨进程、跨机均为任务要求；same-host 结果只覆盖本机跨进程。
- 每组至少重复 3 次并检查波动汇总；smoke 运行不满足完整基线验收。

