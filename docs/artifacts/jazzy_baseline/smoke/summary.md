# Jazzy ROS 2 baseline summary

- **STATUS:** `ok`
- **not_final_baseline:** `True`
- **host_class:** `cursor-cloud-vm`
- **ROS_DISTRO:** `jazzy`
- **topology:** `same-host`
- **domain:** `87`
- **UTC:** `2026-10-11T08:53:02Z`
- **CPU:** `Intel(R) Xeon(R) Processor` × 4
- **kernel:** `6.12.94+`

Cloud / lab measurement only. Not the final 10× denominator until repeated on the target robot or HIL host.

Latency is one-way (same-host `CLOCK_MONOTONIC` stamp) or ping-pong RTT.
Throughput is received messages after warmup ÷ measure window.
CPU is process util over that window; RSS is `/proc/<pid>/status` VmRSS.

Fast DDS and Cyclone stay in **separate** tables. This is not a bake-off
and not a Humble dual-chain SCOREBOARD update.

## `rmw_fastrtps_cpp`

dpkg / recorded version: `8.4.4-1noble.20260911.100940`

| qos | size (B) | mode | Hz | p50 (µs) | p90 (µs) | p99 (µs) | max | msg/s | MB/s | loss | CPU% pub/sub | RSS peak KiB pub/sub |
|-----|----------|------|----|----------|----------|----------|-----|------|------|------|---------------|------------------------|
| `reliable` | 1024 | `oneway` | 20.00 | 536.14 | 563.74 | 577.75 | 578.50 | 20.50 | 0.021 | 0.000 | 9.198 / 0.907 | 67628.0 / 67152.0 |
| `reliable` | 65536 | `oneway` | 20.00 | 524.49 | 568.83 | 620.07 | 622.03 | 20.50 | 1.343 | 0.000 | 8.798 / 0.725 | 67584.0 / 67328.0 |

## `rmw_cyclonedds_cpp`

dpkg / recorded version: `2.2.4-1noble.20260911.095700`

| qos | size (B) | mode | Hz | p50 (µs) | p90 (µs) | p99 (µs) | max | msg/s | MB/s | loss | CPU% pub/sub | RSS peak KiB pub/sub |
|-----|----------|------|----|----------|----------|----------|-----|------|------|------|---------------|------------------------|
| `reliable` | 1024 | `oneway` | 20.00 | 462.82 | 517.65 | 576.89 | 593.52 | 20.50 | 0.021 | 0.000 | 10.40 / 0.725 | 56176.0 / 56192.0 |
| `reliable` | 65536 | `oneway` | 20.00 | 572.37 | 625.40 | 840.26 | 901.08 | 20.50 | 1.344 | 0.000 | 10.40 / 0.724 | 56768.0 / 57208.0 |

## Method

- Warmup seconds are discarded before percentiles and throughput.
- Same-host uses two processes and `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST`.
- Cross-host is optional; a single VM records `STATUS: blocked`.
- Repeat recommended ≥ 3 on the robot / HIL host; isolate CPUs if you can.

