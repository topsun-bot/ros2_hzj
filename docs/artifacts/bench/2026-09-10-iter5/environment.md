# Environment — iter5 remasure (Chain A)

Shared facts. Per-topology files: [`chain_a_same_process/environment.md`](chain_a_same_process/environment.md), [`chain_a_same_host/environment.md`](chain_a_same_host/environment.md).

- **UTC date dir:** `2026-09-10-iter5`
- **hostname class:** `cursor-cloud-vm` (`hostname=cursor`)
- **Host OS:** Ubuntu 24.04.4 LTS
- **Bench OS (container):** Ubuntu 22.04.5 LTS / Humble
- **CPU:** Intel Xeon × 4 logical (same class as iter4)
- **Chain:** A only (`rmw_fastrtps_cpp`, `ROS_DOMAIN_ID=42`)
- **image:** `osrf/ros:humble-desktop` digest `sha256:fb07245b32187d74350be25323d8ad2f8ca5c25c325759911a1eff2267a49c1e` (same as iter4 / iter3 / iter2-after)
- **Command:** `BENCH_DATE=2026-09-10-iter5 CHAIN_A_IMAGE=osrf/ros:humble-desktop LARGE_PACKET_CHAINS=A ./scripts/bench/run_large_packet.sh`
- **Sizes / gap / samples:** 102400 / 262144 / 1048576 B; 100 ms; 80 samples (same as iter4)
- **git SHA ros2_hzj (at remasure):** `364f7ccda1e4a09b7d0e4b1abff1fffb51c8b037` (additive `shm_midsize` on top of iter4 `preallocated_number=32` / `dynamic=false`)
- **Knob:** additive user SHM `<maxMessageSize>280000</maxMessageSize>` `<segment_size>2097152</segment_size>`; `useBuiltinTransports` true. XMLPARSER did not reject these elements (empty pingpong stderr).
- **Discarded probes (not in the landed XML):** exclusive UDP+SHM `segment_size=768 KiB` (BestEffort 1 MiB 80/80 → 1/80); UDP-only / no SHM (BestEffort 1 MiB 0/90). iter3 unfragmented SHM (`maxMessageSize` 2 MiB / `segment_size` 4 MiB) stays discarded.

These facts describe the measurement environment. They are **not** a root-cause analysis. Do not mix Chain A and Chain B. This does not prove a Feishu / real-robot / cross-host root cause.

这些环境记录 **不是** 飞书现场、实机、或跨机根因证明。
