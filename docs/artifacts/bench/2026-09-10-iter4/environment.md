# Environment — iter4 remasure (Chain A)

Shared facts. Per-topology files land after remasure.

- **UTC date dir:** `2026-09-10-iter4`
- **hostname class:** `cursor-cloud-vm`
- **Chain:** A only (`rmw_fastrtps_cpp`, `ROS_DOMAIN_ID=42`)
- **Command:** `BENCH_DATE=2026-09-10-iter4 CHAIN_A_IMAGE=osrf/ros:humble-desktop LARGE_PACKET_CHAINS=A ./scripts/bench/run_large_packet.sh`
- **Knob:** `<preallocated_number>0</preallocated_number>` (was 32; default thread-count guess) and `<dynamic>true</dynamic>` under default-participant `<allocation><send_buffers>`. A 32→16 probe did not recover same-host mid-size and was not kept.

These facts describe the measurement environment. They are **not** a root-cause analysis. Do not mix Chain A and Chain B. This does not prove a Feishu / real-robot / cross-host root cause.

这些环境记录 **不是** 飞书现场、实机、或跨机根因证明。
