# Environment — iter6 IMU baseline (Chain A)

Shared facts. Per-topology files: [`chain_a_same_process/environment.md`](chain_a_same_process/environment.md), [`chain_a_same_host/environment.md`](chain_a_same_host/environment.md).

- **UTC date dir:** `2026-09-10-iter6-imu-baseline`
- **hostname class:** `cursor-cloud-vm` (`hostname=cursor`)
- **Host OS:** Ubuntu 24.04.4 LTS
- **Bench OS (container):** Ubuntu 22.04.5 LTS / Humble
- **CPU:** Intel Xeon × 4 logical (same class as iter5)
- **Chain:** A only (`rmw_fastrtps_cpp`, `ROS_DOMAIN_ID=42`)
- **image:** `osrf/ros:humble-desktop` digest `sha256:fb07245b32187d74350be25323d8ad2f8ca5c25c325759911a1eff2267a49c1e` (same as iter5 / iter4 / iter3 / iter2-after)
- **Command:** `BENCH_DATE=2026-09-10-iter6-imu-baseline CHAIN_A_IMAGE=osrf/ros:humble-desktop IMU_HF_CHAINS=A ./scripts/bench/run_imu_hf.sh`
- **Payload / gap / samples:** **64 B**; **5 ms** (target **200 Hz**, IMU-ish); 400 samples + 40 warmup; timeout 1 s
- **Primary metric:** jitter (RTT p95/p99 + inter-message interval). Do not claim success from p50/mean. **64 B / 200 Hz** nailed before any knob.
- **git SHA ros2_hzj (at remasure):** `2b8f666` (jitter fields in `pingpong.py`; `config/fastdds.xml` still the iter5-accepted seed; no Step B knob)
- **Knobs (unchanged from iter5):** additive user SHM `maxMessageSize=280000` / `segment_size=2 MiB`; builtin UDP+SHM; iter2 2 MiB sockets; iter3/4 `send_buffers` 32 / `dynamic=false`. **No new knob in Step A.**
- **XMLPARSER:** pingpong stderr empty (no parse errors)

These facts describe the measurement environment. They are **not** a root-cause analysis. Do not mix Chain A and Chain B. This does not prove a Feishu / real-robot / cross-host root cause.

这些环境记录 **不是** 飞书现场、实机、或跨机根因证明。
