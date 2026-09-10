# Environment — iter1 remasure (Chain A)

Shared facts for this UTC-date directory. Per-topology files: [`chain_a_same_process/environment.md`](chain_a_same_process/environment.md), [`chain_a_same_host/environment.md`](chain_a_same_host/environment.md).

- **UTC date dir:** `2026-09-10-iter1`
- **hostname class:** `cursor-cloud-vm` (`hostname=cursor`)
- **Host OS:** Ubuntu 24.04.4 LTS
- **Bench OS (container):** Ubuntu 22.04.5 LTS / Humble
- **CPU:** Intel Xeon × 4 logical (same class as 2026-09-10 baseline)
- **Chain:** A only (`rmw_fastrtps_cpp`, `ROS_DOMAIN_ID=42`)
- **image:** `ros2_hzj/ros:humble` (`6f08fd8ce67c`, ~6.68GB) built from `docker/ros/Dockerfile` (Humble + Nav2; **no** RMW/domain ENV baked in)
- **Command:** `BENCH_DATE=2026-09-10-iter1 CHAIN_A_TOPOLOGIES='same-process same-host' ./scripts/bench/docker_chain_a.sh`
- **Samples / sizes:** 400 samples; 64 / 1024 / 16384 / 65536 B (same as baseline)
- **git SHA ros2_hzj (at remasure):** `a9cc1fc1f4090c511751979153738e668d3e702c`
- **XMLPARSER:** iter1 ping-pong stdout has **no** `Invalid element ... Name: history` / `Error parsing '.../fastdds.xml'`. Baseline 2026-09-10 did.

These facts describe the measurement environment. They are **not** a root-cause analysis. Do not mix Chain A and Chain B in one table. This does not prove a Feishu / large-packet / real-robot root cause.
