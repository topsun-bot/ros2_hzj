# Environment — iter2 large-packet baseline (Step A, no knob)

Shared facts. Per-topology files live under each `chain_*` directory.

- **UTC date dir:** `2026-09-10-iter2-large-baseline`
- **hostname class:** `cursor-cloud-vm` (`hostname=cursor`)
- **Host OS:** Ubuntu 24.04.4 LTS
- **CPU:** Intel Xeon × 4 logical
- **RAM:** 15 GiB (1 MiB payloads did not OOM)
- **Payload lengths:** 102400 / 262144 / 1048576 bytes
- **Inter-message gap:** 100 ms (target 10 Hz)
- **Samples:** 80 recorded + 10 warmup; timeout 8 s
- **Chain A image:** `osrf/ros:humble-desktop` digest `sha256:fb07245b32187d74350be25323d8ad2f8ca5c25c325759911a1eff2267a49c1e`
- **Chain A:** `rmw_fastrtps_cpp`, `ROS_DOMAIN_ID=42`, `FASTRTPS_DEFAULT_PROFILES_FILE=config/fastdds.xml` (iter1 Humble-valid historyQos; **no** socket-buffer knob yet)
- **Chain B:** Cyclone domain 0; `CYCLONEDDS_HOME=/opt/cyclonedds`; no RouDi
- **git SHA ros2_hzj (at baseline):** `280c98d08948e5d519aa42d945e16b80172da620`
- **Command:** `BENCH_DATE=2026-09-10-iter2-large-baseline CHAIN_A_IMAGE=osrf/ros:humble-desktop ./scripts/bench/run_large_packet.sh`

These facts describe the measurement environment. They are **not** a root-cause analysis. Do not mix Chain A and Chain B. This does not prove a Feishu / real-robot / cross-host root cause.
