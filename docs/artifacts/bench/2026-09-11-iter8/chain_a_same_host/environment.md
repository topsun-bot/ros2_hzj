# Environment — A / `same-host`

- **STATUS:** `ok`
- **UTC:** `2026-09-11T08:41:09Z`
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
- **git SHA ros2_hzj:** `be6016bc049aebc191784c1c0e376f2c19c8a361`
- **DimOS deps source:** `not used (large-packet ping-pong / pytest skipped or ROS-only)`
- **DimOS tree:** `(none)`
- **DimOS git SHA:** `(n/a)`
- **which docker:** `(not on PATH)`
- **which ros2:** `/opt/ros/humble/bin/ros2`

## Notes

Sourced chain_a.sh (RMW=rmw_fastrtps_cpp, ROS_DOMAIN_ID=42). ROS setup=/opt/ros/humble/setup.bash. pytest exit=0. pingpong exit=0. Topology=same-host. BENCH_SIZES=64. BENCH_INTERVAL_MS=5. BENCH_ROS_MSG=uint8_multiarray. Fast-DDS transports are whatever the Humble rmw_fastrtps_cpp default plus config/fastdds.xml use — fastdds.xml does not force UDP-only or SHM-only; do not invent SHM. Do not compare with Chain B. Not real-robot / Feishu-field / cross-host proof.

These facts describe the measurement environment. They are **not** a
root-cause analysis. Do not mix Chain A and Chain B in one table.
