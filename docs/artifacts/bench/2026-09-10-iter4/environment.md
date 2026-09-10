# Environment — iter4 remasure (Chain A)

Shared facts. Per-topology files: [`chain_a_same_process/environment.md`](chain_a_same_process/environment.md), [`chain_a_same_host/environment.md`](chain_a_same_host/environment.md).

- **UTC date dir:** `2026-09-10-iter4`
- **hostname class:** `cursor-cloud-vm` (`hostname=cursor`)
- **Host OS:** Ubuntu 24.04.4 LTS
- **Bench OS (container):** Ubuntu 22.04.5 LTS / Humble
- **CPU:** Intel Xeon × 4 logical (same class as iter3)
- **Chain:** A only (`rmw_fastrtps_cpp`, `ROS_DOMAIN_ID=42`)
- **image:** `osrf/ros:humble-desktop` digest `sha256:fb07245b32187d74350be25323d8ad2f8ca5c25c325759911a1eff2267a49c1e` (same as iter3 / iter2-after)
- **Command:** `BENCH_DATE=2026-09-10-iter4 CHAIN_A_IMAGE=osrf/ros:humble-desktop LARGE_PACKET_CHAINS=A ./scripts/bench/run_large_packet.sh`
- **Sizes / gap / samples:** 102400 / 262144 / 1048576 B; 100 ms; 80 samples (same as iter3)
- **git SHA ros2_hzj (at remasure):** working tree `preallocated_number=32` / `dynamic=false` on top of `c1b4ae650b2ba816541ad2b924ef1031b043ddb3` (that commit was a discarded 0-prealloc probe, not the measured XML)
- **Knob:** `<preallocated_number>32</preallocated_number>` kept and `<dynamic>false</dynamic>` under default-participant `<allocation><send_buffers>`. XMLPARSER did not reject these elements (empty pingpong stderr).
- **Discarded probes (not in the landed XML):** `preallocated_number` 16 and 0 with `dynamic` still true. 16 did not recover same-host mid-size. 0 erased same-host 1 MiB (BestEffort p50 2935 → 5075 µs).

These facts describe the measurement environment. They are **not** a root-cause analysis. Do not mix Chain A and Chain B. This does not prove a Feishu / real-robot / cross-host root cause.

这些环境记录 **不是** 飞书现场、实机、或跨机根因证明。
