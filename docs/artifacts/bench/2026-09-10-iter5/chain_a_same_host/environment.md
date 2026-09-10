# Environment — A / `same-host`

- **STATUS:** `ok`
- **UTC:** `2026-09-10T21:39:22Z`
- **Topology (required label):** `same-host`
- **Chain:** `A`
- **hostname:** `cursor`
- **hostname class:** `cursor-cloud-vm`
- **OS:** `Linux-6.12.94+-x86_64-with-glibc2.35` / `Ubuntu 22.04.5 LTS`
- **CPU:** `Intel(R) Xeon(R) Processor` × 4 logical
- **Python:** `3.10.12` (`/usr/bin/python3`)
- **ROS_DISTRO:** `humble`
- **RMW_IMPLEMENTATION:** `rmw_fastrtps_cpp`
- **ROS_DOMAIN_ID:** `42`
- **FASTRTPS_DEFAULT_PROFILES_FILE:** `/work/config/fastdds.xml`
- **CYCLONEDDS_HOME:** `(unset)`
- **CYCLONEDDS_URI:** `(unset)`
- **cyclonedds C:** `unknown`
- **cyclonedds Python:** `not-installed`
- **pytest:** `6.2.5`
- **numpy:** `1.21.5`
- **pydantic:** `not-installed`
- **rclpy:** `3.3.21`
- **git SHA ros2_hzj:** `364f7ccda1e4a09b7d0e4b1abff1fffb51c8b037`
- **DimOS deps source:** `not used (large-packet ping-pong / pytest skipped or ROS-only)`
- **DimOS tree:** `(none)`
- **DimOS git SHA:** `(n/a)`
- **which docker:** `(not on PATH)`
- **which ros2:** `/opt/ros/humble/bin/ros2`

## Notes

Sourced chain_a.sh (RMW=rmw_fastrtps_cpp, ROS_DOMAIN_ID=42). ROS setup=/opt/ros/humble/setup.bash. pytest exit=0. pingpong exit=0. Topology=same-host. BENCH_SIZES=102400,262144,1048576. BENCH_INTERVAL_MS=100. BENCH_ROS_MSG=uint8_multiarray. Knob: additive user SHM shm_midsize maxMessageSize=280000 segment_size=2097152; useBuiltinTransports remains true (iter2 UDP sockets still apply). Not exclusive SHM, not UDP-only. Do not compare with Chain B. Not real-robot / Feishu-field / cross-host proof.

These facts describe the measurement environment. They are **not** a
root-cause analysis. Do not mix Chain A and Chain B in one table.
