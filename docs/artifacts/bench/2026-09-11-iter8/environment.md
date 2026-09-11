# Environment — iter8 remasure (Chain A)

Shared facts. Per-topology files: [`chain_a_same_process/environment.md`](chain_a_same_process/environment.md), [`chain_a_same_host/environment.md`](chain_a_same_host/environment.md).

- **UTC date dir:** `2026-09-11-iter8`
- **hostname class:** `cursor-cloud-vm` (`hostname=cursor`)
- **Host OS:** Ubuntu 24.04.4 LTS
- **Bench OS (container):** Ubuntu 22.04.5 LTS / Humble
- **CPU:** Intel Xeon × 4 logical (same class as iter7 / iter6 / iter5)
- **Chain:** A only (`rmw_fastrtps_cpp`, `ROS_DOMAIN_ID=42`)
- **image:** `osrf/ros:humble-desktop` digest `sha256:fb07245b32187d74350be25323d8ad2f8ca5c25c325759911a1eff2267a49c1e` (same as iter7 / iter6 / iter5)
- **Command:** `BENCH_DATE=2026-09-11-iter8 CHAIN_A_IMAGE=osrf/ros:humble-desktop IMU_HF_CHAINS=A ./scripts/bench/run_imu_hf.sh`
- **Payload / gap / samples:** **64 B**; **5 ms** (target **200 Hz**, IMU-ish); 400 samples + 40 warmup; timeout 1 s
- **Primary metric:** jitter (RTT p95/p99 + inter-message interval). Do not claim success from p50/mean.
- **git SHA ros2_hzj (at remasure):** `be6016bc049aebc191784c1c0e376f2c19c8a361` (`leaseAnnouncement` 15 s on the default participant for this run only)
- **Probe (not kept):** `<leaseAnnouncement><sec>15</sec></leaseAnnouncement>`. XMLPARSER accepted it (empty pingpong stderr). Reverted after remasure. Keep/discard judged on jitter vs iter7, not p50.
- **Landed knobs (unchanged):** `healthy_check_timeout_ms` 10000; `maxMessageSize=280000` / `segment_size=2 MiB`; builtin UDP+SHM; 2 MiB sockets; `send_buffers` 32 / `dynamic=false`. iter6 `port_queue_capacity` 64 stays discarded. Exclusive / oversized SHM stays discarded.

These facts describe the measurement environment. They are **not** a root-cause analysis. Do not mix Chain A and Chain B. This does not prove a Feishu / real-robot / cross-host root cause.

这些环境记录 **不是** 飞书现场、实机、或跨机根因证明。
