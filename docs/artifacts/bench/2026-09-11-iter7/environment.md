# Environment — iter7 remasure (Chain A)

Shared facts. Per-topology files: [`chain_a_same_process/environment.md`](chain_a_same_process/environment.md), [`chain_a_same_host/environment.md`](chain_a_same_host/environment.md).

- **UTC date dir:** `2026-09-11-iter7`
- **hostname class:** `cursor-cloud-vm` (`hostname=cursor`)
- **Host OS:** Ubuntu 24.04.4 LTS
- **Bench OS (container):** Ubuntu 22.04.5 LTS / Humble
- **CPU:** Intel Xeon × 4 logical (same class as iter6 / iter5)
- **Chain:** A only (`rmw_fastrtps_cpp`, `ROS_DOMAIN_ID=42`)
- **image:** `osrf/ros:humble-desktop` digest `sha256:fb07245b32187d74350be25323d8ad2f8ca5c25c325759911a1eff2267a49c1e` (same as iter6 / iter5 / iter4 / iter3 / iter2-after)
- **Command:** `BENCH_DATE=2026-09-11-iter7 CHAIN_A_IMAGE=osrf/ros:humble-desktop IMU_HF_CHAINS=A ./scripts/bench/run_imu_hf.sh`
- **Payload / gap / samples:** **64 B**; **5 ms** (target **200 Hz**, IMU-ish); 400 samples + 40 warmup; timeout 1 s
- **Primary metric:** jitter (RTT p95/p99 + inter-message interval). Do not claim success from p50/mean.
- **git SHA ros2_hzj (at remasure):** `5efbca352b9e442234412f982c7e6af59f85c0c8` (`healthy_check_timeout_ms` 10000 on `shm_midsize`)
- **Knob (kept):** `<healthy_check_timeout_ms>10000</healthy_check_timeout_ms>`. XMLPARSER accepted it (empty pingpong stderr). Keep/discard judged on jitter, not p50.
- **Landed knobs (unchanged):** `maxMessageSize=280000` / `segment_size=2 MiB`; builtin UDP+SHM; 2 MiB sockets; `send_buffers` 32 / `dynamic=false`. iter6 `port_queue_capacity` 64 stays discarded. Exclusive / oversized SHM stays discarded.

These facts describe the measurement environment. They are **not** a root-cause analysis. Do not mix Chain A and Chain B. This does not prove a Feishu / real-robot / cross-host root cause.

这些环境记录 **不是** 飞书现场、实机、或跨机根因证明。
