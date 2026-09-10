# Environment — iter3 remasure (Chain A)

Shared facts. Per-topology files: [`chain_a_same_process/environment.md`](chain_a_same_process/environment.md), [`chain_a_same_host/environment.md`](chain_a_same_host/environment.md).

- **UTC date dir:** `2026-09-10-iter3`
- **hostname class:** `cursor-cloud-vm` (`hostname=cursor`)
- **Host OS:** Ubuntu 24.04.4 LTS
- **Bench OS (container):** Ubuntu 22.04.5 LTS / Humble
- **CPU:** Intel Xeon × 4 logical (same class as iter2-after)
- **Chain:** A only (`rmw_fastrtps_cpp`, `ROS_DOMAIN_ID=42`)
- **image:** `osrf/ros:humble-desktop` digest `sha256:fb07245b32187d74350be25323d8ad2f8ca5c25c325759911a1eff2267a49c1e` (same as iter2-after)
- **Command:** `BENCH_DATE=2026-09-10-iter3 CHAIN_A_IMAGE=osrf/ros:humble-desktop LARGE_PACKET_CHAINS=A ./scripts/bench/run_large_packet.sh`
- **Sizes / gap / samples:** 102400 / 262144 / 1048576 B; 100 ms; 80 samples (same as iter2)
- **git SHA ros2_hzj (at remasure):** parent `3544eda86c63a2c4636c632c52ef67e859b3b915` plus the send-buffer XML in this directory's `change.md` (not the reverted SHM probe)
- **Knob:** `<preallocated_number>32</preallocated_number>` and `<dynamic>true</dynamic>` under default-participant `<allocation><send_buffers>`. XMLPARSER did not reject these elements (empty pingpong stderr).

These facts describe the measurement environment. They are **not** a root-cause analysis. Do not mix Chain A and Chain B. This does not prove a Feishu / real-robot / cross-host root cause.
