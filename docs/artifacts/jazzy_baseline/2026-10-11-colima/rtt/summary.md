# Jazzy ROS 2 baseline summary

- **STATUS:** `ok`
- **not_final_baseline:** `True`
- **host_class:** `colima-local-vm`
- **ROS_DISTRO:** `jazzy`
- **topology:** `same-host`
- **domain:** `87`
- **UTC:** `2026-10-11T11:30:15Z`
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
| 1 | reliable | 1024 | rtt | 10.00 | 1123.8 | 1599.5 | 1808.7 | 1831.9 | 10.00 | 0.010 | 0.000 | 6.980 / 5.985 | 68164.0 / 67924.0 | ok |  |
| 1 | reliable | 4194304 | rtt | 10.00 | 38636.6 | 42900.7 | 43895.2 | 44005.7 | 10.00 | 41.94 | 0.000 | 20.01 / 11.01 | 80776.0 / 88692.0 | ok |  |
| 1 | best_effort | 1024 | rtt | 10.00 | 1220.3 | 2659.7 | 3051.0 | 3094.5 | 10.00 | 0.010 | 0.000 | 6.965 / 7.005 | 68140.0 / 67904.0 | ok |  |
| 1 | best_effort | 4194304 | rtt | 10.00 | 16159.3 | 16687.4 | 16806.2 | 16819.4 | 2.000 | 8.389 | 0.800 | 17.06 / 8.027 | 88840.0 / 88692.0 | ok |  |

## `rmw_cyclonedds_cpp`

dpkg / recorded version: `2.2.4-1noble.20260902.140937`

| repeat | qos | size (B) | mode | Hz | p50 (µs) | p90 (µs) | p99 (µs) | max | msg/s | MB/s | loss | CPU% pub/sub | RSS peak KiB pub/sub | status | reason |
|-----|-----|----------|------|----|----------|----------|----------|-----|------|------|------|---------------|------------------------|--------|--------|
| 1 | reliable | 1024 | rtt | 10.00 | 955.35 | 2381.7 | 10901.9 | 11848.5 | 10.00 | 0.010 | 0.000 | 10.00 / 8.002 | 56588.0 / 56536.0 | ok |  |
| 1 | reliable | 4194304 | rtt | 10.00 | 118022.5 | 363078.0 | 437908.5 | 446223.0 | 10.00 | 41.94 | 0.000 | 28.03 / 24.04 | 88936.0 / 95592.0 | ok |  |
| 1 | best_effort | 1024 | rtt | 10.00 | 1282.7 | 1850.8 | 2466.7 | 2535.2 | 10.00 | 0.010 | 0.000 | 7.001 / 7.006 | 56536.0 / 56580.0 | ok |  |
| 1 | best_effort | 4194304 | rtt | 10.00 | 32138.5 | 34598.6 | 35152.2 | 35213.7 | 2.000 | 8.389 | 0.800 | 22.01 / 16.01 | 78380.0 / 74224.0 | ok |  |

## 重复运行的波动

- 汇总状态：`partial`；预期重复数：`1`。
- 以下统计针对各次运行的指标值；p50/p99 的均值不是合并样本后的总体分位数。
- sample_stdev 为样本标准差（n−1）；CV = sample_stdev / |mean|。
- n < 2 时标准差与 CV 不可用；mean = 0 时 CV 不可用，以 — / JSON null 表示。
- 至少 3 次成功、编号唯一、指标完整，且达到预期重复数，才标记 complete。
- 重复编号的全部记录、失败记录不参与统计；缺失或非有限指标逐项排除并报告。
- complete 仅表示此参数组的重复统计完整，不表示全矩阵、全部拓扑或最终基线验收完成。

### 参数组 1

rmw=`rmw_fastrtps_cpp` / rmw_version=`8.4.4-1noble.20260902.140744` / host_class=`colima-local-vm` / ros_distro=`jazzy` / topology=`same-host` / qos=`reliable` / mode=`rtt` / size_bytes=`1024` / hz_offered=`10.0` / duration_s=`1.0` / warmup_s=`0.2`

状态 `partial`；成功 1 / 预期 1；指标完整且编号唯一 1；观测记录 1。

- 警告：at least 3 fully measured unique successful repeats required; got 1

| metric | n | mean | sample_stdev | min | max | CV |
|---|---|---|---|---|---|---|
| `p50_us` | 1 | 1123.8 | — | 1123.8 | 1123.8 | — |
| `p99_us` | 1 | 1808.7 | — | 1808.7 | 1808.7 | — |
| `max_us` | 1 | 1831.9 | — | 1831.9 | 1831.9 | — |
| `throughput_msg_s` | 1 | 10.00 | — | 10.00 | 10.00 | — |
| `throughput_mbyte_s` | 1 | 0.010 | — | 0.010 | 0.010 | — |
| `pub_cpu_percent` | 1 | 6.980 | — | 6.980 | 6.980 | — |
| `sub_cpu_percent` | 1 | 5.985 | — | 5.985 | 5.985 | — |
| `pub_rss_kb_peak` | 1 | 68164.0 | — | 68164.0 | 68164.0 | — |
| `sub_rss_kb_peak` | 1 | 67924.0 | — | 67924.0 | 67924.0 | — |

### 参数组 2

rmw=`rmw_fastrtps_cpp` / rmw_version=`8.4.4-1noble.20260902.140744` / host_class=`colima-local-vm` / ros_distro=`jazzy` / topology=`same-host` / qos=`reliable` / mode=`rtt` / size_bytes=`4194304` / hz_offered=`10.0` / duration_s=`1.0` / warmup_s=`0.2`

状态 `partial`；成功 1 / 预期 1；指标完整且编号唯一 1；观测记录 1。

- 警告：at least 3 fully measured unique successful repeats required; got 1

| metric | n | mean | sample_stdev | min | max | CV |
|---|---|---|---|---|---|---|
| `p50_us` | 1 | 38636.6 | — | 38636.6 | 38636.6 | — |
| `p99_us` | 1 | 43895.2 | — | 43895.2 | 43895.2 | — |
| `max_us` | 1 | 44005.7 | — | 44005.7 | 44005.7 | — |
| `throughput_msg_s` | 1 | 10.00 | — | 10.00 | 10.00 | — |
| `throughput_mbyte_s` | 1 | 41.94 | — | 41.94 | 41.94 | — |
| `pub_cpu_percent` | 1 | 20.01 | — | 20.01 | 20.01 | — |
| `sub_cpu_percent` | 1 | 11.01 | — | 11.01 | 11.01 | — |
| `pub_rss_kb_peak` | 1 | 80776.0 | — | 80776.0 | 80776.0 | — |
| `sub_rss_kb_peak` | 1 | 88692.0 | — | 88692.0 | 88692.0 | — |

### 参数组 3

rmw=`rmw_fastrtps_cpp` / rmw_version=`8.4.4-1noble.20260902.140744` / host_class=`colima-local-vm` / ros_distro=`jazzy` / topology=`same-host` / qos=`best_effort` / mode=`rtt` / size_bytes=`1024` / hz_offered=`10.0` / duration_s=`1.0` / warmup_s=`0.2`

状态 `partial`；成功 1 / 预期 1；指标完整且编号唯一 1；观测记录 1。

- 警告：at least 3 fully measured unique successful repeats required; got 1

| metric | n | mean | sample_stdev | min | max | CV |
|---|---|---|---|---|---|---|
| `p50_us` | 1 | 1220.3 | — | 1220.3 | 1220.3 | — |
| `p99_us` | 1 | 3051.0 | — | 3051.0 | 3051.0 | — |
| `max_us` | 1 | 3094.5 | — | 3094.5 | 3094.5 | — |
| `throughput_msg_s` | 1 | 10.00 | — | 10.00 | 10.00 | — |
| `throughput_mbyte_s` | 1 | 0.010 | — | 0.010 | 0.010 | — |
| `pub_cpu_percent` | 1 | 6.965 | — | 6.965 | 6.965 | — |
| `sub_cpu_percent` | 1 | 7.005 | — | 7.005 | 7.005 | — |
| `pub_rss_kb_peak` | 1 | 68140.0 | — | 68140.0 | 68140.0 | — |
| `sub_rss_kb_peak` | 1 | 67904.0 | — | 67904.0 | 67904.0 | — |

### 参数组 4

rmw=`rmw_fastrtps_cpp` / rmw_version=`8.4.4-1noble.20260902.140744` / host_class=`colima-local-vm` / ros_distro=`jazzy` / topology=`same-host` / qos=`best_effort` / mode=`rtt` / size_bytes=`4194304` / hz_offered=`10.0` / duration_s=`1.0` / warmup_s=`0.2`

状态 `partial`；成功 1 / 预期 1；指标完整且编号唯一 1；观测记录 1。

- 警告：at least 3 fully measured unique successful repeats required; got 1

| metric | n | mean | sample_stdev | min | max | CV |
|---|---|---|---|---|---|---|
| `p50_us` | 1 | 16159.3 | — | 16159.3 | 16159.3 | — |
| `p99_us` | 1 | 16806.2 | — | 16806.2 | 16806.2 | — |
| `max_us` | 1 | 16819.4 | — | 16819.4 | 16819.4 | — |
| `throughput_msg_s` | 1 | 2.000 | — | 2.000 | 2.000 | — |
| `throughput_mbyte_s` | 1 | 8.389 | — | 8.389 | 8.389 | — |
| `pub_cpu_percent` | 1 | 17.06 | — | 17.06 | 17.06 | — |
| `sub_cpu_percent` | 1 | 8.027 | — | 8.027 | 8.027 | — |
| `pub_rss_kb_peak` | 1 | 88840.0 | — | 88840.0 | 88840.0 | — |
| `sub_rss_kb_peak` | 1 | 88692.0 | — | 88692.0 | 88692.0 | — |

### 参数组 5

rmw=`rmw_cyclonedds_cpp` / rmw_version=`2.2.4-1noble.20260902.140937` / host_class=`colima-local-vm` / ros_distro=`jazzy` / topology=`same-host` / qos=`reliable` / mode=`rtt` / size_bytes=`1024` / hz_offered=`10.0` / duration_s=`1.0` / warmup_s=`0.2`

状态 `partial`；成功 1 / 预期 1；指标完整且编号唯一 1；观测记录 1。

- 警告：at least 3 fully measured unique successful repeats required; got 1

| metric | n | mean | sample_stdev | min | max | CV |
|---|---|---|---|---|---|---|
| `p50_us` | 1 | 955.35 | — | 955.35 | 955.35 | — |
| `p99_us` | 1 | 10901.9 | — | 10901.9 | 10901.9 | — |
| `max_us` | 1 | 11848.5 | — | 11848.5 | 11848.5 | — |
| `throughput_msg_s` | 1 | 10.00 | — | 10.00 | 10.00 | — |
| `throughput_mbyte_s` | 1 | 0.010 | — | 0.010 | 0.010 | — |
| `pub_cpu_percent` | 1 | 10.00 | — | 10.00 | 10.00 | — |
| `sub_cpu_percent` | 1 | 8.002 | — | 8.002 | 8.002 | — |
| `pub_rss_kb_peak` | 1 | 56588.0 | — | 56588.0 | 56588.0 | — |
| `sub_rss_kb_peak` | 1 | 56536.0 | — | 56536.0 | 56536.0 | — |

### 参数组 6

rmw=`rmw_cyclonedds_cpp` / rmw_version=`2.2.4-1noble.20260902.140937` / host_class=`colima-local-vm` / ros_distro=`jazzy` / topology=`same-host` / qos=`reliable` / mode=`rtt` / size_bytes=`4194304` / hz_offered=`10.0` / duration_s=`1.0` / warmup_s=`0.2`

状态 `partial`；成功 1 / 预期 1；指标完整且编号唯一 1；观测记录 1。

- 警告：at least 3 fully measured unique successful repeats required; got 1

| metric | n | mean | sample_stdev | min | max | CV |
|---|---|---|---|---|---|---|
| `p50_us` | 1 | 118022.5 | — | 118022.5 | 118022.5 | — |
| `p99_us` | 1 | 437908.5 | — | 437908.5 | 437908.5 | — |
| `max_us` | 1 | 446223.0 | — | 446223.0 | 446223.0 | — |
| `throughput_msg_s` | 1 | 10.00 | — | 10.00 | 10.00 | — |
| `throughput_mbyte_s` | 1 | 41.94 | — | 41.94 | 41.94 | — |
| `pub_cpu_percent` | 1 | 28.03 | — | 28.03 | 28.03 | — |
| `sub_cpu_percent` | 1 | 24.04 | — | 24.04 | 24.04 | — |
| `pub_rss_kb_peak` | 1 | 88936.0 | — | 88936.0 | 88936.0 | — |
| `sub_rss_kb_peak` | 1 | 95592.0 | — | 95592.0 | 95592.0 | — |

### 参数组 7

rmw=`rmw_cyclonedds_cpp` / rmw_version=`2.2.4-1noble.20260902.140937` / host_class=`colima-local-vm` / ros_distro=`jazzy` / topology=`same-host` / qos=`best_effort` / mode=`rtt` / size_bytes=`1024` / hz_offered=`10.0` / duration_s=`1.0` / warmup_s=`0.2`

状态 `partial`；成功 1 / 预期 1；指标完整且编号唯一 1；观测记录 1。

- 警告：at least 3 fully measured unique successful repeats required; got 1

| metric | n | mean | sample_stdev | min | max | CV |
|---|---|---|---|---|---|---|
| `p50_us` | 1 | 1282.7 | — | 1282.7 | 1282.7 | — |
| `p99_us` | 1 | 2466.7 | — | 2466.7 | 2466.7 | — |
| `max_us` | 1 | 2535.2 | — | 2535.2 | 2535.2 | — |
| `throughput_msg_s` | 1 | 10.00 | — | 10.00 | 10.00 | — |
| `throughput_mbyte_s` | 1 | 0.010 | — | 0.010 | 0.010 | — |
| `pub_cpu_percent` | 1 | 7.001 | — | 7.001 | 7.001 | — |
| `sub_cpu_percent` | 1 | 7.006 | — | 7.006 | 7.006 | — |
| `pub_rss_kb_peak` | 1 | 56536.0 | — | 56536.0 | 56536.0 | — |
| `sub_rss_kb_peak` | 1 | 56580.0 | — | 56580.0 | 56580.0 | — |

### 参数组 8

rmw=`rmw_cyclonedds_cpp` / rmw_version=`2.2.4-1noble.20260902.140937` / host_class=`colima-local-vm` / ros_distro=`jazzy` / topology=`same-host` / qos=`best_effort` / mode=`rtt` / size_bytes=`4194304` / hz_offered=`10.0` / duration_s=`1.0` / warmup_s=`0.2`

状态 `partial`；成功 1 / 预期 1；指标完整且编号唯一 1；观测记录 1。

- 警告：at least 3 fully measured unique successful repeats required; got 1

| metric | n | mean | sample_stdev | min | max | CV |
|---|---|---|---|---|---|---|
| `p50_us` | 1 | 32138.5 | — | 32138.5 | 32138.5 | — |
| `p99_us` | 1 | 35152.2 | — | 35152.2 | 35152.2 | — |
| `max_us` | 1 | 35213.7 | — | 35213.7 | 35213.7 | — |
| `throughput_msg_s` | 1 | 2.000 | — | 2.000 | 2.000 | — |
| `throughput_mbyte_s` | 1 | 8.389 | — | 8.389 | 8.389 | — |
| `pub_cpu_percent` | 1 | 22.01 | — | 22.01 | 22.01 | — |
| `sub_cpu_percent` | 1 | 16.01 | — | 16.01 | 16.01 | — |
| `pub_rss_kb_peak` | 1 | 78380.0 | — | 78380.0 | 78380.0 | — |
| `sub_rss_kb_peak` | 1 | 74224.0 | — | 74224.0 | 74224.0 | — |

## Method

- Warmup seconds are discarded before percentiles and throughput.
- Same-host uses two processes; the default configuration sets `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` (see each processes.json for the effective environment).
- 同进程、跨进程、跨机均为任务要求；same-host 结果只覆盖本机跨进程。
- 每组至少重复 3 次并检查波动汇总；smoke 运行不满足完整基线验收。

