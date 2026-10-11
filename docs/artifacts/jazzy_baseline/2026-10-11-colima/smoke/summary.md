# Jazzy ROS 2 baseline summary

- **STATUS:** `ok`
- **not_final_baseline:** `True`
- **host_class:** `colima-local-vm`
- **ROS_DISTRO:** `jazzy`
- **topology:** `same-host`
- **domain:** `87`
- **UTC:** `2026-10-11T09:18:37Z`
- **CPU:** `aarch64` × 4
- **kernel:** `6.8.0-117-generic`

Cloud / lab measurement only. Not the final 10× denominator until repeated on the target robot or HIL host.

Latency is one-way (same-host `CLOCK_MONOTONIC` stamp) or ping-pong RTT.
Throughput is received messages after warmup ÷ measure window.
CPU is process util over that window; RSS is `/proc/<pid>/status` VmRSS.

Fast DDS and Cyclone stay in **separate** tables. This is not a bake-off
and not a Humble dual-chain SCOREBOARD update.

## `rmw_fastrtps_cpp`

dpkg / recorded version: `8.4.4-1noble.20260902.140744`

| repeat | qos | size (B) | mode | Hz | p50 (µs) | p90 (µs) | p99 (µs) | max | msg/s | MB/s | loss | CPU% pub/sub | RSS peak KiB pub/sub | status | reason |
|-----|-----|----------|------|----|----------|----------|----------|-----|------|------|------|---------------|------------------------|--------|--------|
| 1 | reliable | 1024 | oneway | 20.00 | 757.84 | 3109.9 | 5418.0 | 6629.6 | 20.00 | 0.020 | 0.000 | 10.51 / 11.52 | 68160.0 / 67880.0 | ok |  |
| 1 | reliable | 65536 | oneway | 20.00 | 686.07 | 1257.0 | 3433.4 | 4473.7 | 20.00 | 1.311 | 0.000 | 10.50 / 9.506 | 68156.0 / 67924.0 | ok |  |

## `rmw_cyclonedds_cpp`

dpkg / recorded version: `2.2.4-1noble.20260902.140937`

| repeat | qos | size (B) | mode | Hz | p50 (µs) | p90 (µs) | p99 (µs) | max | msg/s | MB/s | loss | CPU% pub/sub | RSS peak KiB pub/sub | status | reason |
|-----|-----|----------|------|----|----------|----------|----------|-----|------|------|------|---------------|------------------------|--------|--------|
| 1 | reliable | 1024 | oneway | 20.00 | 561.57 | 1050.8 | 2088.5 | 2461.9 | 20.00 | 0.020 | 0.000 | 10.000 / 10.50 | 56528.0 / 56516.0 | ok |  |
| 1 | reliable | 65536 | oneway | 20.00 | 3382.6 | 5367.2 | 6077.2 | 6213.4 | 20.00 | 1.311 | 0.000 | 15.50 / 11.00 | 57116.0 / 57468.0 | ok |  |

## 重复运行的波动

- 汇总状态：`partial`；预期重复数：`1`。
- 以下统计针对各次运行的指标值；p50/p99 的均值不是合并样本后的总体分位数。
- sample_stdev 为样本标准差（n−1）；CV = sample_stdev / |mean|。
- n < 2 时标准差与 CV 不可用；mean = 0 时 CV 不可用，以 — / JSON null 表示。
- 至少 3 次成功、编号唯一、指标完整，且达到预期重复数，才标记 complete。
- 重复编号的全部记录、失败记录不参与统计；缺失或非有限指标逐项排除并报告。
- complete 仅表示此参数组的重复统计完整，不表示全矩阵、全部拓扑或最终基线验收完成。

### 参数组 1

rmw=`rmw_fastrtps_cpp` / rmw_version=`8.4.4-1noble.20260902.140744` / host_class=`colima-local-vm` / ros_distro=`jazzy` / topology=`same-host` / qos=`reliable` / mode=`oneway` / size_bytes=`1024` / hz_offered=`20.0` / duration_s=`2.0` / warmup_s=`0.5`

状态 `partial`；成功 1 / 预期 1；指标完整且编号唯一 1；观测记录 1。

- 警告：at least 3 fully measured unique successful repeats required; got 1

| metric | n | mean | sample_stdev | min | max | CV |
|---|---|---|---|---|---|---|
| `p50_us` | 1 | 757.84 | — | 757.84 | 757.84 | — |
| `p99_us` | 1 | 5418.0 | — | 5418.0 | 5418.0 | — |
| `max_us` | 1 | 6629.6 | — | 6629.6 | 6629.6 | — |
| `throughput_msg_s` | 1 | 20.00 | — | 20.00 | 20.00 | — |
| `throughput_mbyte_s` | 1 | 0.020 | — | 0.020 | 0.020 | — |
| `pub_cpu_percent` | 1 | 10.51 | — | 10.51 | 10.51 | — |
| `sub_cpu_percent` | 1 | 11.52 | — | 11.52 | 11.52 | — |
| `pub_rss_kb_peak` | 1 | 68160.0 | — | 68160.0 | 68160.0 | — |
| `sub_rss_kb_peak` | 1 | 67880.0 | — | 67880.0 | 67880.0 | — |

### 参数组 2

rmw=`rmw_fastrtps_cpp` / rmw_version=`8.4.4-1noble.20260902.140744` / host_class=`colima-local-vm` / ros_distro=`jazzy` / topology=`same-host` / qos=`reliable` / mode=`oneway` / size_bytes=`65536` / hz_offered=`20.0` / duration_s=`2.0` / warmup_s=`0.5`

状态 `partial`；成功 1 / 预期 1；指标完整且编号唯一 1；观测记录 1。

- 警告：at least 3 fully measured unique successful repeats required; got 1

| metric | n | mean | sample_stdev | min | max | CV |
|---|---|---|---|---|---|---|
| `p50_us` | 1 | 686.07 | — | 686.07 | 686.07 | — |
| `p99_us` | 1 | 3433.4 | — | 3433.4 | 3433.4 | — |
| `max_us` | 1 | 4473.7 | — | 4473.7 | 4473.7 | — |
| `throughput_msg_s` | 1 | 20.00 | — | 20.00 | 20.00 | — |
| `throughput_mbyte_s` | 1 | 1.311 | — | 1.311 | 1.311 | — |
| `pub_cpu_percent` | 1 | 10.50 | — | 10.50 | 10.50 | — |
| `sub_cpu_percent` | 1 | 9.506 | — | 9.506 | 9.506 | — |
| `pub_rss_kb_peak` | 1 | 68156.0 | — | 68156.0 | 68156.0 | — |
| `sub_rss_kb_peak` | 1 | 67924.0 | — | 67924.0 | 67924.0 | — |

### 参数组 3

rmw=`rmw_cyclonedds_cpp` / rmw_version=`2.2.4-1noble.20260902.140937` / host_class=`colima-local-vm` / ros_distro=`jazzy` / topology=`same-host` / qos=`reliable` / mode=`oneway` / size_bytes=`1024` / hz_offered=`20.0` / duration_s=`2.0` / warmup_s=`0.5`

状态 `partial`；成功 1 / 预期 1；指标完整且编号唯一 1；观测记录 1。

- 警告：at least 3 fully measured unique successful repeats required; got 1

| metric | n | mean | sample_stdev | min | max | CV |
|---|---|---|---|---|---|---|
| `p50_us` | 1 | 561.57 | — | 561.57 | 561.57 | — |
| `p99_us` | 1 | 2088.5 | — | 2088.5 | 2088.5 | — |
| `max_us` | 1 | 2461.9 | — | 2461.9 | 2461.9 | — |
| `throughput_msg_s` | 1 | 20.00 | — | 20.00 | 20.00 | — |
| `throughput_mbyte_s` | 1 | 0.020 | — | 0.020 | 0.020 | — |
| `pub_cpu_percent` | 1 | 10.000 | — | 10.000 | 10.000 | — |
| `sub_cpu_percent` | 1 | 10.50 | — | 10.50 | 10.50 | — |
| `pub_rss_kb_peak` | 1 | 56528.0 | — | 56528.0 | 56528.0 | — |
| `sub_rss_kb_peak` | 1 | 56516.0 | — | 56516.0 | 56516.0 | — |

### 参数组 4

rmw=`rmw_cyclonedds_cpp` / rmw_version=`2.2.4-1noble.20260902.140937` / host_class=`colima-local-vm` / ros_distro=`jazzy` / topology=`same-host` / qos=`reliable` / mode=`oneway` / size_bytes=`65536` / hz_offered=`20.0` / duration_s=`2.0` / warmup_s=`0.5`

状态 `partial`；成功 1 / 预期 1；指标完整且编号唯一 1；观测记录 1。

- 警告：at least 3 fully measured unique successful repeats required; got 1

| metric | n | mean | sample_stdev | min | max | CV |
|---|---|---|---|---|---|---|
| `p50_us` | 1 | 3382.6 | — | 3382.6 | 3382.6 | — |
| `p99_us` | 1 | 6077.2 | — | 6077.2 | 6077.2 | — |
| `max_us` | 1 | 6213.4 | — | 6213.4 | 6213.4 | — |
| `throughput_msg_s` | 1 | 20.00 | — | 20.00 | 20.00 | — |
| `throughput_mbyte_s` | 1 | 1.311 | — | 1.311 | 1.311 | — |
| `pub_cpu_percent` | 1 | 15.50 | — | 15.50 | 15.50 | — |
| `sub_cpu_percent` | 1 | 11.00 | — | 11.00 | 11.00 | — |
| `pub_rss_kb_peak` | 1 | 57116.0 | — | 57116.0 | 57116.0 | — |
| `sub_rss_kb_peak` | 1 | 57468.0 | — | 57468.0 | 57468.0 | — |

## Method

- Warmup seconds are discarded before percentiles and throughput.
- Same-host uses two processes and `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST`.
- 同进程、跨进程、跨机均为任务要求；same-host 结果只覆盖本机跨进程。
- 每组至少重复 3 次并检查波动汇总；smoke 运行不满足完整基线验收。

